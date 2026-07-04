================================================================================
MEDICAL CODING ASSIST AGENT
================================================================================

[ OVERVIEW ]
--------------------------------------------------------------------------------
This project supports the development of a notebook designed for submission to 
the Kaggle 5-Day Agent AI Development Capstone Project. 

The agent is designed to assist with ICD-10 code capture at institutions that 
either lack sufficient coding resources or are focused on coding for specific 
specialties (e.g., orthopaedic surgery vs. the 360-degree view a primary care 
provider might have). By analyzing clinical notes and cross-referencing them 
against current coding rules, the agent identifies missing codes and highlights 
coding gaps.

[ PROJECT ARCHITECTURE ]
--------------------------------------------------------------------------------
The notebook implements an agent architecture that leverages gemini-2.5-flash 
to extract medical entities and autonomously query its skills (ICD-10 databases 
and rule checkers) to reconcile and validate its output.

```text
+-------------------+        +-----------------------+        +----------------------+
|  Clinical Note    | -----> | 1. Entity Extraction  | -----> |  Extracted Entities  |
+-------------------+        |   (gemini-2.5-flash)  |        | (Diagnoses, Symptoms)|
                             +-----------------------+        +----------------------+
                                                                         |
+-------------------+                                                    v
| Already Coded     |        +-----------------------+        +----------------------+
| ICD-10 List       | -----> | 2. Agent Reconciler   | -----> |  Final Output        |
+-------------------+        |   (gemini-2.5-flash)  |        | (Missing Code Gaps)  |
                             +-----------------------+        +----------------------+
                                |        |        |
                                v        v        v
                         +--------+ +--------+ +-------------+
                         | ICD-10 | | UMLS   | | ICD-10 Rule |
                         | Vector | | Mock   | | Checker     |
                         | DB     | | API    | |             |
                         +--------+ +--------+ +-------------+
                                     SKILLS / TOOLS
```
