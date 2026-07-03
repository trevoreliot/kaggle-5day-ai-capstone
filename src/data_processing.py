import pandas as pd

def load_patient_diagnoses(csv_path: str) -> pd.DataFrame:
    """
    Loads the diagnoses.csv file and processes the ICD-10 codes.
    
    The 'secondary_icd10s' column contains a pipe-delimited list of codes.
    This function parses the primary and secondary codes into a single list
    of all assigned codes per encounter/row.
    """
    df = pd.read_csv(csv_path)
    
    # Fill NaN values with empty strings for easier string manipulation
    df['primary_icd10'] = df['primary_icd10'].fillna('')
    df['secondary_icd10s'] = df['secondary_icd10s'].fillna('')
    
    def parse_codes(row):
        codes = []
        
        # 1. Add primary code
        primary = str(row['primary_icd10']).strip()
        if primary:
            codes.append(primary)
            
        # 2. Add secondary codes (split by pipe)
        secondary_str = str(row['secondary_icd10s']).strip()
        if secondary_str:
            # Split and clean the codes
            secondary = [c.strip() for c in secondary_str.split('|') if c.strip()]
            codes.extend(secondary)
            
        return codes

    # Apply the parsing function row by row
    df['assigned_icd10_codes'] = df.apply(parse_codes, axis=1)
    
    # We mainly care about patient_id, visit_date, and our parsed list of codes
    # Returning a subset of columns keeps memory usage low
    return df[['patient_id', 'visit_date', 'assigned_icd10_codes']]

if __name__ == "__main__":
    # Test the parsing logic
    import os
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(base_dir, 'synth_phi', 'diagnoses.csv')
    
    if os.path.exists(path):
        parsed_df = load_patient_diagnoses(path)
        print("Successfully parsed diagnoses.csv!")
        print(f"Total encounters loaded: {len(parsed_df)}")
        print("\nFirst 5 rows:")
        print(parsed_df.head())
    else:
        print(f"Dataset not found at {path}")
