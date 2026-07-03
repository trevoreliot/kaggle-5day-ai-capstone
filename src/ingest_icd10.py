import os
import sys
from lxml import etree

# Ensure src is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.rag import add_icd10_documents, get_icd10_collection

def get_text(element):
    if element is None:
        return ""
    # extract all text recursively from the element (e.g. for nemod tags inside title)
    return "".join(element.itertext()).strip()

def ingest_data():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    xsd_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'icd10cm-index.xsd')
    xml_path = os.path.join(base_dir, 'assets', 'ICD10_Assets', 'icd10cm-index-2027.xml')

    print(f"Loading XSD from {xsd_path}...")
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
    schema = etree.XMLSchema(schema_root)

    print(f"Loading and validating XML from {xml_path}...")
    # Validate while parsing
    xml_parser = etree.XMLParser(schema=schema)
    try:
        with open(xml_path, 'rb') as f:
            xml_tree = etree.parse(f, xml_parser)
        print("XML validation successful.")
    except etree.XMLSyntaxError as e:
        print(f"XML validation failed: {e}")
        return

    documents = []
    metadatas = []
    ids = []

    def process_term(term_element, path_strings):
        title_elem = term_element.find("title")
        title_str = get_text(title_elem)
        current_path = path_strings + [title_str]
        
        code_elem = term_element.find("code")
        if code_elem is not None:
            code_str = get_text(code_elem)
            doc_str = " -> ".join(current_path)
            documents.append(doc_str)
            metadatas.append({"code": code_str})
            ids.append(f"term_{len(ids)}")
            
        for sub_term in term_element.findall("term"):
            process_term(sub_term, current_path)

    root = xml_tree.getroot()
    print("Parsing XML terms...")
    for letter in root.findall("letter"):
        for main_term in letter.findall("mainTerm"):
            process_term(main_term, [])
            
    print(f"Extracted {len(documents)} terms with codes.")
    
    if not documents:
        print("No documents found to ingest.")
        return

    print("Checking existing database...")
    collection = get_icd10_collection()
    if collection.count() > 0:
        print(f"Collection already contains {collection.count()} documents. Skipping ingestion.")
        return

    print("Ingesting into ChromaDB in batches...")
    batch_size = 5000
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        print(f"Ingesting batch {i} to {end_idx}...")
        add_icd10_documents(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
