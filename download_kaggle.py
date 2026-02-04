import kaggle
import os

def download_data_via_python():
    print("Iniciando download via Python API...")
    dataset = "olistbr/brazilian-ecommerce"
    target_path = "data"
    
    # Authenticate (uses ~/.kaggle/kaggle.json automatically)
    kaggle.api.authenticate()
    
    # Download and Unzip
    print(f"Baixando {dataset} para {target_path}...")
    kaggle.api.dataset_download_files(dataset, path=target_path, unzip=True)
    print("Download concluído!")

if __name__ == "__main__":
    download_data_via_python()
