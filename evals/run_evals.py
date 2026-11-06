import json, os, re, time, sys
from collections import Counter
from datetime import datetime
from langfuse import get_client
from app.triage import triage_issue, MODEL, PROMPT_VERSION, PROVIDER

CLASSES = ['bug', 'feature', 'question']
DATA = os.getenv('EVAL_DATA', 'data/golden.jsonl')
DATASET = os.path.splitext(os.path.basename(DATA))[0]

class DailyQuotaExceeded(Exception):
    pass

def cache_path():
    safe = re.sub(r'[^A-Za-z0-9._-]', '_', f'{PROMPT_VERSION}__{MODEL}')
    return f'evals/cache/{safe}.json'

def load_cache():
    p = cache_path()
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    os.makedirs('evals/cache', exist_ok=True)
    with open(cache_path(), 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=1)

def call_with_retry(case, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return triage_issue(case['title'], case['body'], issue_number=case['number']).model_dump()
        except Exception as e:
            msg = str(e)
            print(f'  attempt {attempt} for #{case["number"]} failed: {type(e).__name__}: {msg[:300]}')
            if 'perday' in msg.lower().replace(' ', ''):
                raise DailyQuotaExceeded(msg)
            m = re.search(r'retry in ([\d.]+)s', msg)
            wait = float(m.group(1)) + 2 if m else 20 * attempt
            print(f'  waiting {wait:.0f}s')
            time.sleep(wait)
    return None

def run_suite(limit=None, pause=None):
    if pause is None:
        pause = 0 if PROVIDER == 'ollama' else 15
    cases = [json.loads(l) for l in open(DATA, encoding='utf-8')]
    if limit:
        cases = cases[:limit]
    print(f'dataset: {DATA} | {len(cases)} cases | model: {MODEL} | prompt: {PROMPT_VERSION}\n')

    cache = load_cache()
    totals, hits, confusion = Counter(), Counter(), Counter()
    failures, errors = [], 0

    try:
        for n, c in enumerate(cases, 1):
            key = str(c['number'])
            expected = c['expected_category']
            totals[expected] += 1

            if key in cache:
                out, from_cache = cache[key], True
            else:
                out, from_cache = call_with_retry(c), False
                if out is not None:
                    cache[key] = out
                    save_cache(cache)

            if out is None:
                errors += 1
                failures.append({'number': c['number'], 'expected': expected, 'got': 'ERROR', 'title': c['title']})
            else:
                confusion[(expected, out['category'])] += 1
                if out['category'] == expected:
                    hits[expected] += 1
                else:
                    failures.append({'number': c['number'], 'expected': expected,
                                     'got': out['category'], 'title': c['title']})
            tag = ' (cached)' if from_cache else ''
            print(f'[{n}/{len(cases)}] #{c["number"]} expected={expected} got={out["category"] if out else "ERROR"}{tag}')
            if not from_cache and pause:
                time.sleep(pause)
    except DailyQuotaExceeded:
        print('\nDaily quota reached. Progress is saved. Rerun later or switch models.')
        get_client().flush()
        sys.exit(1)

    get_client().flush()
    return {
        'dataset': DATASET,
        'model': MODEL,
        'prompt_version': PROMPT_VERSION,
        'cases': len(cases),
        'errors': errors,
        'category_accuracy': sum(hits.values()) / len(cases),
        'per_class_recall': {k: (hits[k] / totals[k] if totals[k] else None) for k in CLASSES},
        'confusion': {f'{e}->{g}': v for (e, g), v in confusion.items()},
        'failures': failures,
    }

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    result = run_suite(limit=limit)
    os.makedirs('evals/reports', exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = f'evals/reports/{stamp}_{DATASET}_{result["prompt_version"]}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print('\n=== RESULT ===')
    print('dataset:', result['dataset'], '| model:', result['model'], '| prompt:', result['prompt_version'])
    print('accuracy:', round(result['category_accuracy'], 3), '| errors:', result['errors'])
    print('per-class recall:', result['per_class_recall'])
    print('confusion (expected->got):', result['confusion'])
    print('failures:')
    for f_ in result['failures']:
        print(f'  #{f_["number"]} expected={f_["expected"]} got={f_["got"]} | {f_["title"][:80]}')
    print('saved:', path)