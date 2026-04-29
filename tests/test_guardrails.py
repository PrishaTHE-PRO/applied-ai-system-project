from ai.guardrails import is_unsafe_request


def test_diagnosis_blocked():
    assert is_unsafe_request("Can you diagnose my dog's cough?")


def test_dosage_blocked():
    assert is_unsafe_request("How much ibuprofen should I give a 30 lb dog?")


def test_normal_question_allowed():
    assert not is_unsafe_request("How often should I bathe my dog?")