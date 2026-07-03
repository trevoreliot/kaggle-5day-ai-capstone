import kagglehub
import os
import shutil

def download_patient_records():
    """
    Downloads the Patient Records dataset from Kaggle using kagglehub
    and places it into the 'synth_phi' directory in the repository root.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    target_dir = os.path.join(base_dir, 'synth_phi')
    
    if os.path.exists(target_dir) and os.listdir(target_dir):
        print(f"Dataset already exists at: {target_dir}")
        return target_dir
        
    print("Downloading 'sergionefedov/patient-records-100k-patients-15-conditions'...")
    
    # Download dataset - this caches locally
    cached_path = kagglehub.dataset_download("sergionefedov/patient-records-100k-patients-15-conditions")
    
    print(f"Dataset cached at: {cached_path}")
    print(f"Copying files to {target_dir}...")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    for item in os.listdir(cached_path):
        s = os.path.join(cached_path, item)
        d = os.path.join(target_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
            
    print(f"Dataset successfully downloaded and copied to: {target_dir}")
    
    files = os.listdir(target_dir)
    print(f"Contains {len(files)} items at the root level.")
    
    return target_dir

if __name__ == "__main__":
    download_patient_records()
