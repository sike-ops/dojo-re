from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="dojo-re")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="run the FastAPI web app")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")

    subparsers.add_parser("build-runner", help="build the Docker runner image")

    args = parser.parse_args()
    if args.command == "build-runner":
        root = Path(__file__).resolve().parents[2]
        subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "dojo-re-runner:latest",
                "-f",
                str(root / "docker" / "runner.Dockerfile"),
                str(root),
            ],
            check=True,
        )
        return

    if args.command in {None, "serve"}:
        import uvicorn

        uvicorn.run(
            "dojo_re.app:app",
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 8000),
            reload=getattr(args, "reload", False),
        )
