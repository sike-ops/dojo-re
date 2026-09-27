# dojo-re

AI-generated reverse-engineering practice app. DeepSeek creates small single-file
programs, the backend compiles and disassembles them in Docker, and the web UI
lets you reconstruct the program from assembly and check output equivalence.

## Requirements

- `uv`
- Docker
- Node.js/npm for frontend development
- `DEEPSEEK_API_KEY` in your shell

Do not put API keys in repo files. The key is read only by the Python backend.
By default the app uses DeepSeek V4.1 Flash via API model id `deepseek-flash`.
`DEEPSEEK_MODEL=DeepSeek-V4.1-Flash` is accepted as an alias and normalized to
the API id.

## Setup

```bash
uv sync --dev
export DEEPSEEK_API_KEY="..."
uv run dojo-re build-runner
```

For frontend dependencies:

```bash
npm install
```

## Development

Run the backend:

```bash
uv run dojo-re serve --reload
```

Run the React frontend in another terminal:

```bash
npm run dev
```

Open `http://127.0.0.1:5173`.

## Production-style local run

```bash
npm run build
uv run dojo-re serve
```

Open `http://127.0.0.1:8000`.

## Tests

```bash
uv run pytest
```
