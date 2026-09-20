from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


class Pod16RuntimeError(Exception):
    """Raised when the local POD-16 runtime cannot be started or stopped."""


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    api_healthy: bool
    docker_running: bool
    pod16_containers_running: bool


class POD16Runtime:
    """Start POD-16 only when a client actually needs it.

    This object is intentionally not a daemon. It performs short startup checks,
    starts Docker Desktop only when required, starts the POD-16 Compose stack,
    and then becomes idle. There is no background polling thread.

    If this instance started the stack, shutdown() stops it again. Docker
    Desktop is also stopped when this runtime started it and no unrelated
    containers are still running.
    """

    def __init__(
        self,
        *,
        project_dir: str | Path | None = None,
        base_url: str = "http://127.0.0.1:8000",
        health_timeout: float = 0.75,
        startup_timeout: float = 120.0,
        state_file: str | Path | None = None,
    ) -> None:
        self.project_dir = self._resolve_project_dir(
            project_dir
        )
        self.base_url = base_url.rstrip("/")
        self.health_url = f"{self.base_url}/health"
        self.health_timeout = health_timeout
        self.startup_timeout = startup_timeout
        self.state_file = (
            Path(state_file)
            if state_file is not None
            else self._default_state_file()
        )

        self._owns_stack = False
        self._started_docker = False

    @staticmethod
    def _resolve_project_dir(
        project_dir: str | Path | None,
    ) -> Path:
        candidates: list[Path] = []

        if project_dir is not None:
            candidates.append(Path(project_dir))

        env_home = os.environ.get("POD16_HOME")
        if env_home:
            candidates.append(Path(env_home))

        candidates.extend(
            [
                Path.cwd(),
                Path(__file__).resolve().parents[1],
            ]
        )

        for candidate in candidates:
            resolved = candidate.expanduser().resolve()
            if (
                resolved / "docker-compose.yml"
            ).is_file():
                return resolved

        raise Pod16RuntimeError(
            "Could not locate the POD-16 project directory. "
            "Pass project_dir=... or set POD16_HOME."
        )

    @staticmethod
    def _default_state_file() -> Path:
        local_appdata = os.environ.get(
            "LOCALAPPDATA"
        )

        if local_appdata:
            root = Path(local_appdata) / "POD16"
        else:
            root = Path.home() / ".pod16"

        return root / "runtime.json"

    @staticmethod
    def _creation_flags() -> int:
        if os.name != "nt":
            return 0

        return getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

    def _run(
        self,
        *args: str,
        timeout: float = 30.0,
    ) -> subprocess.CompletedProcess[str]:
        kwargs: dict[str, Any] = {
            "cwd": self.project_dir,
            "capture_output": True,
            "text": True,
            "timeout": timeout,
            "check": False,
        }

        flags = self._creation_flags()
        if flags:
            kwargs["creationflags"] = flags

        try:
            return subprocess.run(
                list(args),
                **kwargs,
            )
        except FileNotFoundError as exc:
            raise Pod16RuntimeError(
                f"Required command was not found: {args[0]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise Pod16RuntimeError(
                "Command timed out: "
                + " ".join(args)
            ) from exc

    @staticmethod
    def _failure_message(
        result: subprocess.CompletedProcess[str],
    ) -> str:
        output = (
            result.stderr.strip()
            or result.stdout.strip()
            or "unknown error"
        )
        return output

    def is_healthy(self) -> bool:
        try:
            with urlopen(
                self.health_url,
                timeout=self.health_timeout,
            ) as response:
                return response.status == 200
        except (OSError, URLError):
            return False

    def _docker_running(self) -> bool:
        result = self._run(
            "docker",
            "info",
            "--format",
            "{{.ServerVersion}}",
            timeout=5.0,
        )
        return result.returncode == 0

    def _wait_for_docker(self) -> None:
        deadline = (
            time.monotonic()
            + self.startup_timeout
        )

        while time.monotonic() < deadline:
            if self._docker_running():
                return
            time.sleep(1.0)

        raise Pod16RuntimeError(
            "Docker Desktop did not become ready "
            f"within {self.startup_timeout:.0f} seconds."
        )

    def _start_docker_desktop(self) -> None:
        result = self._run(
            "docker",
            "desktop",
            "start",
            "--timeout",
            str(int(self.startup_timeout)),
            timeout=self.startup_timeout + 10,
        )

        if result.returncode != 0:
            raise Pod16RuntimeError(
                "Could not start Docker Desktop: "
                + self._failure_message(result)
            )

        self._wait_for_docker()

    def _stop_docker_desktop(self) -> None:
        result = self._run(
            "docker",
            "desktop",
            "stop",
            "--timeout",
            "30",
            timeout=40.0,
        )

        if result.returncode != 0:
            raise Pod16RuntimeError(
                "Could not stop Docker Desktop: "
                + self._failure_message(result)
            )

    def _compose(
        self,
        *args: str,
        timeout: float = 120.0,
    ) -> subprocess.CompletedProcess[str]:
        return self._run(
            "docker",
            "compose",
            "-p",
            "pod16",
            "-f",
            str(
                self.project_dir
                / "docker-compose.yml"
            ),
            *args,
            timeout=timeout,
        )

    def _pod16_containers_running(self) -> bool:
        if not self._docker_running():
            return False

        result = self._run(
            "docker",
            "ps",
            "-q",
            "--filter",
            "label=com.docker.compose.project=pod16",
            timeout=5.0,
        )

        return (
            result.returncode == 0
            and bool(result.stdout.strip())
        )

    def _other_containers_running(self) -> bool:
        if not self._docker_running():
            return False

        all_result = self._run(
            "docker",
            "ps",
            "-q",
            timeout=5.0,
        )
        pod16_result = self._run(
            "docker",
            "ps",
            "-q",
            "--filter",
            "label=com.docker.compose.project=pod16",
            timeout=5.0,
        )

        if (
            all_result.returncode != 0
            or pod16_result.returncode != 0
        ):
            return True

        all_ids = set(
            all_result.stdout.split()
        )
        pod16_ids = set(
            pod16_result.stdout.split()
        )

        return bool(all_ids - pod16_ids)

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {}

        try:
            return json.loads(
                self.state_file.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

    def _write_state(self) -> None:
        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.state_file.write_text(
            json.dumps(
                {
                    "started_docker": (
                        self._started_docker
                    ),
                    "project_dir": str(
                        self.project_dir
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _clear_state(self) -> None:
        try:
            self.state_file.unlink(
                missing_ok=True
            )
        except OSError:
            pass

    def _wait_for_health(self) -> None:
        deadline = (
            time.monotonic()
            + self.startup_timeout
        )

        while time.monotonic() < deadline:
            if self.is_healthy():
                return
            time.sleep(0.5)

        logs = self._compose(
            "logs",
            "--tail",
            "80",
            "api",
            timeout=10.0,
        )

        details = self._failure_message(logs)

        raise Pod16RuntimeError(
            "POD-16 did not become healthy "
            f"within {self.startup_timeout:.0f} seconds. "
            f"Recent API logs: {details}"
        )

    def ensure_running(self) -> None:
        """Make POD-16 available, doing no work if it is already healthy."""
        if self.is_healthy():
            return

        previous_state = self._load_state()
        docker_was_running = (
            self._docker_running()
        )

        if docker_was_running:
            self._started_docker = bool(
                previous_state.get(
                    "started_docker",
                    False,
                )
            )
        else:
            self._start_docker_desktop()
            self._started_docker = True

        try:
            result = self._compose(
                "up",
                "-d",
                "db",
                "api",
                timeout=self.startup_timeout,
            )

            if result.returncode != 0:
                raise Pod16RuntimeError(
                    "Could not start the POD-16 "
                    "Compose stack: "
                    + self._failure_message(result)
                )

            self._owns_stack = True
            self._write_state()
            self._wait_for_health()

        except Exception:
            self._best_effort_cleanup()
            raise

    def _best_effort_cleanup(self) -> None:
        if self._docker_running():
            self._compose(
                "stop",
                "-t",
                "5",
                "api",
                "db",
                timeout=20.0,
            )

            if (
                self._started_docker
                and not self._other_containers_running()
            ):
                try:
                    self._stop_docker_desktop()
                except Pod16RuntimeError:
                    pass

        self._owns_stack = False
        self._clear_state()

    def shutdown(
        self,
        *,
        force: bool = False,
    ) -> None:
        """Stop resources owned by this runtime.

        force=True is intended for the CLI stop command. It stops the POD-16
        stack even when it was started by an earlier process.
        """
        if (
            not force
            and not self._owns_stack
        ):
            return

        state = self._load_state()
        started_docker = (
            self._started_docker
            or bool(
                state.get(
                    "started_docker",
                    False,
                )
            )
        )

        if not self._docker_running():
            self._owns_stack = False
            self._clear_state()
            return

        result = self._compose(
            "stop",
            "-t",
            "10",
            "api",
            "db",
            timeout=30.0,
        )

        if result.returncode != 0:
            raise Pod16RuntimeError(
                "Could not stop POD-16 containers: "
                + self._failure_message(result)
            )

        self._owns_stack = False

        if (
            started_docker
            and not self._other_containers_running()
        ):
            self._stop_docker_desktop()
            self._clear_state()
            return

        if started_docker:
            self._write_state()
        else:
            self._clear_state()

    def status(self) -> RuntimeStatus:
        docker_running = (
            self._docker_running()
        )

        return RuntimeStatus(
            api_healthy=self.is_healthy(),
            docker_running=docker_running,
            pod16_containers_running=(
                self._pod16_containers_running()
                if docker_running
                else False
            ),
        )

    def __enter__(self) -> "POD16Runtime":
        self.ensure_running()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.shutdown()
