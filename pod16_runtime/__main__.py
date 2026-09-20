from __future__ import annotations

import argparse
import json

from pod16_runtime.runtime import (
    POD16Runtime,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "On-demand lifecycle manager "
            "for the local POD-16 stack."
        )
    )
    parser.add_argument(
        "command",
        choices={
            "start",
            "stop",
            "status",
        },
    )
    args = parser.parse_args()

    runtime = POD16Runtime()

    if args.command == "start":
        runtime.ensure_running()
        print("POD-16 is ready.")
        return 0

    if args.command == "stop":
        runtime.shutdown(force=True)
        print("POD-16 is stopped.")
        return 0

    status = runtime.status()
    print(
        json.dumps(
            {
                "api_healthy": (
                    status.api_healthy
                ),
                "docker_running": (
                    status.docker_running
                ),
                "pod16_containers_running": (
                    status.pod16_containers_running
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
