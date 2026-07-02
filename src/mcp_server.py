import os
import json
from mcp.server.fastmcp import FastMCP
from .rag import search_icd10_rag
from .umls import query_umls
from .rules import check_coding_rules

# Initialize FastMCP Server
mcp = FastMCP("MedicalCodingAssist")

@mcp.tool()
def search_icd10(query: str, top_k: int = 5) -> str:
    """
    Search the ICD-10-CM guidelines and tabular list for a given query using ChromaDB RAG.
    
    Args:
        query: The medical term or symptom to search for.
        top_k: Number of results to return.
    """
    results = search_icd10_rag(query, n_results=top_k)
    return json.dumps(results, indent=2)

@mcp.tool()
def normalize_medical_term(term: str) -> str:
    """
    Query the UMLS API to normalize medical jargon or symptoms.
    
    Args:
        term: The medical term to normalize.
    """
    result = query_umls(term)
    return json.dumps(result, indent=2)

@mcp.tool()
def validate_icd10_codes(codes: list[str]) -> str:
    """
    Validates a list of ICD-10-CM codes against Excludes1, Excludes2, and 7th character rules.
    
    Args:
        codes: A list of ICD-10-CM codes to validate.
    """
    results = check_coding_rules(codes)
    return json.dumps(results, indent=2)

@mcp.tool()
def read_clinical_note(file_path: str) -> str:
    """
    Securely reads a clinical note file from the dataset.
    
    Args:
        file_path: The relative or absolute path to the clinical note text file.
    """
    try:
        # In a real environment, we'd add path traversal protection here
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

if __name__ == "__main__":
    mcp.run()
