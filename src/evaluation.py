import os
import random
import time
import json
import pandas as pd
from google import genai
from pydantic import BaseModel
from src.agent_prompts import SYSTEM_PROMPT, ENTITY_EXTRACTION_PROMPT, RECONCILIATION_PROMPT
from src.data_processing import load_patient_diagnoses
from src.pipeline import check_needs_reconciliation
from src.rules import check_coding_rules
from src.rag import search_icd10_rag
from src.umls import query_umls

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

# Native Tools for Gemini
def search_icd10_tool(query: str, top_k: int = 5) -> str:
    """Search the ICD-10-CM guidelines and tabular list for a given query."""
    return json.dumps(search_icd10_rag(query, n_results=top_k), indent=2)

def normalize_medical_term_tool(term: str) -> str:
    """Query the UMLS API to normalize medical jargon or symptoms."""
    return json.dumps(query_umls(term), indent=2)

def validate_icd10_codes_tool(codes: list[str]) -> str:
    """Validates a list of ICD-10-CM codes against Excludes1, Excludes2, and 7th character rules."""
    return json.dumps(check_coding_rules(codes), indent=2)

GEMINI_TOOLS = [search_icd10_tool, normalize_medical_term_tool, validate_icd10_codes_tool]

class MedicalCodingAgent:
    def __init__(self, client):
        self.client = client
        
    def analyze_note(self, note: str, assigned_codes: list[str]) -> list[dict]:
        # 1. Entity Extraction
        prompt = ENTITY_EXTRACTION_PROMPT.format(clinical_note=note)
        
        config = genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExtractionResponse,
            temperature=0.0
        )
        
        try:
            extraction_response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
        except Exception as e:
            if '429' in str(e) or 'quota' in str(e).lower():
                print("gemini-2.5-flash limit reached for extraction. Falling back to gemini-1.5-flash...")
                extraction_response = self.client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=config
                )
            else:
                raise e
                
        extracted_entities = extraction_response.text
        
        # 2. Reconciliation with Tools
        recon_prompt = RECONCILIATION_PROMPT.format(
            extracted_entities=extracted_entities,
            assigned_codes=assigned_codes
        )
        
        chat_config = genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=GEMINI_TOOLS,
            response_mime_type="application/json",
            response_schema=ReconciliationResponse,
            temperature=0.0
        )
        
        # Use Chats API with Tools to enable the Agent Skill
        chat = self.client.chats.create(
            model='gemini-2.5-flash',
            config=chat_config
        )
        
        try:
            recon_response = chat.send_message(recon_prompt)
        except Exception as e:
            if '429' in str(e) or 'quota' in str(e).lower():
                print("gemini-2.5-flash limit reached for reconciliation. Falling back to gemini-1.5-flash...")
                chat = self.client.chats.create(
                    model='gemini-1.5-flash',
                    config=chat_config
                )
                recon_response = chat.send_message(recon_prompt)
            else:
                raise e
        
        try:
            missing = json.loads(recon_response.text).get("missing_codes", [])
        except Exception:
            missing = []
            
        return missing

def load_data():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    synth_dir = os.path.join(base_dir, 'synth_phi')
    
    diag_df = load_patient_diagnoses(os.path.join(synth_dir, 'diagnoses.csv'))
    raw_diag = pd.read_csv(os.path.join(synth_dir, 'diagnoses.csv'))
    
    # Merge the parsed codes back into raw_diag for ease of access
    merged_diag = raw_diag.merge(diag_df[['patient_id', 'visit_date', 'assigned_icd10_codes']], on=['patient_id', 'visit_date'])
    
    patients_df = pd.read_csv(os.path.join(synth_dir, 'patients.csv'))
    meds_df = pd.read_csv(os.path.join(synth_dir, 'medications.csv'))
    
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

def evaluate_pipeline(n_samples=5):
    merged_diag, patients_df, meds_df = load_data()
    
    # Filter for rows that have at least 2 codes so we can safely drop 1
    valid_encounters = merged_diag[merged_diag['assigned_icd10_codes'].apply(len) >= 2]
    sampled = valid_encounters.sample(n=n_samples, random_state=42)
    
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Failed to initialize Gemini Client. Make sure GEMINI_API_KEY is set. Error: {e}")
        return

    results = []
    
    # Initialize the Agent
    agent = MedicalCodingAgent(client)
    
    for idx, diag_row in sampled.iterrows():
        pid = diag_row['patient_id']
        patient = patients_df[patients_df['patient_id'] == pid].iloc[0]
        meds = meds_df[meds_df['patient_id'] == pid]
        
        note = generate_synthetic_note(patient, diag_row, meds)
        true_codes = diag_row['assigned_icd10_codes']
        
        # Simulate Gap: Drop one code randomly
        dropped_code = random.choice(true_codes)
        assigned_codes = [c for c in true_codes if c != dropped_code]
        
        print(f"--- Evaluating Patient {pid} ---")
        print(f"Note: {note}")
        print(f"True Codes: {true_codes}")
        print(f"Assigned (Provided to Agent): {assigned_codes}")
        print(f"Dropped (Target for Agent): {dropped_code}")
        
        missing_codes = agent.analyze_note(note, assigned_codes)
        
        suggested_codes = [m.get("suggested_code", "") if isinstance(m, dict) else m.suggested_code for m in missing_codes]
        
        print(f"Agent Suggested Missing Codes: {suggested_codes}")
        
        # Score
        found = dropped_code in suggested_codes
        print(f"Success: {found}\n")
        
        results.append({
            "patient_id": pid,
            "note": note,
            "true_codes": true_codes,
            "assigned_codes": assigned_codes,
            "dropped_code": dropped_code,
            "suggested_codes": suggested_codes,
            "found": found,
            "raw_missing": missing_codes
        })
        time.sleep(4)
        
    # Calculate metrics
    total = len(results)
    successes = sum([r["found"] for r in results])
    print(f"=============================")
    print(f"Evaluation Complete!")
    print(f"Recall (Found dropped code): {successes}/{total} ({(successes/total)*100:.1f}%)")
    
    total_suggested = sum([len(r["suggested_codes"]) for r in results])
    if total_suggested > 0:
        precision = successes / total_suggested
        print(f"Precision (Dropped code was suggested / Total suggestions): {successes}/{total_suggested} ({precision*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    evaluate_pipeline(2)
