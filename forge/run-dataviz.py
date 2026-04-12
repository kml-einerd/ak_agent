#!/usr/bin/env python3
"""Dispatch DataViz system tasks to PM-OS forge workers."""
import sys, json, time, os
sys.path.insert(0, os.path.dirname(__file__))
import forge

forge.PM_API_URL = 'https://pm-api-852176378633.us-central1.run.app'
forge.PM_API_KEY = ''

# Read the plan
with open(os.path.join(os.path.dirname(__file__), 'plans/data-viz-system.md')) as f:
    plan = f.read()

sws = forge._parse_plan_to_subwaves(plan)
run_id = f'forge-dataviz-{int(time.time())}'

print(f'╔{"═"*66}╗')
print(f'║  CODE FORGE — DataViz System ({len(sws)} tasks)' + ' '*(66-42-len(str(len(sws)))) + '║')
print(f'║  Run: {run_id:<58} ║')
print(f'╚{"═"*66}╝')
print()

results = []
start = time.time()

for sw in sws:
    md = forge._build_claude_md(sw)
    r = forge.submit_task({
        'type': 'code',
        'title': f'DataViz — {sw["id"]}: {sw["title"][:40]}',
        'agent': 'dex',
        'provider': 'haiku',
        'instructions': [
            f'## CLAUDE.md\n{md[:800]}',
            f'## Task\n{sw["task_description"][:1000]}',
            'Implement what is described. Output the code. FORGE_COMPLETE when done.',
        ],
        'acceptance': sw.get('acceptance') or sw.get('test_command') or 'Task completed',
    })
    tid = r.get('task_id')
    results.append((sw['id'], sw['title'][:35], tid))
    icon = '✅' if tid else '❌'
    print(f'  {icon} {sw["id"]:<8} {sw["title"][:40]:<40} → {tid or "FAIL"}')
    time.sleep(0.15)

ok = sum(1 for _,_,tid in results if tid)
submit_time = time.time() - start
print(f'\n  Submetidas: {ok}/{len(results)} em {submit_time:.1f}s')
print(f'  Aguardando...\n')

# Poll
total = len(results)
for attempt in range(60):
    time.sleep(10)
    done=0; running=0; failed=0
    for _,_,tid in results:
        if not tid: continue
        s = forge.get_task(tid)
        st = s.get('status','?')
        if st in ('done','passed'): done += 1
        elif st == 'failed': failed += 1
        elif st == 'running': running += 1

    elapsed = int(time.time() - start)
    completed = done + failed
    pct = (completed/total*100) if total else 0
    filled = int(40 * completed / total) if total else 0
    bar = chr(9608)*filled + chr(9617)*(40-filled)
    print(f'  [{elapsed:>3}s] {bar} {pct:5.1f}%  Done:{done} Run:{running} Fail:{failed}')
    if completed >= total: break

elapsed = int(time.time() - start)
done_count = sum(1 for _,_,tid in results if tid and forge.get_task(tid).get('status') in ('done','passed'))
fail_count = sum(1 for _,_,tid in results if tid and forge.get_task(tid).get('status') == 'failed')

print(f'\n{"═"*68}')
print(f'  Done: {done_count}/{total}  Failed: {fail_count}  Time: {elapsed}s ({elapsed//60}m{elapsed%60}s)')
print(f'  100% Cloud Run — zero local')
print(f'{"═"*68}')

# Save results
with open(f'/tmp/forge-dataviz-{run_id}.json', 'w') as f:
    json.dump({'run_id': run_id, 'tasks': [(n,t,tid) for n,t,tid in results], 'done': done_count, 'failed': fail_count}, f, indent=2)
