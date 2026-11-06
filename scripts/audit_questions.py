import glob, json, os, sys, requests
from dotenv import load_dotenv

load_dotenv()
H = {'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}
REPO = 'microsoft/TypeScript'

report_path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob('evals/reports/*_dev_*.json'))[-1]
report = json.load(open(report_path, encoding='utf-8'))

data = {}
for fn in ('data/golden.jsonl', 'data/dev.jsonl'):
    for line in open(fn, encoding='utf-8'):
        c = json.loads(line)
        data[c['number']] = c

fails = [f for f in report['failures'] if f['expected'] == 'question' and f['got'] == 'bug']
print(report_path, '| question->bug failures:', len(fails))

for f in fails[:10]:
    c = data[f['number']]
    print('=' * 80)
    print(f'#{c["number"]} {c["title"]}')
    print(f'https://github.com/{REPO}/issues/{c["number"]}')
    print('LABELS:', c['labels'])
    print('BODY:', c['body'][:500].replace('\n', ' '))
    r = requests.get(f'https://api.github.com/repos/{REPO}/issues/{c["number"]}/comments',
                     headers=H, params={'per_page': 3})
    if r.ok:
        for cm in r.json():
            print('  COMMENT by', cm['user']['login'], ':', cm['body'][:300].replace('\n', ' '))