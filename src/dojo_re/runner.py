from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from dojo_re.languages import language_spec
from dojo_re.models import ChallengeTest, CompileResult, Language, RunResult


class RunnerError(RuntimeError):
    pass


class DockerRunner:
    def __init__(self, image: str = "dojo-re-runner:latest") -> None:
        self.image = image

    def compile(self, language: Language, source: str) -> CompileResult:
        spec = language_spec(language)
        with tempfile.TemporaryDirectory(prefix="dojo-re-") as tmp:
            workdir = Path(tmp)
            (workdir / spec.filename).write_text(source, encoding="utf-8")

            compile_result = self._docker_run(
                workdir,
                f"timeout 12s {spec.compile_command}",
                timeout=20,
            )
            if compile_result.returncode != 0:
                return CompileResult(
                    ok=False,
                    stdout=compile_result.stdout[-8000:],
                    stderr=compile_result.stderr[-8000:],
                )

            objdump_result = self._docker_run(
                workdir,
                "objdump -d -Mintel program",
                timeout=10,
            )
            if objdump_result.returncode != 0:
                return CompileResult(
                    ok=False,
                    stdout=compile_result.stdout[-8000:],
                    stderr=(compile_result.stderr + objdump_result.stderr)[-8000:],
                )

            return CompileResult(
                ok=True,
                stdout=compile_result.stdout[-8000:],
                stderr=compile_result.stderr[-8000:],
                assembly=objdump_result.stdout[-200000:],
            )

    def compile_and_run_tests(
        self,
        language: Language,
        source: str,
        tests: list[ChallengeTest],
    ) -> tuple[CompileResult, list[RunResult]]:
        spec = language_spec(language)
        with tempfile.TemporaryDirectory(prefix="dojo-re-") as tmp:
            workdir = Path(tmp)
            (workdir / spec.filename).write_text(source, encoding="utf-8")

            compile_result_raw = self._docker_run(
                workdir,
                f"timeout 12s {spec.compile_command}",
                timeout=20,
            )
            compile_result = CompileResult(
                ok=compile_result_raw.returncode == 0,
                stdout=compile_result_raw.stdout[-8000:],
                stderr=compile_result_raw.stderr[-8000:],
            )
            if not compile_result.ok:
                return compile_result, []

            results: list[RunResult] = []
            for test in tests:
                run = self._docker_run(
                    workdir,
                    "timeout 4s ./program",
                    stdin=test.stdin,
                    timeout=8,
                )
                results.append(
                    RunResult(
                        name=test.name,
                        stdin=test.stdin,
                        expected_stdout=test.stdout,
                        actual_stdout=run.stdout,
                        passed=run.returncode == 0 and run.stdout == test.stdout,
                        stderr=run.stderr[-8000:],
                        exit_code=run.returncode,
                        timed_out=run.returncode == 124,
                    ),
                )
            return compile_result, results

    def _docker_run(
        self,
        workdir: Path,
        command: str,
        stdin: str | None = None,
        timeout: int = 10,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--cpus=1",
            "--memory=512m",
            "--pids-limit=128",
            "--security-opt",
            "no-new-privileges",
            "-v",
            f"{workdir}:/work:rw",
            "-w",
            "/work",
        ]
        if stdin is not None:
            cmd.append("-i")
        cmd.extend(
            [
                self.image,
                "bash",
                "-lc",
                command,
            ],
        )
        try:
            return subprocess.run(
                cmd,
                input=stdin,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RunnerError("Docker is required but was not found on PATH.") from exc
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                cmd,
                124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + "\nProcess timed out.",
            )
