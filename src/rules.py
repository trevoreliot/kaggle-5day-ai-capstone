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
    seen_prefixes = set()
    for prefix_len in range(len(c1), 2, -1):
        prefix = c1[:prefix_len].rstrip('.')
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        if prefix in rules:
            for excluded in rules[prefix].get(rule_type, []):
                if c2.startswith(excluded):
                    return f"Code {c1} has an {rule_type} note for {excluded} which conflicts with {c2}."
    return None

def check_excludes1(primary_code: str, additional_code: str) -> dict:
    """
    Checks if there's an Excludes1 conflict between two codes.
    """
    conflict_msg = _check_conflict(primary_code, additional_code, "excludes1") or _check_conflict(additional_code, primary_code, "excludes1")
    if conflict_msg:
        return {"valid": False, "reason": conflict_msg, "rule_type": "Excludes1"}
    return {"valid": True, "reason": "No Excludes1 conflict found.", "rule_type": "Excludes1"}

def check_code_first(codes: list[str]) -> list[dict]:
    results = []
    rules = get_rules_db()
    for i, code in enumerate(codes):
        seen_prefixes = set()
        for prefix_len in range(len(code), 2, -1):
            prefix = code[:prefix_len].rstrip('.')
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            if prefix in rules:
                for cf in rules[prefix].get("codeFirst", []):
                    found_index = -1
                    for j, assigned_code in enumerate(codes):
                        if assigned_code.startswith(cf):
                            found_index = j
                            break
                    if found_index == -1:
                        results.append({
                            "valid": False, 
                            "reason": f"Code {code} has a 'Code First' rule for {cf}. The underlying condition ({cf}) is missing from the assigned codes.",
                            "rule_type": "CodeFirst"
                        })
                    elif found_index > i:
                        results.append({
                            "valid": False, 
                            "reason": f"Code {code} has a 'Code First' rule for {cf}. The underlying condition ({codes[found_index]}) must be sequenced BEFORE {code}.",
                            "rule_type": "CodeFirst"
                        })
    return results

def check_use_additional_code(codes: list[str]) -> list[dict]:
    results = []
    rules = get_rules_db()
    for code in codes:
        seen_prefixes = set()
        for prefix_len in range(len(code), 2, -1):
            prefix = code[:prefix_len].rstrip('.')
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            if prefix in rules:
                for uac in rules[prefix].get("useAdditionalCode", []):
                    found = any(assigned_code.startswith(uac) for assigned_code in codes)
                    if not found:
                        results.append({
                            "valid": False,
                            "reason": f"Code {code} has a 'Use Additional Code' rule for {uac}, which is missing from the assigned codes.",
                            "rule_type": "UseAdditionalCode"
                        })
    return results

def check_7th_character(codes: list[str]) -> list[dict]:
    results = []
    rules = get_rules_db()
    for code in codes:
        clean_code = code.replace(".", "")
        for prefix_len in range(len(code), 2, -1):
            prefix = code[:prefix_len].rstrip('.')
            if prefix in rules and rules[prefix].get("requires_7th_char", False):
                if len(clean_code) < 7:
                    results.append({
                        "valid": False,
                        "reason": f"Code {code} requires a 7th character extension. If the base code is less than 6 characters, you must use placeholder 'X' to reach the 7th character.",
                        "rule_type": "7th_character_required"
                    })
                break
    return results

def check_coding_rules(codes: list[str]) -> list[dict]:
    """
    Validates a list of ICD-10-CM codes against coding conventions.
    """
    results = []
    
    # 1. Check for Excludes1 conflicts
    for i, code1 in enumerate(codes):
        for code2 in codes[i+1:]:
            res = check_excludes1(code1, code2)
            if not res["valid"]:
                results.append(res)
                
    # 2. Check Code First rules
    results.extend(check_code_first(codes))
    
    # 3. Check Use Additional Code rules
    results.extend(check_use_additional_code(codes))
    
    # 4. Check 7th character requirements
    results.extend(check_7th_character(codes))

    if not results:
        results.append({"valid": True, "reason": "All codes passed basic validation.", "rule_type": "all"})
        
    return results
