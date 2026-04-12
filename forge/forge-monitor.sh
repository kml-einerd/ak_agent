#!/bin/bash
# Forge Monitor — Dashboard em tempo real das tasks no PM-OS
# Uso: ./forge-monitor.sh [filtro]
# Ex:  ./forge-monitor.sh          # todas as tasks Forge
#      ./forge-monitor.sh Standard  # só tasks com "Standard" no título

API="https://pm-api-852176378633.us-central1.run.app"
FILTER="${1:-Forge}"
INTERVAL=5

while true; do
    clear
    NOW=$(date "+%H:%M:%S")

    # Fetch tasks
    TASKS=$(curl -s "$API/api/tasks" 2>/dev/null)

    if [ -z "$TASKS" ] || [ "$TASKS" = "null" ]; then
        echo "╔══════════════════════════════════════════════════════════╗"
        echo "║  FORGE MONITOR — API offline                            ║"
        echo "╚══════════════════════════════════════════════════════════╝"
        sleep $INTERVAL
        continue
    fi

    # Parse with Python (json in bash is painful)
    python3 -c "
import json, sys

tasks = json.loads('''$TASKS''')
if not isinstance(tasks, list):
    print('API returned non-list')
    sys.exit(0)

filt = '$FILTER'
forge_tasks = [t for t in tasks if filt in (t.get('title') or '')]
forge_tasks.reverse()  # newest first

total = len(forge_tasks)
running = sum(1 for t in forge_tasks if t.get('status') == 'running')
done = sum(1 for t in forge_tasks if t.get('status') in ('done', 'passed'))
failed = sum(1 for t in forge_tasks if t.get('status') == 'failed')
pending = sum(1 for t in forge_tasks if t.get('status') == 'pending')

pct = (done / total * 100) if total > 0 else 0
bar_len = 40
filled = int(bar_len * done / total) if total > 0 else 0
bar = '█' * filled + '░' * (bar_len - filled)

print('╔══════════════════════════════════════════════════════════╗')
print(f'║  FORGE MONITOR — {filt:<38}   $NOW ║')
print(f'║  {bar} {pct:5.1f}%  ║')
print(f'║  Done: {done}  Running: {running}  Pending: {pending}  Failed: {failed}  Total: {total:<3}  ║')
print('╠══════════════════════════════════════════════════════════╣')

icons = {
    'done': '✅', 'passed': '✅',
    'running': '⏳', 'pending': '🔄',
    'failed': '❌',
}

for t in forge_tasks[:25]:  # Show last 25
    status = t.get('status', '?')
    icon = icons.get(status, '❓')
    title = (t.get('title') or t.get('id', '?'))[:42]
    agent = (t.get('agent') or '-')[:6]
    provider = (t.get('provider') or '-')[:6]
    tid = (t.get('id') or '?')[-8:]

    print(f'║  {icon} {title:<42} {agent:<6} {provider:<6} ...{tid} ║')

print('╚══════════════════════════════════════════════════════════╝')
print(f'  Ctrl+C pra sair. Atualiza a cada {$INTERVAL}s.')
print(f'  API: $API')
" 2>/dev/null

    sleep $INTERVAL
done
