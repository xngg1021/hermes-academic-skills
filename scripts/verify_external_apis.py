"""Manual/pre-release network checks: 0 pass, 1 repository/schema bug, 2 external unavailability."""
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from qa import ROOT, fences, run_fence


def main():
    results = []
    for path in sorted((ROOT / 'skills').glob('*/SKILL.md')):
        for i, kind, code in fences(path):
            if kind != 'external-test: true':
                continue
            try:
                p = run_fence(path, i, code, timeout=180)
            except subprocess.TimeoutExpired:
                results.append({'skill': path.parent.name, 'status': 'EXTERNAL_UNAVAILABLE', 'reason': 'timeout'})
                continue
            status = 'PASS'
            reason = ''
            if p.returncode:
                # Do not dump tracebacks containing query emails or credentials.
                if any(t in p.stderr for t in ('HTTP Error 401', 'HTTP Error 403', 'HTTP Error 429', 'HTTP Error 500',
                                              'HTTP Error 502', 'HTTP Error 503', 'HTTP Error 504',
                                              'URLError', 'TimeoutError', 'RemoteDisconnected')):
                    status, reason = 'EXTERNAL_UNAVAILABLE', 'authentication, quota, service or transport failure'
                else:
                    status, reason = 'FAIL', 'schema, identity or code assertion failed; inspect locally with credentials redacted'
            results.append({'skill': path.parent.name, 'status': status, 'reason': reason,
                            'details': p.stdout.strip() if not p.returncode else ''})
    print(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'results': results}, indent=2))
    if not results or any(r['status'] == 'FAIL' for r in results):
        return 1
    return 2 if any(r['status'] == 'EXTERNAL_UNAVAILABLE' for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
