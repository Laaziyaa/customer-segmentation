from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


class ClusterEvaluator:

    def __init__(self):

        self.output_dir = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "outputs"
            / "plots"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def evaluate(self, X):

        inertias = []
        silhouette_scores = []

        k_values = range(2, 11)

        print("=" * 60)
        print("CLUSTER EVALUATION")
        print("=" * 60)

        for k in k_values:

            model = KMeans(
                n_clusters=k,
                random_state=42,
                n_init=20
            )

            labels = model.fit_predict(X)

            inertia = model.inertia_

            score = silhouette_score(X, labels)

            inertias.append(inertia)
            silhouette_scores.append(score)

            print(
                f"K = {k:<2} "
                f"Inertia = {inertia:.2f} "
                f"Silhouette = {score:.4f}"
            )

        self.plot_elbow(k_values, inertias)

        self.plot_silhouette(k_values, silhouette_scores)

        best_index = silhouette_scores.index(max(silhouette_scores))

        best_k = list(k_values)[best_index]

        print("\nRecommended K =", best_k)

        return best_k

    def plot_elbow(self, k_values, inertias):

        plt.figure(figsize=(8,5))

        plt.plot(
            k_values,
            inertias,
            marker="o"
        )

        plt.title("Elbow Method")
        plt.xlabel("Number of Clusters (K)")
        plt.ylabel("Inertia")

        plt.grid(True)

        plt.savefig(
            self.output_dir / "elbow_method.png",
            dpi=300
        )

        plt.close()

    def plot_silhouette(self, k_values, scores):

        plt.figure(figsize=(8,5))

        plt.plot(
            k_values,
            scores,
            marker="o"
        )

        plt.title("Silhouette Scores")
        plt.xlabel("Number of Clusters (K)")
        plt.ylabel("Silhouette Score")

        plt.grid(True)

        plt.savefig(
            self.output_dir / "silhouette_scores.png",
            dpi=300
        )

        plt.close()