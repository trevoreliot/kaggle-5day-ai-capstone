def check_needs_reconciliation(agent_identified_codes: list[str], assigned_codes: list[str]) -> bool:
    """
    Checks if we need to run the LLM Reconciliation step to save tokens.
    If all agent-identified codes are already in the assigned_codes list, 
    there is no gap to reconcile, so we can skip the LLM call.
    """
    agent_set = set(agent_identified_codes)
    assigned_set = set(assigned_codes)
    
    # If the agent found codes that are NOT in the assigned list, we need to reconcile
    new_codes_found = agent_set - assigned_set
    
    if not new_codes_found:
        print("No new codes identified by the agent. Skipping Reconciliation to save tokens.")
        return False
        
    print(f"Agent found potential new codes: {new_codes_found}. Proceeding to Reconciliation.")
    return True
