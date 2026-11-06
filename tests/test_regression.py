from evals.run_evals import run_suite

def test_category_accuracy():
    result = run_suite(limit=30)   # smaller subset keeps CI fast
    assert result['category_accuracy'] >= 0.80