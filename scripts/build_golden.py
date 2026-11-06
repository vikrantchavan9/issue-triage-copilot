import json, random
from collections import defaultdict

random.seed(42)

LABEL_MAP = {'bug': 'bug', 'suggestion': 'feature', 'question': 'question'}
PER_CLASS = {'bug': 20, 'feature': 20, 'question': 10}

issues = [json.loads(l) for l in open('data/issues.jsonl')]

by_class = defaultdict(list)
for i in issues:
    cats = {LABEL_MAP[l.lower()] for l in i['labels'] if l.lower() in LABEL_MAP}
    if len(cats) == 1:                      # skip unlabeled or conflicting issues
        i['expected_category'] = cats.pop()
        by_class[i['expected_category']].append(i)

print('available per class:', {k: len(v) for k, v in by_class.items()})

golden = []
for cls, n in PER_CLASS.items():
    random.shuffle(by_class[cls])
    golden += by_class[cls][:n]
random.shuffle(golden)

golden_ids = {i['number'] for i in golden}
history = [i for i in issues if i['number'] not in golden_ids]

with open('data/golden.jsonl', 'w') as f:
    for i in golden:
        f.write(json.dumps(i) + '\n')
with open('data/history.jsonl', 'w') as f:
    for i in history:
        f.write(json.dumps(i) + '\n')

print('golden:', len(golden), '| history:', len(history))