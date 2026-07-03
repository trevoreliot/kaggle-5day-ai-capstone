import os
import json

_RULES_DB = None

def get_rules_db():
    global _RULES_DB
    if _RULES_DB is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        rules_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'rules.json')
        try:
            with open(rules_path, 'r') as f:
                _RULES_DB = json.load(f)
        except FileNotFoundError:
            _RULES_DB = {}
    return _RULES_DB

def _check_conflict(c1: str, c2: str, rule_type: str) -> str | None:
    rules = get_rules_db()
    # Check if c1 or its parent prefixes have an exclude rule for c2
    # E.g., if c1="A04.0", check "A04.0", "A04", "A0"
    for prefix_len in range(len(c1), 2, -1):
        prefix = c1[:prefix_len].rstrip('.')
        if prefix in rules:
            for excluded in rules[prefix].get(rule_type, []):
                # c2 conflicts if it starts with the excluded prefix
                # e.g., if excluded="A18.3", and c2="A18.32", it's a conflict
                if c2.startswith(excluded):
                    return f"Code {c1} has an {rule_type} note for {excluded} which conflicts with {c2}."
    return None

def check_excludes1(primary_code: str, additional_code: str) -> dict:
    """
    Checks if there's an Excludes1 conflict between two codes.
    Excludes1 means 'NOT CODED HERE' (mutually exclusive).
    """
    conflict_msg = _check_conflict(primary_code, additional_code, "excludes1") or _check_conflict(additional_code, primary_code, "excludes1")
    if conflict_msg:
        return {"valid": False, "reason": conflict_msg, "rule_type": "Excludes1"}
    return {"valid": True, "reason": "No Excludes1 conflict found.", "rule_type": "Excludes1"}

def check_coding_rules(codes: list[str]) -> list[dict]:
    """
    Validates a list of ICD-10-CM codes against coding conventions.
    
    Args:
        codes: A list of ICD-10-CM codes to validate.
        
    Returns:
        A list of validation results highlighting any violations.
    """
    results = []
    
    # 1. Check for Excludes1 conflicts
    for i, code1 in enumerate(codes):
        for code2 in codes[i+1:]:
            res = check_excludes1(code1, code2)
            if not res["valid"]:
                results.append(res)
                
    # 2. Check for 7th character requirement (placeholder logic for demo)
    for code in codes:
        if code.startswith("S") or code.startswith("T"):
            if len(code.replace(".", "")) < 7:
                results.append({
                    "valid": False,
                    "reason": f"Code {code} requires a 7th character extension (e.g., A, D, S) for injuries.",
                    "rule_type": "7th_character_required"
                })

    if not results:
        results.append({"valid": True, "reason": "All codes passed basic validation.", "rule_type": "all"})
        
    return results
