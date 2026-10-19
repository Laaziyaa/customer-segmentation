import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { LineCurveChart } from "../components/Charts";
import { CardSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";

export const EvaluationPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["modelEvaluation"],
    queryFn: api.getEvaluation,
  });

  if (isLoading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Model quality</h1>
          <p className="page-desc">Clustering quality metrics and validation curves...</p>
        </div>
        <div className="metrics-grid">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Model quality</h1>
        </div>
        <StatusNotice
          type="error"
          title="Could not load evaluation metrics"
          message="Failed to compute or load clustering evaluation data. Please retry."
          actionText="Retry"
          onAction={() => refetch()}
        />
      </div>
    );
  }

  const {
    silhouette,
    davies_bouldin,
    calinski_harabasz,
    optimal_k,
    stability_score,
    elbow_curve,
    silhouette_curve,
    metrics_explanation,
  } = data;

  // Format data for LineCurveChart
  const elbowPoints = elbow_curve.map((p) => ({ k: p.k, value: p.inertia ?? 0 }));
  const silhouettePoints = silhouette_curve.map((p) => ({ k: p.k, value: p.score ?? 0 }));

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Model quality</h1>
        <p className="page-desc">
          Mathematical validation of the customer clustering model. Evaluates cluster separation, density, and stability across initializations.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="metrics-grid">
        <div className="kpi-card">
          <div className="kpi-label">Silhouette Score</div>
          <div className="kpi-val">{silhouette.toFixed(3)}</div>
          <div className="kpi-sub" style={{ fontSize: "11.5px", lineHeight: 1.35, marginTop: "6px" }}>
            {metrics_explanation?.silhouette || "Measures cluster cohesion and separation (-1 to 1; higher is better)."}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Davies-Bouldin Index</div>
          <div className="kpi-val">{davies_bouldin.toFixed(3)}</div>
          <div className="kpi-sub" style={{ fontSize: "11.5px", lineHeight: 1.35, marginTop: "6px" }}>
            {metrics_explanation?.davies_bouldin || "Evaluates ratio of within-cluster spread to separation (lower is better)."}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Calinski-Harabasz</div>
          <div className="kpi-val">{Math.round(calinski_harabasz).toLocaleString()}</div>
          <div className="kpi-sub" style={{ fontSize: "11.5px", lineHeight: 1.35, marginTop: "6px" }}>
            {metrics_explanation?.calinski_harabasz || "Variance ratio criterion (higher values mean denser, distinct clusters)."}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Cluster Stability Score</div>
          <div className="kpi-val">{(stability_score * 100).toFixed(0)}%</div>
          <div className="kpi-sub" style={{ fontSize: "11.5px", lineHeight: 1.35, marginTop: "6px" }}>
            {metrics_explanation?.stability || "Measured via Adjusted Rand Index across different random seeds (reproducibility)."}
          </div>
        </div>
      </div>

      {/* Evaluation Curves */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(460px, 1fr))", gap: "20px" }}>
        {/* Elbow Curve */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Elbow Method (Inertia Curve)</h2>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                Identifies point of diminishing returns where inertia decline flattens.
              </div>
            </div>
          </div>
          <LineCurveChart data={elbowPoints} yLabel="Inertia" recommendedK={optimal_k} />
        </div>

        {/* Silhouette Curve */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Silhouette Analysis across K</h2>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                Compares average silhouette coefficient for candidate cluster counts.
              </div>
            </div>
          </div>
          <LineCurveChart data={silhouettePoints} yLabel="Silhouette" recommendedK={optimal_k} />
        </div>
      </div>
    </div>
  );
};
