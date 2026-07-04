import os
import sys
import json
import re
from lxml import etree

def extract_codes(note_text):
    codes = []
    # Match patterns like (A05.-) or (A18.32) or (E10-E14)
    # This regex finds ICD-10 code blocks bounded by non-word chars
    matches = re.findall(r'(?<!\w)[A-Z][0-9][A-Z0-9](?:\.[A-Z0-9]+)?\-*(?!\w)', note_text)
    for match in matches:
        codes.append(match.rstrip('-').rstrip('.'))
    return codes

def ingest():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    xsd_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'icd10cm-tabular.xsd')
    xml_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'icd10cm-tabular_-2027.xml')

    print(f"Loading XSD from {xsd_path}...")
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
    schema = etree.XMLSchema(schema_root)

    print(f"Loading and validating XML from {xml_path}...")
    xml_parser = etree.XMLParser(schema=schema)
    with open(xml_path, 'rb') as f:
        tree = etree.parse(f, xml_parser)
    print("XML parsed and validated successfully.")

    rules = {}
    
    def add_rules(key, ex_type, notes):
        if key not in rules:
            rules[key] = {"excludes1": [], "excludes2": [], "codeFirst": [], "useAdditionalCode": [], "requires_7th_char": False}
        
        for note in notes:
            text = "".join(note.itertext()).strip()
            codes = extract_codes(text)
            rules[key][ex_type].extend(codes)

    root = tree.getroot()
    
    # Process Excludes, Code First, Use Additional Code
    for ex_type in ["excludes1", "excludes2", "codeFirst", "useAdditionalCode"]:
        for el in root.findall(f".//{ex_type}"):
            parent = el.getparent()
            notes = el.findall("note")
            
            key = None
            if parent.tag == "diag":
                key = parent.find("name").text
            elif parent.tag == "section":
                key = parent.get("id")
            elif parent.tag == "chapter":
                key_node = parent.find("name")
                if key_node is not None:
                    key = f"Chapter_{key_node.text}"
                
            if key:
                add_rules(key, ex_type, notes)
                
    # Process 7th character requirements
    # sevenChrDef is often under a chapter, section, or diag.
    for el in root.findall(f".//sevenChrDef"):
        parent = el.getparent()
        key = None
        if parent.tag == "diag":
            key = parent.find("name").text
        elif parent.tag == "section":
            key = parent.get("id")
        elif parent.tag == "chapter":
            key_node = parent.find("name")
            if key_node is not None:
                key = f"Chapter_{key_node.text}"
                
        if key:
            if key not in rules:
                rules[key] = {"excludes1": [], "excludes2": [], "codeFirst": [], "useAdditionalCode": [], "requires_7th_char": False}
            rules[key]["requires_7th_char"] = True

    # Clean up empty lists
    final_rules = {}
    for k, v in rules.items():
        v["excludes1"] = list(set(v["excludes1"]))
        v["excludes2"] = list(set(v["excludes2"]))
        v["codeFirst"] = list(set(v["codeFirst"]))
        v["useAdditionalCode"] = list(set(v["useAdditionalCode"]))
        
        if v["excludes1"] or v["excludes2"] or v["codeFirst"] or v["useAdditionalCode"] or v["requires_7th_char"]:
            final_rules[k] = v

    out_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'rules.json')
    with open(out_path, 'w') as f:
        json.dump(final_rules, f, indent=2)
    print(f"Extracted rules for {len(final_rules)} entities to {out_path}")

if __name__ == "__main__":
    ingest()
