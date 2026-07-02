import os
import requests
import logging

logger = logging.getLogger(__name__)

def query_umls(term: str) -> dict:
    """
    Query the UMLS API to normalize medical jargon or symptoms.
    
    Args:
        term: The medical term to normalize.
        
    Returns:
        A dictionary containing the normalized concept and details.
    """
    # Use KaggleSecrets if on Kaggle, otherwise use os.getenv
    try:
        from kaggle_secrets import UserSecretsClient
        user_secrets = UserSecretsClient()
        api_key = user_secrets.get_secret("UMLS_API_KEY")
    except ImportError:
        api_key = os.getenv("UMLS_API_KEY")
    
    # PLACEHOLDER LOGIC: Currently waiting for UMLS API approval
    # We will return mocked responses for demonstration purposes
    logger.info(f"Querying UMLS placeholder for term: {term}")
    
    term_lower = term.lower()
    
    # Simple mocked database for the demo
    mock_db = {
        "heart attack": {
            "concept_id": "C0027051",
            "name": "Myocardial Infarction",
            "semantic_type": "Disease or Syndrome",
            "is_definitive": True
        },
        "headache": {
            "concept_id": "C0018681",
            "name": "Headache",
            "semantic_type": "Sign or Symptom",
            "is_definitive": False
        },
        "type 2 diabetes": {
            "concept_id": "C0011860",
            "name": "Diabetes Mellitus, Non-Insulin-Dependent",
            "semantic_type": "Disease or Syndrome",
            "is_definitive": True
        }
    }
    
    for key, value in mock_db.items():
        if key in term_lower or term_lower in key:
            return value
            
    return {
        "concept_id": "UNKNOWN",
        "name": term,
        "semantic_type": "Unknown",
        "message": "Term not found in mock DB. Real API would query UMLS here."
    }
