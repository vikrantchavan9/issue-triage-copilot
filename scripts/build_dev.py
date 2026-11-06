import json, random
from collections import defaultdict

random.seed(7)
LABEL_MAP = {'bug': 'bug', 'suggestion': 'feature', 'question': 'question'}
PER_CLASS = {'bug': 15, 'feature': 15, 'question': 20}

issues = [json.loads(l) for l in open('data/issues.jsonl', encoding='utf-8')]
golden_ids = {json.loads(l)['number'] for l in open('data/golden.jsonl', encoding='utf-8')}

pool = defaultdict(list)
for i in issues:
    if i['number'] in golden_ids:
        continue
    cats = {LABEL_MAP[l.lower()] for l in i['labels'] if l.lower() in LABEL_MAP}
    if len(cats) == 1:
        i['expected_category'] = cats.pop()
        pool[i['expected_category']].append(i)

print('available:', {k: len(v) for k, v in pool.items()})
dev = []
for cls, n in PER_CLASS.items():
    random.shuffle(pool[cls])
    dev += pool[cls][:n]
random.shuffle(dev)

with open('data/dev.jsonl', 'w', encoding='utf-8') as f:
    for i in dev:
        f.write(json.dumps(i) + '\n')
print('dev size:', len(dev))