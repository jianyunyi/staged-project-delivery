#!/usr/bin/env python3
"""Reject stale, missing, or failing evaluation evidence; not an LLM grader."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
selection=json.loads((root/'evals/current.json').read_text())
candidate=root/'evals/runs'/selection['candidate']
meta=json.loads((candidate/'metadata.json').read_text())
current=hashlib.sha256((root/'skills/staged-project-delivery/SKILL.md').read_bytes()).hexdigest()
source=root/'skills/staged-project-delivery'
hashes={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()}
assert meta['package_hashes']==hashes, 'Skill package changed: rerun all three fresh-agent cases.'
assert meta['skill_sha256']==current, 'SKILL.md changed: rerun all three fresh-agent cases and update evidence.'
assert (candidate/'skill-snapshot.md').read_bytes()==(root/'skills/staged-project-delivery/SKILL.md').read_bytes()
review=json.loads((candidate/'review.json').read_text())
assert review['critical_failures']==[], 'Critical behavior failure.'
assert review['method']=='artifact-and-agent-output-review-by-maintainer-agent'
for case in ('lite','standard','irreversible'):
    assert (candidate/case/'agent-output.md').is_file(), 'Missing raw final agent output.'
    result=review['cases'][case]
    assert result['score']==result['max_score'], 'Unresolved process evaluation deviation.'
    assert result['evidence'], 'Missing rationale.'
    additions=result['v030_rules']
    assert set(additions)=={'reuse','root_and_paths','runnable_checks','simplifications','metrics'}
    assert all(x['pass'] and x['evidence'] for x in additions.values()), 'New rule lacks reviewed evidence.'
pre=json.loads((candidate/'irreversible/pre-authorization-state.json').read_text())
fixture=root/'evals/fixtures/irreversible/archive'
assert pre=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.iterdir()}, 'Files changed before authorization.'
functional=json.loads((candidate/'functional-results.json').read_text())
assert all(x['functional_pass'] for x in functional.values()), 'Functional failure.'

assert len((root/'AGENTS.md').read_text().splitlines())<=30, 'AGENTS.md exceeds 30 lines.'
assert hashlib.sha256((root/'AGENTS.md').read_bytes()).hexdigest()==review['agents_sha256'], 'Fallback rules changed: review coverage again.'

print('Current skill is bound to complete, passing, manually reviewed evaluation evidence.')
