import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
import os

nb = new_notebook()

# Markdown Header
nb.cells.append(new_markdown_cell("# Medical Coding Assist Agent\n\nThis is the flattened version of the Capstone project, fully self-contained for Kaggle submission."))

# Setup Cell
setup_code = """
# Install dependencies if running in a raw Kaggle environment
# !pip install chromadb pandas lxml requests google-genai kagglehub pydantic
import os
import json
import time
import random
import pandas as pd
from pydantic import BaseModel
from google import genai

# NOTE: Set your Gemini API key here or in Kaggle Secrets
# os.environ["GEMINI_API_KEY"] = "your_key"
try:
    client = genai.Client()
    print("Gemini initialized.")
except Exception as e:
    print("Gemini initialization failed:", e)
"""
nb.cells.append(new_code_cell(setup_code.strip()))

# Download Data
dl_code = """
import kagglehub
import shutil

# Download the Patient Records Dataset
def download_patient_records():
    print("Downloading patient-records dataset from Kaggle...")
    path = kagglehub.dataset_download("sergionefedov/patient-records-100k-patients-15-conditions")
    print("Downloaded to:", path)
    
    # In a notebook environment, the data is already in `path`
    return path

# In Kaggle, we might already have the dataset attached, but we'll download it to be safe.
DATA_PATH = download_patient_records()
"""
nb.cells.append(new_code_cell(dl_code.strip()))

# Data Processing
with open("src/data_processing.py", "r") as f:
    dp_code = f.read().replace("from .download_patient_data import download_patient_records", "")
nb.cells.append(new_markdown_cell("## Data Processing"))
nb.cells.append(new_code_cell(dp_code.strip()))

# Prompts
with open("src/agent_prompts.py", "r") as f:
    prompts_code = f.read()
nb.cells.append(new_markdown_cell("## Prompts"))
nb.cells.append(new_code_cell(prompts_code.strip()))

# Rules
with open("src/rules.py", "r") as f:
    rules_code = f.read()
nb.cells.append(new_markdown_cell("## Business Logic Rules"))
nb.cells.append(new_code_cell(rules_code.strip()))

# RAG & UMLS (Tools)
with open("src/rag.py", "r") as f:
    rag_code = f.read()
with open("src/umls.py", "r") as f:
    umls_code = f.read()

tools_code = rag_code + "\n\n" + umls_code + """

# Native Tools for Gemini
def search_icd10_tool(query: str, top_k: int = 5) -> str:
    \"\"\"Search the ICD-10-CM guidelines and tabular list for a given query.\"\"\"
    return json.dumps(search_icd10_rag(query, n_results=top_k), indent=2)

def normalize_medical_term_tool(term: str) -> str:
    \"\"\"Query the UMLS API to normalize medical jargon or symptoms.\"\"\"
    return json.dumps(query_umls(term), indent=2)

def validate_icd10_codes_tool(codes: list[str]) -> str:
    \"\"\"Validates a list of ICD-10-CM codes against Excludes1, Excludes2, and 7th character rules.\"\"\"
    return json.dumps(check_coding_rules(codes), indent=2)

GEMINI_TOOLS = [search_icd10_tool, normalize_medical_term_tool, validate_icd10_codes_tool]
"""
nb.cells.append(new_markdown_cell("## MCP Tools (Converted to Native Functions)"))
nb.cells.append(new_code_cell(tools_code.strip()))

# Evaluation
eval_code = """
# Data models for structured output
class Entity(BaseModel):
    entity_name: str
    entity_type: str
    text_span: str

class ExtractionResponse(BaseModel):
    entities: list[Entity]

class MissingCode(BaseModel):
    suggested_code: str
    justification_span: str
    guideline_rationale: str

class ReconciliationResponse(BaseModel):
    missing_codes: list[MissingCode]

def load_eval_data():
    diag_df = load_patient_diagnoses(os.path.join(DATA_PATH, 'diagnoses.csv'))
    raw_diag = pd.read_csv(os.path.join(DATA_PATH, 'diagnoses.csv'))
    merged_diag = raw_diag.merge(diag_df[['patient_id', 'visit_date', 'assigned_icd10_codes']], on=['patient_id', 'visit_date'])
    patients_df = pd.read_csv(os.path.join(DATA_PATH, 'patients.csv'))
    meds_df = pd.read_csv(os.path.join(DATA_PATH, 'medications.csv'))
    return merged_diag, patients_df, meds_df

def generate_synthetic_note(patient: pd.Series, diag_row: pd.Series, meds: pd.DataFrame) -> str:
    age = patient['age']
    sex = "male" if patient['sex'] == "M" else "female"
    smoking = patient['smoking_status']
    
    primary = str(diag_row['primary_diagnosis']).replace('_', ' ')
    secondary = str(diag_row['secondary_diagnoses']).replace('|', ', ').replace('_', ' ')
    if pd.isna(diag_row['secondary_diagnoses']) or not secondary or secondary.lower() == 'nan':
        secondary_str = "No secondary conditions reported."
    else:
        secondary_str = f"Secondary conditions include {secondary}."
        
    visit_type = diag_row['visit_type']
    
    meds_str = ""
    if not meds.empty:
        med_lines = []
        for _, m in meds.iterrows():
            med_lines.append(f"{m['medication']} {m['dose']} {m['unit']} {m['frequency']}")
        meds_str = "Patient is currently prescribed: " + ", ".join(med_lines) + "."
    
    note = f"A {age}-year-old {sex} {smoking} smoker presented for a {visit_type} visit. "
    note += f"Primary diagnosis: {primary}. {secondary_str} "
    if meds_str:
        note += f" {meds_str}"
        
    return note

def evaluate_pipeline(n_samples=2):
    merged_diag, patients_df, meds_df = load_eval_data()
    valid_encounters = merged_diag[merged_diag['assigned_icd10_codes'].apply(len) >= 2]
    sampled = valid_encounters.sample(n=n_samples, random_state=42)
    
    results = []
    
    for idx, diag_row in sampled.iterrows():
        pid = diag_row['patient_id']
        patient = patients_df[patients_df['patient_id'] == pid].iloc[0]
        meds = meds_df[meds_df['patient_id'] == pid]
        
        note = generate_synthetic_note(patient, diag_row, meds)
        true_codes = diag_row['assigned_icd10_codes']
        
        dropped_code = random.choice(true_codes)
        assigned_codes = [c for c in true_codes if c != dropped_code]
        
        print(f"\\n--- Evaluating Patient {pid} ---")
        print(f"Assigned (Provided to Agent): {assigned_codes}")
        print(f"Dropped (Target for Agent): {dropped_code}")
        
        # 1. Entity Extraction
        prompt = ENTITY_EXTRACTION_PROMPT.format(clinical_note=note)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ExtractionResponse,
                temperature=0.0
            )
        )
        extracted_entities = response.text
        
        # 2. Reconciliation with Tools
        recon_prompt = RECONCILIATION_PROMPT.format(
            extracted_entities=extracted_entities,
            assigned_codes=assigned_codes
        )
        recon_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=recon_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=GEMINI_TOOLS,
                response_mime_type="application/json",
                response_schema=ReconciliationResponse,
                temperature=0.0
            )
        )
        
        try:
            missing = json.loads(recon_response.text).get("missing_codes", [])
        except Exception:
            missing = []
            
        suggested_codes = [m["suggested_code"] for m in missing]
        found = dropped_code in suggested_codes
        print(f"Agent Suggested: {suggested_codes} | Success: {found}")
        
        results.append({
            "found": found,
            "suggested_codes": suggested_codes
        })
        time.sleep(4)
        
    # Metrics
    total = len(results)
    successes = sum([r["found"] for r in results])
    print(f"\\nEvaluation Complete! Recall: {successes}/{total} ({(successes/total)*100:.1f}%)")
    
    return results

# results = evaluate_pipeline(2)
"""
nb.cells.append(new_markdown_cell("## Evaluation Pipeline"))
nb.cells.append(new_code_cell(eval_code.strip()))

with open("kaggle_notebook.ipynb", "w") as f:
    nbformat.write(nb, f)

print("kaggle_notebook.ipynb generated successfully!")
