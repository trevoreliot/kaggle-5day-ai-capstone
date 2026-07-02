def check_excludes1(primary_code: str, additional_code: str) -> dict:
    """
    Checks if there's an Excludes1 conflict between two codes.
    Excludes1 means 'NOT CODED HERE' (mutually exclusive).
    """
    # Placeholder logic - in reality, this would query the Tabular List rules
    conflicts = {
        ("J00", "J01.90"): "Acute rhinopharyngitis (J00) has an Excludes1 note for acute sinusitis (J01.-).",
        ("E10.9", "E11.9"): "Type 1 diabetes mellitus (E10.-) has an Excludes1 note for Type 2 diabetes mellitus (E11.-)."
    }
    
    conflict_msg = conflicts.get((primary_code, additional_code)) or conflicts.get((additional_code, primary_code))
    
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
                
    # 2. Check for 7th character requirement (placeholder)
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
