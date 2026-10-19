from pathlib import Path

import pandas as pd

from .trainer import ClusterTrainer
from .preprocessor import DataPreprocessor
from .evaluator import ClusterEvaluator
from .profiler import ClusterProfiler
from .personas import PersonaGenerator
from .recommendation import RecommendationEngine


def run_segmentation_pipeline(processed_df):
    """
    Runs the complete customer segmentation pipeline.

    Parameters:
        processed_df (pd.DataFrame): Enhanced dataset from the data engineering pipeline.

    Returns:
        dict: Contains clustered dataset, summary, personas and recommendations.
    """

    print("=" * 60)
    print("CUSTOMER SEGMENTATION PIPELINE")
    print("=" * 60)

    project_root = Path(__file__).resolve().parents[2]

    df = processed_df.copy()

    print(f"\nDataset Shape : {df.shape}")

    print("\n[1] Preprocessing dataset...")

    preprocessor = DataPreprocessor(df)

    X_processed, transformer = preprocessor.preprocess()

    print("Preprocessing completed successfully.")
    print(f"Processed Shape : {X_processed.shape}")

    print("\n[2] Evaluating optimal number of clusters...")

    evaluator = ClusterEvaluator()

    recommended_k = evaluator.evaluate(X_processed)

    # Business decision for better customer segmentation
    final_k = 4

    print("\n" + "=" * 60)
    print(f"Recommended K (Silhouette): {recommended_k}")
    print(f"Final K Used: {final_k}")
    print("=" * 60)

    trainer = ClusterTrainer(n_clusters=final_k)

    trainer.save_preprocessor(transformer)

    model, labels = trainer.train(X_processed)

    from app.config import PROCESSED_DATA_DIR
    output_path = PROCESSED_DATA_DIR / "clustered_customers.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"\nClustered dataset saved to:\n{output_path}")

    print("\n[3] Profiling customer clusters...")

    profiler = ClusterProfiler()

    summary = profiler.profile(df)

    print("\n[4] Generating customer personas...")

    persona_generator = PersonaGenerator()

    persona_df = persona_generator.generate(summary)

    print("\n[5] Generating recommendations...")

    recommendation_engine = RecommendationEngine()

    recommendation_df = recommendation_engine.generate(persona_df)

    print("\nSegmentation pipeline completed successfully.")
    print("=" * 60)

    return {
        "clustered_df": df,
        "summary_df": summary,
        "persona_df": persona_df,
        "recommendation_df": recommendation_df,
        "model": model,
        "transformer": transformer,
    }


def main():
    from app.config import PROCESSED_DATA_DIR
    dataset_path = PROCESSED_DATA_DIR / "enhanced_bank_dataset.csv"

    print("\nLoading processed dataset...")

    df = pd.read_csv(dataset_path)

    run_segmentation_pipeline(df)


if __name__ == "__main__":
    main()