import sys
import os

# Add src to Python path so we can import it
sys.path.insert(0, os.path.abspath("."))

from src.mcp_server import mcp
from src.umls import query_umls
from src.rules import check_coding_rules

def test_umls_placeholder():
    """Test the placeholder logic for UMLS API."""
    res = query_umls("heart attack")
    assert res["concept_id"] == "C0027051"
    
    res2 = query_umls("unknown random thing")
    assert res2["concept_id"] == "UNKNOWN"

def test_rules_excludes1():
    """Test the Excludes1 rule checking logic."""
    res = check_coding_rules(["J00", "J01.90"])
    assert not res[0]["valid"]
    assert res[0]["rule_type"] == "Excludes1"
    
    res2 = check_coding_rules(["E10.9", "I10"])
    assert res2[0]["valid"]

def test_rules_7th_character():
    """Test the 7th character validation."""
    res = check_coding_rules(["S82.101"])
    assert not res[0]["valid"]
    assert res[0]["rule_type"] == "7th_character_required"
    
import asyncio

async def test_mcp_tools_exist():
    """Test that all tools are registered on the FastMCP server."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "search_icd10" in tool_names
    assert "normalize_medical_term" in tool_names
    assert "validate_icd10_codes" in tool_names
    assert "read_clinical_note" in tool_names

if __name__ == "__main__":
    print("Running basic tool verification tests...")
    test_umls_placeholder()
    test_rules_excludes1()
    test_rules_7th_character()
    asyncio.run(test_mcp_tools_exist())
    print("All tests passed!")
