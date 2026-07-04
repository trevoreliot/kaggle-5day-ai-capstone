import pytest
from src.rules import check_code_first, check_use_additional_code, check_7th_character

# Mock the rules DB for isolated unit testing
MOCK_RULES_DB = {
    "A40": {
        "codeFirst": ["O08.82"],
        "useAdditionalCode": [],
        "requires_7th_char": False
    },
    "I10": {
        "codeFirst": [],
        "useAdditionalCode": ["I50"],
        "requires_7th_char": False
    },
    "S82.1": {
        "codeFirst": [],
        "useAdditionalCode": [],
        "requires_7th_char": True
    },
    "T14": {
        "codeFirst": [],
        "useAdditionalCode": [],
        "requires_7th_char": True
    }
}

@pytest.fixture(autouse=True)
def mock_get_rules_db(monkeypatch):
    monkeypatch.setattr("src.rules.get_rules_db", lambda: MOCK_RULES_DB)

def test_code_first_valid():
    # O08.82 is the etiology and sequenced BEFORE A40 (manifestation)
    codes = ["O08.82", "A40.1"]
    results = check_code_first(codes)
    assert len(results) == 0

def test_code_first_missing():
    # A40 requires O08.82 to be coded first, but it is missing
    codes = ["A40.1"]
    results = check_code_first(codes)
    assert len(results) == 1
    assert "missing" in results[0]["reason"]
    assert results[0]["rule_type"] == "CodeFirst"

def test_code_first_wrong_order():
    # O08.82 is present, but sequenced AFTER A40
    codes = ["A40.1", "O08.82"]
    results = check_code_first(codes)
    assert len(results) == 1
    assert "BEFORE" in results[0]["reason"]
    assert results[0]["rule_type"] == "CodeFirst"

def test_use_additional_code_valid():
    # I10 has a rule to use I50 as an additional code, and it's present
    codes = ["I10", "I50.9"]
    results = check_use_additional_code(codes)
    assert len(results) == 0

def test_use_additional_code_missing():
    # I10 requires I50, but it is missing
    codes = ["I10"]
    results = check_use_additional_code(codes)
    assert len(results) == 1
    assert "missing" in results[0]["reason"]
    assert results[0]["rule_type"] == "UseAdditionalCode"

def test_7th_character_valid():
    # S82.1 requires 7th character, and it has 7 characters (excluding dot)
    codes = ["S82.101A"]
    results = check_7th_character(codes)
    assert len(results) == 0

def test_7th_character_invalid_short():
    # S82.1 requires 7th character, but it only has 5
    codes = ["S82.1"]
    results = check_7th_character(codes)
    assert len(results) == 1
    assert "7th character extension" in results[0]["reason"]
    assert results[0]["rule_type"] == "7th_character_required"

def test_7th_character_placeholder_x():
    # T14 requires 7th character, it's short, so it must be padded with X to get to 7
    # T14.9XXA is 7 chars. T14.9A is wrong.
    codes_valid = ["T14.9XXA"]
    results = check_7th_character(codes_valid)
    assert len(results) == 0

    codes_invalid = ["T14.9A"]
    results2 = check_7th_character(codes_invalid)
    assert len(results2) == 1
