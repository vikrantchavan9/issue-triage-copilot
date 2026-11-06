import os, json, requests
from dotenv import load_dotenv
load_dotenv()

REPO = 'microsoft/TypeScript'   # change this
HEADERS = {'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}

def fetch(pages=30):
    out = []
    for page in range(1, pages + 1):
        r = requests.get(
            f'https://api.github.com/repos/{REPO}/issues',
            params={'state': 'all', 'per_page': 100, 'page': page},
            headers=HEADERS,
        )
        r.raise_for_status()
        for i in r.json():
            if 'pull_request' in i:   # this endpoint also returns PRs
                continue
            out.append({
                'number': i['number'],
                'title': i['title'],
                'body': (i['body'] or '')[:3000],
                'labels': [l['name'] for l in i['labels']],
            })
    return out

with open('data/issues.jsonl', 'w') as f:
    for issue in fetch():
        f.write(json.dumps(issue) + '\n')