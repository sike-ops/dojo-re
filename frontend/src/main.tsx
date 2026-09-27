import React, {useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import Editor from '@monaco-editor/react';
import {BadgeCheck, CircleAlert, Loader2, Play, RotateCcw} from 'lucide-react';
import './styles.css';

type Language = 'c' | 'cpp' | 'rust' | 'zig' | 'go';
type Difficulty = 'easy' | 'medium' | 'hard';

type ChallengeTest = {
  name: string;
  stdin: string;
  stdout: string;
  public: boolean;
};

type Challenge = {
  id: string;
  language: Language;
  title: string;
  description: string;
  assembly: string;
  public_tests: ChallengeTest[];
  created_at: number;
};

type TestResult = {
  name: string;
  stdin: string;
  expected_stdout: string;
  actual_stdout: string;
  passed: boolean;
  stderr: string;
  exit_code: number | null;
  timed_out: boolean;
};

type SubmissionResult = {
  challenge_id: string;
  passed: boolean;
  compile_stdout: string;
  compile_stderr: string;
  tests: TestResult[];
};

const starterSource: Record<Language, string> = {
  c: '#include <stdio.h>\n\nint main(void) {\n    return 0;\n}\n',
  cpp: '#include <iostream>\n\nint main() {\n    return 0;\n}\n',
  rust: 'fn main() {\n}\n',
  zig: 'const std = @import("std");\n\npub fn main() !void {\n}\n',
  go: 'package main\n\nfunc main() {\n}\n',
};

const monacoLanguage: Record<Language, string> = {
  c: 'c',
  cpp: 'cpp',
  rust: 'rust',
  zig: 'zig',
  go: 'go',
};

function App() {
  const [language, setLanguage] = useState<Language | 'any'>('any');
  const [difficulty, setDifficulty] = useState<Difficulty>('medium');
  const [theme, setTheme] = useState('');
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [source, setSource] = useState(starterSource.c);
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  const selectedEditorLanguage = useMemo(() => {
    return challenge ? monacoLanguage[challenge.language] : 'c';
  }, [challenge]);

  async function generateChallenge() {
    setBusy(true);
    setResult(null);
    setStatus('Generating challenge with DeepSeek...');
    try {
      const response = await fetch('/api/challenges', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({language, difficulty, theme: theme || null}),
      });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(formatError(payload));
      setChallenge(payload as Challenge);
      setSource(starterSource[(payload as Challenge).language]);
      setStatus('Challenge ready.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  async function submitSource() {
    if (!challenge) return;
    setBusy(true);
    setStatus('Compiling and checking reconstruction...');
    try {
      const response = await fetch(`/api/challenges/${challenge.id}/submit`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({source}),
      });
      const payload = await readJson(response);
      if (!response.ok) throw new Error(formatError(payload));
      setResult(payload as SubmissionResult);
      setStatus((payload as SubmissionResult).passed ? 'All tests passed.' : 'Output mismatch.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <div className="brand">
          <span className="mark">RE</span>
          <span>dojo-re</span>
        </div>
        <div className="controls">
          <select value={language} onChange={event => setLanguage(event.target.value as Language | 'any')}>
            <option value="any">Any language</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
            <option value="rust">Rust</option>
            <option value="zig">Zig</option>
            <option value="go">Go</option>
          </select>
          <select value={difficulty} onChange={event => setDifficulty(event.target.value as Difficulty)}>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <input
            value={theme}
            onChange={event => setTheme(event.target.value)}
            placeholder="theme"
            aria-label="theme"
          />
          <button onClick={generateChallenge} disabled={busy}>
            {busy ? <Loader2 className="spin" size={16} /> : <RotateCcw size={16} />}
            Generate
          </button>
          <button className="primary" onClick={submitSource} disabled={busy || !challenge}>
            <Play size={16} />
            Check
          </button>
        </div>
      </header>

      <section className="workspace">
        <section className="pane challenge-pane">
          <div className="pane-head">
            <div>
              <h1>{challenge?.title ?? 'Generate a challenge'}</h1>
              <p>{challenge?.description ?? 'Assembly will appear here once DeepSeek creates a program.'}</p>
            </div>
            {challenge && <span className="tag">{challenge.language}</span>}
          </div>
          <div className="editor-shell">
            <Editor
              height="100%"
              language="asm"
              theme="vs-dark"
              value={challenge?.assembly ?? ''}
              options={{readOnly: true, minimap: {enabled: false}, fontSize: 13, wordWrap: 'off'}}
            />
          </div>
        </section>

        <aside className="side">
          <section className="pane tests-pane">
            <div className="pane-title">Public Tests</div>
            <div className="test-list">
              {challenge?.public_tests.map(test => (
                <div className="test-row" key={test.name}>
                  <strong>{test.name}</strong>
                  <label>stdin</label>
                  <pre>{test.stdin || '<empty>'}</pre>
                  <label>stdout</label>
                  <pre>{test.stdout || '<empty>'}</pre>
                </div>
              )) ?? <span className="muted">No challenge loaded.</span>}
            </div>
          </section>

          <section className="pane status-pane">
            <div className="pane-title">Status</div>
            <div className="status-line">{status || 'Ready.'}</div>
            {result && (
              <div className={result.passed ? 'verdict pass' : 'verdict fail'}>
                {result.passed ? <BadgeCheck size={18} /> : <CircleAlert size={18} />}
                {result.passed ? 'passed' : 'failed'}
              </div>
            )}
          </section>
        </aside>

        <section className="pane source-pane">
          <div className="pane-head compact">
            <div>
              <h2>Reconstruction</h2>
              <p>Write a source-level clone that matches the binary output.</p>
            </div>
          </div>
          <div className="editor-shell">
            <Editor
              height="100%"
              language={selectedEditorLanguage}
              theme="vs-dark"
              value={source}
              onChange={value => setSource(value ?? '')}
              options={{minimap: {enabled: false}, fontSize: 13, wordWrap: 'on'}}
            />
          </div>
        </section>

        <section className="pane results-pane">
          <div className="pane-title">Check Results</div>
          <div className="result-list">
            {result?.compile_stderr && <pre className="compile-output">{result.compile_stderr}</pre>}
            {result?.tests.map(test => (
              <div className={test.passed ? 'result-row ok' : 'result-row bad'} key={test.name}>
                <div>
                  <strong>{test.name}</strong>
                  <span>{test.passed ? 'match' : 'mismatch'}</span>
                </div>
                {!test.passed && (
                  <div className="diff-grid">
                    <pre>{test.expected_stdout || '<empty>'}</pre>
                    <pre>{test.actual_stdout || '<empty>'}</pre>
                  </div>
                )}
              </div>
            )) ?? <span className="muted">Submit a reconstruction to compare outputs.</span>}
          </div>
        </section>
      </section>
    </main>
  );
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  return JSON.parse(text);
}

function formatError(payload: unknown): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as {detail: unknown}).detail;
    return typeof detail === 'string' ? detail : JSON.stringify(detail, null, 2);
  }
  return 'Request failed.';
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
