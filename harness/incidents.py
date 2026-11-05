"""Report smoke failures to the demo ClickUp List. Defaults to a read-free dry run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

LIST_ID = '901521438487'
REPO = 'Mohmmed93/harness-engineering-demo'
SITE = 'https://mohmmed93.github.io/harness-engineering-demo/'
TRIAGE = 'HARNESS_INCIDENT_TRIAGE'


def failures(report):
    found = []
    def visit(suites):
        for suite in suites:
            for spec in suite.get('specs', []):
                for test in spec.get('tests', []):
                    # A failure followed by a successful retry is flaky, not a failed smoke run.
                    if test.get('status') != 'unexpected':
                        continue
                    results = test.get('results', [])
                    error = (results[-1].get('error') or {}).get('message', '') if results else ''
                    error = re.sub(r'\x1b\[[0-9;]*m', '', error)
                    found.append({'file': spec.get('file', suite.get('file', 'unknown')),
                                  'title': spec.get('title', 'unknown test'),
                                  'error': error[:1200]})
            visit(suite.get('suites', []))
    visit(report.get('suites', []))
    return sorted(found, key=lambda x: (x['file'], x['title']))


def make_incident(evidence, report):
    if evidence.get('result') == 'success':
        return None
    if evidence.get('result') != 'failure':
        raise ValueError('Only completed smoke failures are reportable')
    sha = evidence.get('sha', '')
    run = str(evidence.get('runId', ''))
    attempt = str(evidence.get('runAttempt', '1'))
    if not re.fullmatch('[a-f0-9]{40}', sha) or not run.isdigit() or not attempt.isdigit():
        raise ValueError('Valid commit, run ID and attempt are required')
    if evidence.get('url', '').rstrip('/') != SITE.rstrip('/'):
        raise ValueError('Only the demo Pages URL is allowed')
    failed = failures(report)
    stable = evidence.get('identityBefore') == evidence.get('identityAfter') == 'success'
    assertion = failed and all('expect(' in f['error'] for f in failed)
    classification = 'application-check' if stable and assertion else 'infrastructure-or-unknown'
    identities = [(f['file'], f['title']) for f in failed] or [('smoke', classification)]
    rehearsal = evidence.get('rehearsal') is True
    digest = hashlib.sha256(json.dumps([SITE, classification, identities, rehearsal],sort_keys=True).encode()).hexdigest()[:20]
    key = f'[harness-incident:{digest}]'
    observation = f'[harness-run:{run}:{attempt}]'
    run_url = f'https://github.com/{REPO}/actions/runs/{run}'
    details = '\n'.join(f"- {f['file']}: {f['title']}\n  {f['error']}" for f in failed)
    label = 'REHEARSAL: intentional test failure; the application is healthy. Deployment reference only.' if rehearsal else 'Actual smoke failure; inspect the linked run artifacts.'
    text = (f'{label}\n{observation}\nCommit: {sha}\nSite: {SITE}\nRun and evidence artifacts: {run_url}\n'
            f'Classification: {classification}\nIdentity before/after: '
            f"{evidence.get('identityBefore', 'unknown')}/{evidence.get('identityAfter', 'unknown')}\n"
            f'Failed checks:\n{details or "No trustworthy assertion report. Inspect runner/deployment logs."}\n')
    return {'key':key,'observation':observation,'name':f'[{"Reporting rehearsal" if rehearsal else "Smoke incident"}] {classification} {digest[:8]}',
            'description':f'{TRIAGE}\n{key}\n\nConfirm reproduction before authorizing a code repair. '
                          f'This incident is not proof of an application bug.\n\n{text}',
            'update':text,'classification':classification}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('ClickUp redirect refused; credential remains on api.clickup.com')


class ClickUp:
    def __init__(self, token):
        if not token: raise ValueError('CLICKUP_TOKEN is missing')
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, path, body=None, method=None):
        request = urllib.request.Request('https://api.clickup.com/api/v2'+path,
            data=json.dumps(body).encode() if body is not None else None, method=method,
            headers={'Authorization':self.token,'Content-Type':'application/json'})
        try:
            with self.opener.open(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'ClickUp HTTP {error.code}; response body withheld') from None
        except (TimeoutError, urllib.error.URLError):
            raise RuntimeError('ClickUp request failed or timed out; inspect task before retrying a write') from None

    def open_tasks(self):
        tasks = []
        for page in range(100):
            data = self.request(f'/list/{LIST_ID}/task?page={page}&include_closed=false')
            batch = data.get('tasks')
            if not isinstance(batch,list): raise ValueError('Invalid task-list response')
            tasks.extend(t for t in batch if t.get('status',{}).get('type') not in ('closed','done'))
            if data.get('last_page') or len(batch)<100: return tasks
        raise ValueError('Task pagination limit reached; refusing to create a possible duplicate')

    def create(self, incident):
        return self.request(f'/list/{LIST_ID}/task',
                            {'name':incident['name'],'description':incident['description'],'notify_all':False})

    def update(self, task, description):
        return self.request('/task/'+quote(str(task['id']),safe=''),{'description':description},'PUT')


def publish(api, incident):
    if incident is None: return {'action':'no_failure'}
    matches = [t for t in api.open_tasks()
               if incident['key'] in (t.get('description') or '').splitlines()]
    if len(matches)>1: raise ValueError('Multiple matching incidents; resolve duplicates manually')
    if matches:
        task=matches[0]
        description=task.get('description') or ''
        if incident['observation'] in description.splitlines():
            return {'action':'already_reported','task_id':task['id'],'url':task.get('url')}
        updated=description+'\n\n'+incident['update']
        if len(updated)>50000: raise ValueError('Incident history too long; refusing to discard existing notes')
        api.update(task,updated)
        return {'action':'updated','task_id':task['id'],'url':task.get('url')}
    task=api.create(incident)
    return {'action':'created','task_id':task['id'],'url':task.get('url')}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--send',action='store_true')
    args=parser.parse_args()
    evidence=json.loads(args.evidence.read_text())
    # Missing/malformed reports represent an infrastructure failure, never a code repair instruction.
    try: report=json.loads(args.report.read_text())
    except (FileNotFoundError,json.JSONDecodeError): report={}
    incident=make_incident(evidence,report)
    if args.send:
        result=publish(ClickUp(os.environ.get('CLICKUP_TOKEN')),incident)
    else:
        result={'action':'dry_run','incident':incident}
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'Incident reporting stopped: {exc}',file=sys.stderr)
        sys.exit(1)
