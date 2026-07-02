================================================================================
GEMINI DEVELOPER CONTEXT & INSTRUCTIONS: MEDICAL CODING ASSIST AGENT
================================================================================

[ PROJECT OVERVIEW ]
--------------------------------------------------------------------------------
The objective is to build an AI agent for the Kaggle 5-Day AI Agent Capstone. 
The agent will act as a Medical Coder and Auditor. It will ingest synthetic 
clinical notes and assigned ICD-10-CM codes, and then analyze the record for 
potential coding gaps (missing codes that should have been added where appropriate).

The agent will leverage the "Patient Records 100K patients, 15 conditions" dataset, 
which contains demographics, lab results, medications, and ICD-10 diagnosis codes [1, 2]. 
It will cross-reference this clinical data with the ICD-10-CM Alphabetic Index [3], 
the Tabular List [4], and the Official Guidelines for Coding and Reporting [5, 6].

[ CORE DEVELOPMENT RULES & STANDARDS ]
--------------------------------------------------------------------------------
* Python Formatting: All Python code must strictly adhere to PEP 8 standards. 
  Ensure clean readability, proper spacing, and informative docstrings.
* Credential Management: ABSOLUTELY NO `.env` files or hardcoded API keys. 
  Since this is a Kaggle environment, all secrets (e.g., UMLS API keys, LLM keys) 
  must be stored and accessed exclusively via `kaggle_secrets.KaggleSecrets`.
* Kaggle Optimization: Kaggle environments are ephemeral and have strict RAM/disk 
  limits. 
  - Prefer lightweight, in-memory, or embedded databases like ChromaDB
    for RAG tools rather than persistent servers.
  - Chunk and parse the fixed-width and XML ICD-10 files efficiently using 
    Pandas and native Python XML libraries to avoid memory overflow.
* Output Formatting: Refrain from using emojis in any output, documentation, 
  or markdown. Use ASCII-style or org-mode decorators (e.g., [*], ===, ---).

[ MODEL CONTEXT PROTOCOL (MCP) ARCHITECTURE ]
--------------------------------------------------------------------------------
The agent will be augmented with the following tools to parse complex medical logic:
1. Vector Database / RAG Tool: Uses ChromaDB or FAISS to semantically search 
   the ICD-10-CM Alphabetic Index and Tabular List.
2. UMLS / SNOMED CT API Tool: Normalizes medical jargon and abbreviations 
   from the clinical notes to map symptoms and definitive diagnoses correctly.
3. Rule-Checker Tool: A programmatic function to validate ICD-10 conventions, 
   specifically enforcing:
   - Excludes1 notes ("NOT CODED HERE!", indicating mutually exclusive codes) [4, 7].
   - Excludes2 notes ("Not included here", indicating conditions that can co-occur) [4, 8].
   - Etiology/Manifestation pairings ("Code First" / "Use Additional Code") [4, 8].

[ PROJECT MILESTONES : todo.org ]
--------------------------------------------------------------------------------
* Kaggle 5-Day AI Agent Capstone: Medical Coding Assist
** Day 1: Project Setup & Data Acquisition
   - [X] Set up Python virtual environment and Kaggle notebook.
   - [X] Download the synthetic EHR Patient Records dataset (100K patients, 15 conditions) [1].
   - [X] Parse the ICD-10-CM Tabular List to extract hierarchies and instructional notes [4].
   - [X] Gather Alphabetic Index and Official Guidelines [3, 5].
** Day 2: Tooling & MCP Setup
   - [ ] Set up an MCP server to handle secure local file reads.
   - [ ] Develop ChromaDB RAG MCP Tool for semantic ICD-10 manual searches.
   - [ ] Develop UMLS/SNOMED CT API MCP Tool for clinical text normalization.
   - [ ] Develop Rule-Checker MCP Tool to enforce Excludes1/Excludes2 and etiology sequencing [4, 7, 8].
** Day 3: Agent Architecture & Prompt Engineering
   - [ ] Design the system prompt for the Medical Coder/Auditor persona.
   - [ ] Implement "Entity Extraction" (extracting diagnoses, symptoms, labs).
   - [ ] Implement "Reconciliation" (comparing extracted entities against coded lists).
** Day 4: Implementing ICD-10-CM Business Logic
   - [ ] Program agent to validate "Code First" / "Use Additional Code" violations [4].
   - [ ] Ensure agent handles 7th-character extensions and placeholder 'X' requirements [9, 10].
   - [ ] Enforce guidelines differentiating definitive diagnoses from integral symptoms [11].
** Day 5: Evaluation, Refinement & Submission
   - [ ] Run the agent on a validation set of clinical notes.
   - [ ] Evaluate precision and recall of the gap analysis.
   - [ ] Format final output to highlight: Missing code, clinical text justification, and guideline citation.
   - [ ] Finalize Kaggle notebook, scrub any test credentials, and submit.
================================================================================
