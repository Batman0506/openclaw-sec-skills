#!/bin/bash
# Run auto-collect.py with GitHub token from credentials
TOKEN=$(python3 -c "
import json
with open('/home/ubuntu/.openclaw/credentials/tokens.json') as f:
    t = json.load(f)
gt = t['github']['token'] if isinstance(t['github'], dict) else t['github']
print(gt)
")
export GITHUB_TOKEN="$TOKEN"
cd /home/ubuntu/.openclaw/workspace/openclaw-sec-skills

# Run auto-collect
python3 -u scripts/auto-collect.py 2>&1 | tee /tmp/secskills-run.log

# Check for changes and push (直连，不用代理)
if git diff --quiet README.md scripts/auto-collect.py 2>/dev/null; then
    echo "No changes to push"
else
    git add -A
    git commit -m "Auto-update: $(date +%Y-%m-%d) - Chinese security skills"
    git push 2>&1 | tail -5
fi
