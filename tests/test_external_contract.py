"""No network: test the actual helpers extracted from public external Verification fences."""
import ast
import io
from pathlib import Path
import sys
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from qa import fences


@pytest.fixture(params=['academic-source-verification', 'literature-analysis'])
def helper(request):
    path = ROOT / 'skills' / request.param / 'SKILL.md'
    code = next(code for _, kind, code in fences(path) if kind == 'external-test: true')
    tree = ast.parse(code)
    tree.body = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
                 or isinstance(node, ast.FunctionDef) and node.name == 'get']
    ns = {}
    exec(compile(tree, str(path), 'exec'), ns)
    return ns


def test_key_only_sent_to_openalex(helper, monkeypatch):
    monkeypatch.setenv('OPENALEX_API_KEY', 'example-placeholder')
    seen = []
    def fetch(req, timeout):
        seen.append((req, timeout))
        return io.BytesIO(b'{"ok": true}')
    helper['urlopen'] = fetch
    assert helper['get']('https://api.openalex.org/works/W1')['ok']
    assert seen[-1][0].get_header('Authorization') == 'Bearer example-placeholder'
    helper['get']('https://api.crossref.org/works/10.1234/example')
    assert seen[-1][0].get_header('Authorization') is None
    monkeypatch.delenv('OPENALEX_API_KEY')
    helper['get']('https://api.openalex.org/works/W1')
    assert seen[-1][0].get_header('Authorization') is None
    assert all(timeout == 20 for _, timeout in seen)


@pytest.mark.parametrize('status', [401, 429, 503])
def test_http_failure_never_becomes_empty_success(helper, monkeypatch, status):
    calls = []
    def fail(req, timeout):
        calls.append(req)
        raise HTTPError(req.full_url, status, 'test', {}, None)
    helper['urlopen'] = fail
    monkeypatch.setattr(helper['time'], 'sleep', lambda seconds: None)
    with pytest.raises(HTTPError):
        helper['get']('https://api.openalex.org/works/W1')
    assert len(calls) == (1 if status == 401 else 3)


def test_long_retry_after_does_not_loop(helper, monkeypatch):
    calls = []
    def fail(req, timeout):
        calls.append(req)
        raise HTTPError(req.full_url, 429, 'budget exhausted', {'Retry-After': '86400'}, None)
    helper['urlopen'] = fail
    monkeypatch.setattr(helper['time'], 'sleep', lambda seconds: pytest.fail('must not wait a day'))
    with pytest.raises(HTTPError):
        helper['get']('https://api.openalex.org/works/W1')
    assert len(calls) == 1
