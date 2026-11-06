import glob, json

report_path = sorted(glob.glob('evals/reports/*.json'))[-1]
report = json.load(open(report_path, encoding='utf-8'))
golden = {c['number']: c for c in map(json.loads, open('data/golden.jsonl', encoding='utf-8'))}

print('report:', report_path, '\n')
for f in report['failures']:
    c = golden[f['number']]
    print('=' * 80)
    print(f'#{c["number"]}  expected={f["expected"]}  got={f["got"]}')
    print('https://github.com/microsoft/TypeScript/issues/' + str(c['number']))
    print('TITLE:', c['title'])
    print('LABELS:', c['labels'])
    print('BODY:', c['body'][:600].replace('\n', ' '))