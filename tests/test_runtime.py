from pathlib import Path
from subprocess import CompletedProcess

from pod16_runtime.runtime import (
    POD16Runtime,
)


def _runtime(
    tmp_path: Path,
) -> POD16Runtime:
    project_dir = tmp_path / "pod16"
    project_dir.mkdir()
    (
        project_dir
        / "docker-compose.yml"
    ).write_text(
        "services: {}\n",
        encoding="utf-8",
    )

    return POD16Runtime(
        project_dir=project_dir,
        state_file=tmp_path / "runtime.json",
    )


def test_ensure_running_is_noop_when_healthy(
    tmp_path,
    monkeypatch,
):
    runtime = _runtime(tmp_path)

    monkeypatch.setattr(
        runtime,
        "is_healthy",
        lambda: True,
    )

    called = False

    def fail_if_called():
        nonlocal called
        called = True
        return False

    monkeypatch.setattr(
        runtime,
        "_docker_running",
        fail_if_called,
    )

    runtime.ensure_running()

    assert called is False


def test_ensure_running_starts_only_needed_stack(
    tmp_path,
    monkeypatch,
):
    runtime = _runtime(tmp_path)

    health_checks = iter(
        [False, True]
    )
    monkeypatch.setattr(
        runtime,
        "is_healthy",
        lambda: next(
            health_checks,
            True,
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_docker_running",
        lambda: False,
    )

    docker_started = False
    compose_calls = []

    def start_docker():
        nonlocal docker_started
        docker_started = True

    def compose(*args, **kwargs):
        compose_calls.append(args)
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        runtime,
        "_start_docker_desktop",
        start_docker,
    )
    monkeypatch.setattr(
        runtime,
        "_compose",
        compose,
    )

    runtime.ensure_running()

    assert docker_started is True
    assert (
        "up",
        "-d",
        "db",
        "api",
    ) in compose_calls
    assert runtime._owns_stack is True
    assert runtime.state_file.exists()


def test_shutdown_stops_stack_and_owned_docker(
    tmp_path,
    monkeypatch,
):
    runtime = _runtime(tmp_path)
    runtime._owns_stack = True
    runtime._started_docker = True

    monkeypatch.setattr(
        runtime,
        "_docker_running",
        lambda: True,
    )
    monkeypatch.setattr(
        runtime,
        "_other_containers_running",
        lambda: False,
    )

    compose_calls = []
    docker_stopped = False

    def compose(*args, **kwargs):
        compose_calls.append(args)
        return CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    def stop_docker():
        nonlocal docker_stopped
        docker_stopped = True

    monkeypatch.setattr(
        runtime,
        "_compose",
        compose,
    )
    monkeypatch.setattr(
        runtime,
        "_stop_docker_desktop",
        stop_docker,
    )

    runtime.shutdown()

    assert (
        "stop",
        "-t",
        "10",
        "api",
        "db",
    ) in compose_calls
    assert docker_stopped is True
    assert runtime._owns_stack is False


def test_shutdown_does_not_stop_shared_docker(
    tmp_path,
    monkeypatch,
):
    runtime = _runtime(tmp_path)
    runtime._owns_stack = True
    runtime._started_docker = True

    monkeypatch.setattr(
        runtime,
        "_docker_running",
        lambda: True,
    )
    monkeypatch.setattr(
        runtime,
        "_other_containers_running",
        lambda: True,
    )

    monkeypatch.setattr(
        runtime,
        "_compose",
        lambda *args, **kwargs: (
            CompletedProcess(
                args=args,
                returncode=0,
                stdout="",
                stderr="",
            )
        ),
    )

    docker_stopped = False

    def stop_docker():
        nonlocal docker_stopped
        docker_stopped = True

    monkeypatch.setattr(
        runtime,
        "_stop_docker_desktop",
        stop_docker,
    )

    runtime.shutdown()

    assert docker_stopped is False
    assert runtime.state_file.exists()
