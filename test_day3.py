import sys
import os

# Add src to Python path so we can import it
sys.path.insert(0, os.path.abspath("."))

from src.agent_prompts import SYSTEM_PROMPT, ENTITY_EXTRACTION_PROMPT, RECONCILIATION_PROMPT
from src.download_patient_data import download_patient_records

def test_prompts_exist():
    """Test that all prompts are defined and are non-empty strings."""
    assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 0
    assert isinstance(ENTITY_EXTRACTION_PROMPT, str) and len(ENTITY_EXTRACTION_PROMPT) > 0
    assert isinstance(RECONCILIATION_PROMPT, str) and len(RECONCILIATION_PROMPT) > 0

def test_prompts_formatting():
    """Test that the extraction and reconciliation prompts can be formatted with their expected kwargs."""
    # Test entity extraction prompt
    clinical_note = "Patient presents with chest pain."
    formatted_ext = ENTITY_EXTRACTION_PROMPT.format(clinical_note=clinical_note)
    assert clinical_note in formatted_ext
    
    # Test reconciliation prompt
    extracted = "[{'entity_name': 'chest pain'}]"
    assigned = "['R07.9']"
    formatted_rec = RECONCILIATION_PROMPT.format(extracted_entities=extracted, assigned_codes=assigned)
    assert extracted in formatted_rec
    assert assigned in formatted_rec

def test_download_patient_data_function():
    """
    Test that the download function exists and is callable. 
    We just check the definition to avoid re-triggering large downloads in a fast test suite.
    """
    assert callable(download_patient_records)

if __name__ == "__main__":
    print("Running Day 3 verification tests...")
    test_prompts_exist()
    test_prompts_formatting()
    test_download_patient_data_function()
    print("All Day 3 tests passed!")
