"""Packet-clone orchestration and independently rerun acceptance, without product edits."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path.cwd()


def run(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs)


def queue(spec):
    tid, role, task, targets, context, interfaces, criteria, verify = spec
    clone = ROOT / '.agent/workspaces' / tid.replace('-', '')
    packet = f'''Ignore AGENTS.md except this packet; the packet is your only authority.
# PACKET {tid}
role: {role}. You are not alone in the codebase; preserve others' edits. No commits.
Workspace: {clone}; work only here.
## Task
{task}
## Target files
'''+''.join('- '+p+'\n' for p in targets)+f'''## Read-only context
{context}
## Interfaces
{interfaces}
## Acceptance criteria
{criteria}
## Boundaries
At most 3 target files and 150 changed lines. Read only listed files, <=100 lines at once. No .env/secret reads or prints, real database/schema/data/volume writes, network/dependencies/fixed-port servers, recursive removal, API path/method/response changes, assertion weakening, blanket type-ignore/noqa. W1 never edits stores/fetch/API types/tests; W2 never edits markup/classes/tokens/tests; W3 never edits product code. Preserve all routes/features/copy/data hooks/aria/stateclasses/hashroutes. Need more context: FAILED requesting exact path. Verify offline, no real database connection.
## Verify
{verify}
## Output
Only JSON envelope: task_id,status PASSED|FAILED,files_modified[{{path,lines_added,lines_removed}}],diff_summary<=400chars,verification{{command,exit_code,tests_passed,tests_failed,duration_ms}},unresolved_blockers[]. Use exact Verify, PASSED only exit0. tests_passed and tests_failed are integers, 0 for static checks or collection. Do not add envelope keys. Static commands/collection are not passing test cases.
'''
    (ROOT/'.agent/packets'/f'{tid}.md').write_text(packet)
    subprocess.run(['git','clone','--quiet','--shared','--branch','overhaul/neo-brutal','.',str(clone)],check=True)
    (clone/'.venv').symlink_to(ROOT/'.venv')
    if any(p.startswith('frontend/') for p in targets):
        (clone/'frontend/node_modules').symlink_to(ROOT/'frontend/node_modules')
    p=ROOT/'.agent/NEXT_STATE.md'; s=p.read_text()
    block=f'### {tid} {role.split()[0]} — OPEN\n- target_files: '+', '.join(targets)+f'\n- contract: {task}\n- verify: {verify}\n\n'
    p.write_text(s.replace('## Queue\n','## Queue\n'+block))
    print('Packet and isolated clone ready:',tid)


def mark(e):
    tid=e['task_id']; commit=run(['git','rev-parse','--short','HEAD']).strip()
    p=ROOT/'.agent/CURRENT_STATE.md'; s=re.sub(r'git_head: .*','git_head: '+commit,p.read_text(),count=1)
    p.write_text(s+'\n- '+tid+' accepted'+commit+': '+e['diff_summary']+' Verify0.\n')
    p=ROOT/'.agent/NEXT_STATE.md'; s=p.read_text()
    s=re.sub(r'^### '+re.escape(tid)+r' .*?(?=^### |^## |\Z)','',s,flags=re.M|re.S)
    s=s.replace('## Done','## Done\n- '+tid+' accepted'+commit+'; verify0.')
    p.write_text(s)
    print('ACCEPTED',tid,commit)


def integrate(e):
    tid=e['task_id']; clone=ROOT/'.agent/workspaces'/tid.replace('-','')
    packet=(ROOT/'.agent/packets'/f'{tid}.md').read_text()
    verify=packet.split('## Verify\n')[1].split('\n## Output')[0].strip()
    assert e['status']=='PASSED' and e['verification']['command']==verify
    targets=[f['path'] for f in e['files_modified']]
    actual=run(['git','diff','--name-only'],cwd=clone).splitlines()
    untracked=run(['git','ls-files','-o','--exclude-standard'],cwd=clone).splitlines()
    new=[p for p in untracked if p in targets]
    assert not [p for p in untracked if p not in ('.venv','frontend/node_modules') and p not in targets],untracked
    assert sorted(actual+new)==sorted(targets),(actual,targets)
    stats=run(['git','diff','--numstat'],cwd=clone).splitlines()
    stats += [str(len((clone/p).read_text().splitlines()))+'\t0\t'+p for p in new]
    assert sum(int(x.split('\t')[0])+int(x.split('\t')[1]) for x in stats)<=150
    for stat,f in zip(sorted(stats,key=lambda x:x.split('\t')[2]),sorted(e['files_modified'],key=lambda f:f['path']),strict=True):
        a,d,p=stat.split('\t'); assert (int(a),int(d),p)==(f['lines_added'],f['lines_removed'],f['path'])
    subprocess.run(['git','diff','--check'],cwd=clone,check=True)
    data=subprocess.check_output(['git','diff','--binary','--',*targets],cwd=clone)
    for p in new:
        r=subprocess.run(['git','diff','--no-index','--binary','--','/dev/null',p],cwd=clone,capture_output=True)
        assert r.returncode==1; data+=r.stdout
    patch=ROOT/'.agent/results'/f'{tid}.patch'; patch.write_bytes(data)
    if targets:
        subprocess.run(['git','apply','--check',str(patch)],check=True)
        subprocess.run(['git','apply',str(patch)],check=True)
    (ROOT/'.agent/results'/f'{tid}.json').write_text(json.dumps(e)+'\n')
    r=subprocess.run(['bash','scripts/agent/accept.sh',tid],capture_output=True,text=True)
    output=r.stdout+r.stderr
    (ROOT/'.agent/results'/f'{tid}.accept.raw.log').write_text(output)
    print('accept.sh exit',r.returncode); print('\n'.join(output.splitlines()[-8:]))
    r.check_returncode(); mark(e)


if __name__=='__main__':
    {'queue':queue,'integrate':integrate,'mark':mark}[sys.argv[1]](json.loads(pathlib.Path(sys.argv[2]).read_text()))
