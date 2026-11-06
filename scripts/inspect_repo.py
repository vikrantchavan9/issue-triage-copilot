import os, sys, requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) < 2:
    sys.exit('Usage: python scripts/inspect_repo.py OWNER/REPO [pages]')

repo = sys.argv[1]
pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5
H = {'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}

# Repo info and license
r = requests.get(f'https://api.github.com/repos/{repo}', headers=H)
r.raise_for_status()
info = r.json()
print('repo:', info['full_name'])
print('license:', (info.get('license') or {}).get('spdx_id'))

# Sample issues and count labels
labels = Counter()
total = labeled = 0
for page in range(1, pages + 1):
    r = requests.get(
        f'https://api.github.com/repos/{repo}/issues',
        params={'state': 'all', 'per_page': 100, 'page': page},
        headers=H,
    )
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    for i in batch:
        if 'pull_request' in i:      # this endpoint also returns PRs, skip them
            continue
        total += 1
        names = [l['name'] for l in i['labels']]
        if names:
            labeled += 1
        labels.update(names)

print(f'issues sampled: {total} (with at least one label: {labeled})')
print('top labels:')
for name, c in labels.most_common(30):
    print(f'  {c:4d}  {name}')

dupes = [n for n in labels if 'dup' in n.lower()]
print('duplicate-like labels:', dupes or 'none found')