from pathlib import Path
import joblib
from sklearn.cluster import KMeans


class ClusterTrainer:

    def __init__(self, n_clusters=4):

        self.n_clusters = n_clusters

        self.project_root = Path(__file__).resolve().parents[2]

        self.model_dir = (
            self.project_root
            / "data"
            / "models"
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def train(self, X):

        print("=" * 60)
        print("TRAINING K-MEANS MODEL")
        print("=" * 60)

        model = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=20
        )

        labels = model.fit_predict(X)

        print("Training completed successfully.")
        print(f"Clusters Created : {self.n_clusters}")

        joblib.dump(
            model,
            self.model_dir / "kmeans_model.pkl"
        )

        print("Model saved successfully.")

        return model, labels

    def save_preprocessor(self, preprocessor):

        joblib.dump(
            preprocessor,
            self.model_dir / "preprocessor.pkl"
        )

        print("Preprocessor saved successfully.")