from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dojo_re.deepseek import DeepSeekChallengeGenerator, GenerationError
from dojo_re.models import (
    ChallengeSummary,
    ChallengeTest,
    GenerateChallengeRequest,
    SubmissionResult,
    SubmitRequest,
)
from dojo_re.runner import DockerRunner, RunnerError
from dojo_re.store import ChallengeStore


store = ChallengeStore()
runner = DockerRunner()


def create_app() -> FastAPI:
    app = FastAPI(title="dojo-re", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/challenges", response_model=ChallengeSummary)
    def generate_challenge(request: GenerateChallengeRequest) -> ChallengeSummary:
        try:
            generated = DeepSeekChallengeGenerator().generate(request)
            tests = [*generated.public_tests, *generated.hidden_tests]
            compile_result, run_results = runner.compile_and_run_tests(
                generated.language,
                generated.source,
                tests,
            )
            if not compile_result.ok:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "Generated source did not compile.",
                        "stdout": compile_result.stdout,
                        "stderr": compile_result.stderr,
                    },
                )
            if len(run_results) != len(tests) or any(result.exit_code != 0 for result in run_results):
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "Generated source failed its harness tests.",
                        "tests": [result.model_dump() for result in run_results],
                    },
                )

            public_count = len(generated.public_tests)
            public_tests = [
                ChallengeTest(
                    name=result.name,
                    stdin=result.stdin,
                    stdout=result.actual_stdout,
                    public=True,
                )
                for result in run_results[:public_count]
            ]
            hidden_tests = [
                ChallengeTest(
                    name=result.name,
                    stdin=result.stdin,
                    stdout=result.actual_stdout,
                    public=False,
                )
                for result in run_results[public_count:]
            ]
            generated = generated.model_copy(
                update={"public_tests": public_tests, "hidden_tests": hidden_tests},
            )

            disassembly = runner.compile(generated.language, generated.source)
            if not disassembly.ok:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "Generated binary could not be disassembled.",
                        "stdout": disassembly.stdout,
                        "stderr": disassembly.stderr,
                    },
                )
            return store.add(generated, disassembly.assembly).summary()
        except GenerationError as exc:
            status_code = 400 if str(exc).startswith("Set DEEPSEEK_API_KEY") else 502
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc
        except RunnerError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/challenges/{challenge_id}", response_model=ChallengeSummary)
    def get_challenge(challenge_id: str) -> ChallengeSummary:
        challenge = store.get(challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        return challenge.summary()

    @app.post("/api/challenges/{challenge_id}/submit", response_model=SubmissionResult)
    def submit(challenge_id: str, request: SubmitRequest) -> SubmissionResult:
        challenge = store.get(challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")

        try:
            compile_result, test_results = runner.compile_and_run_tests(
                challenge.generated.language,
                request.source,
                challenge.all_tests,
            )
        except RunnerError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        passed = compile_result.ok and bool(test_results) and all(result.passed for result in test_results)
        return SubmissionResult(
            challenge_id=challenge_id,
            passed=passed,
            compile_stdout=compile_result.stdout,
            compile_stderr=compile_result.stderr,
            tests=test_results,
        )

    dist_dir = Path(__file__).resolve().parent / "frontend_dist"
    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str = "") -> FileResponse:
            requested = dist_dir / path
            if path and requested.is_file():
                return FileResponse(requested)
            return FileResponse(dist_dir / "index.html")

    return app


app = create_app()
