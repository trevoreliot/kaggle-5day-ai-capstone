import os
from src.mcp_server import mcp
from src.download_patient_data import download_patient_records
from src.agent_prompts import SYSTEM_PROMPT, ENTITY_EXTRACTION_PROMPT, RECONCILIATION_PROMPT
from google import genai

# If you haven't run the ingestion scripts yet, you can uncomment these:
# from src.ingest_icd10 import ingest_data as ingest_icd10_data
# from src.ingest_rules import ingest as ingest_rules_data
# ingest_icd10_data()
# ingest_rules_data()

from src.pipeline import check_needs_reconciliation
def main():
    print("=== Medical Coding Assist Agent Initialization ===")
    
    # 1. Verify MCP Tools
    import asyncio
    print("\n[1] Registered MCP Tools:")
    tools = asyncio.run(mcp.list_tools())
    for tool in tools:
        print(f"  - {tool.name}")
        
    # 2. Download/Locate Dataset
    print("\n[2] Preparing Dataset:")
    dataset_path = download_patient_records()
    print(f"Data is available at {dataset_path}")
    
    # 3. Initialize LLM (Gemini)
    print("\n[3] Initializing LLM:")
    # Note: Ensure GEMINI_API_KEY environment variable is set
    try:
        client = genai.Client()
        print("Gemini Client Initialized! Prompts loaded successfully.")
    except Exception as e:
        print(f"Skipping Gemini Client initialization (API key might be missing): {e}")

    # 4. Pipeline Execution Check
    print("\n[4] Pipeline Execution Check Example:")
    patient_data_codes = ["E11.9", "I10"]
    agent_codes = ["E11.9", "I10", "E11.29"]
    if check_needs_reconciliation(agent_codes, patient_data_codes):
        print("-> Ready to run RECONCILIATION_PROMPT")

if __name__ == "__main__":
    main()

