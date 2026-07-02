import chromadb
import os

# We will store the vector database in a local directory.
# In Kaggle, this will be inside /kaggle/working/
DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")

def get_chroma_client():
    """Initializes and returns the ChromaDB client."""
    return chromadb.PersistentClient(path=DB_DIR)

def get_icd10_collection():
    """Retrieves or creates the ICD-10 collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(name="icd10_index")

def search_icd10_rag(query: str, n_results: int = 5) -> list[dict]:
    """
    Search the ICD-10-CM guidelines and tabular list for a given query.
    
    Args:
        query: The medical term or symptom to search for.
        n_results: Number of results to return.
        
    Returns:
        List of matching ICD-10 codes and descriptions.
    """
    collection = get_icd10_collection()
    
    # In a real scenario with populated data, we query the collection.
    # We use a try-except to handle cases where the collection is empty gracefully.
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results into a list of dicts
        formatted_results = []
        if results and "documents" in results and results["documents"]:
            for i in range(len(results["documents"][0])):
                doc = results["documents"][0][i]
                meta = results["metadatas"][0][i] if "metadatas" in results and results["metadatas"] else {}
                formatted_results.append({
                    "code": meta.get("code", "UNKNOWN"),
                    "description": doc,
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return formatted_results
    except Exception as e:
        return [{"error": str(e), "message": "Failed to query ChromaDB or collection is empty."}]

def add_icd10_documents(documents: list[str], metadatas: list[dict], ids: list[str]):
    """
    Helper function to populate the ChromaDB vector store.
    """
    collection = get_icd10_collection()
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
