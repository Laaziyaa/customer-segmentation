from pathlib import Path
import pandas as pd

class DataLoader:

    def load_dataset(self, dataset_path):

        dataset_path = Path(dataset_path)

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        df = pd.read_csv(dataset_path, sep=";")

        print(f"Dataset loaded successfully from:\n{dataset_path}")
        print(f"Shape: {df.shape}")

        return df