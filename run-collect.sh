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
python3 -u scripts/auto-collect.py 2>&1 | tee /tmp/secskills-run.log
