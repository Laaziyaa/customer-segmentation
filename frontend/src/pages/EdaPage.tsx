import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Database, Grid, AlertCircle } from "lucide-react";
import { api } from "../api/client";
import { HistogramChart } from "../components/Charts";
import { CardSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";
import type { EDADistributionResponse, EDAMissingResponse, EDACorrelationResponse } from "../api/types";

export const EdaPage: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<"distributions" | "missing" | "correlations">("distributions");
  const [selectedColumn, setSelectedColumn] = useState<string>("annual_income");
  const [selectedCluster, setSelectedCluster] = useState<string>("");

  // Get schema to dynamically populate column dropdown
  const { data: schema } = useQuery({
    queryKey: ["datasetSchema"],
    queryFn: api.getSchema,
  });

  // Query EDA data at request time
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["eda", selectedMetric, selectedColumn, selectedCluster],
    queryFn: () =>
      api.getEDA(
        selectedMetric,
        selectedMetric === "distributions" ? selectedColumn : undefined,
        selectedCluster ? Number(selectedCluster) : undefined
      ),
  });

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Data insights</h1>
        <p className="page-desc">
          Exploratory analysis computed directly from the active customer dataset at request time.
        </p>
      </div>

      {/* Control bar */}
      <div className="card" style={{ marginBottom: "20px", padding: "16px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center" }}>
          {/* Metric Selector */}
          <div>
            <label className="form-label" style={{ marginBottom: "4px" }}>
              Insight Type
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as any)}
              className="form-select"
              style={{ minWidth: "170px" }}
            >
              <option value="distributions">Feature Distribution</option>
              <option value="missing">Missing Values</option>
              <option value="correlations">Correlation Matrix</option>
            </select>
          </div>

          {/* Column Selector for Distribution */}
          {selectedMetric === "distributions" && schema?.fields && (
            <div>
              <label className="form-label" style={{ marginBottom: "4px" }}>
                Feature
              </label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="form-select"
                style={{ minWidth: "220px" }}
              >
                {schema.fields.map((f) => (
                  <option key={f.name} value={f.name}>
                    {f.label} {f.is_synthetic ? "(synthetic)" : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Cluster filter (optional) */}
          <div>
            <label className="form-label" style={{ marginBottom: "4px" }}>
              Cluster Scope
            </label>
            <select
              value={selectedCluster}
              onChange={(e) => setSelectedCluster(e.target.value)}
              className="form-select"
              style={{ minWidth: "160px" }}
            >
              <option value="">All Customers</option>
              <option value="0">Segment 0 Only</option>
              <option value="1">Segment 1 Only</option>
              <option value="2">Segment 2 Only</option>
              <option value="3">Segment 3 Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main EDA Content */}
      {isLoading ? (
        <CardSkeleton />
      ) : isError || !data ? (
        <StatusNotice
          type="error"
          title="Could not compute EDA metric"
          message="Failed to compute statistical insights. Please try another feature or retry."
          actionText="Retry"
          onAction={() => refetch()}
        />
      ) : (
        <>
          {/* 1. Feature Distribution Histogram */}
          {selectedMetric === "distributions" && (
            <div className="card">
              {(() => {
                const dist = data as unknown as EDADistributionResponse;
                return (
                  <div>
                    <div className="card-header">
                      <div>
                        <h2 className="card-title">{dist.label} Distribution</h2>
                        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                          Total observations: {dist.count?.toLocaleString()}{" "}
                          {dist.is_synthetic && "· Augmented synthetic feature"}
                        </div>
                      </div>
                    </div>

                    {/* Numeric Summary Stats */}
                    {dist.type === "numeric" && dist.bins && (
                      <>
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                            gap: "10px",
                            padding: "12px",
                            backgroundColor: "var(--bg-subtle)",
                            borderRadius: "var(--radius-sm)",
                            marginBottom: "20px",
                            fontSize: "12.5px",
                          }}
                        >
                          <div>
                            <span style={{ color: "var(--text-muted)" }}>Min:</span>{" "}
                            <strong>{dist.min?.toLocaleString()}</strong>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-muted)" }}>Median:</span>{" "}
                            <strong>{dist.median?.toLocaleString()}</strong>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-muted)" }}>Mean:</span>{" "}
                            <strong>{dist.mean?.toLocaleString()}</strong>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-muted)" }}>Max:</span>{" "}
                            <strong>{dist.max?.toLocaleString()}</strong>
                          </div>
                          <div>
                            <span style={{ color: "var(--text-muted)" }}>Std Dev:</span>{" "}
                            <strong>{dist.std?.toLocaleString()}</strong>
                          </div>
                        </div>

                        {/* Flat SVG Histogram */}
                        <HistogramChart bins={dist.bins} />
                      </>
                    )}

                    {/* Categorical Bar Counts */}
                    {dist.type === "categorical" && dist.categories && (
                      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                        {dist.categories.map((c) => {
                          const maxCat = Math.max(...dist.categories!.map((x) => x.count), 1);
                          return (
                            <div
                              key={c.category}
                              style={{
                                display: "grid",
                                gridTemplateColumns: "180px 1fr 90px",
                                alignItems: "center",
                                gap: "10px",
                                fontSize: "13px",
                              }}
                            >
                              <div style={{ textTransform: "capitalize", fontWeight: 500 }}>{c.category}</div>
                              <div style={{ height: "14px", backgroundColor: "var(--bg-subtle)", borderRadius: "var(--radius-sm)", overflow: "hidden" }}>
                                <div
                                  style={{
                                    height: "100%",
                                    width: `${(c.count / maxCat) * 100}%`,
                                    backgroundColor: "#2563eb",
                                    borderRadius: "var(--radius-sm)",
                                  }}
                                />
                              </div>
                              <div style={{ textAlign: "right", fontFeatureSettings: "tnum", color: "var(--text-muted)" }}>
                                {c.count.toLocaleString()}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {/* 2. Missing Values Analysis */}
          {selectedMetric === "missing" && (
            <div className="card">
              <div className="card-header">
                <div>
                  <h2 className="card-title">Missing Values & Data Completeness</h2>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Column completeness analysis across {(data as unknown as EDAMissingResponse).total_rows?.toLocaleString()} rows
                  </div>
                </div>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Missing Count</th>
                      <th>Missing Percentage</th>
                      <th>Data Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data as unknown as EDAMissingResponse).columns?.map((col) => {
                      const isComplete = col.missing_count === 0;
                      return (
                        <tr key={col.column}>
                          <td>
                            <strong>{col.column}</strong>
                          </td>
                          <td>{col.missing_count.toLocaleString()}</td>
                          <td>{col.missing_pct}%</td>
                          <td>
                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                                padding: "2px 8px",
                                borderRadius: "var(--radius-sm)",
                                fontSize: "12px",
                                backgroundColor: isComplete ? "var(--status-good-bg)" : "var(--status-warn-bg)",
                                color: isComplete ? "var(--status-good)" : "var(--status-warn)",
                                border: `1px solid ${isComplete ? "var(--status-good-border)" : "var(--status-warn-border)"}`,
                              }}
                            >
                              {isComplete ? "100% Complete" : `${col.missing_pct}% Imputed`}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. Correlation Heatmap Table */}
          {selectedMetric === "correlations" && (
            <div className="card">
              <div className="card-header">
                <div>
                  <h2 className="card-title">Feature Correlation Matrix</h2>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Pairwise Pearson correlation coefficients between numerical banking features (-1.0 to +1.0)
                  </div>
                </div>
              </div>

              <div className="table-container">
                <table className="data-table" style={{ fontSize: "12px" }}>
                  <thead>
                    <tr>
                      <th>Feature</th>
                      {(data as unknown as EDACorrelationResponse).features?.map((f) => (
                        <th key={f} style={{ textAlign: "center" }}>
                          {f.replace("_", " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(data as unknown as EDACorrelationResponse).matrix?.map((row) => (
                      <tr key={row.feature}>
                        <td>
                          <strong>{row.label}</strong>
                        </td>
                        {(data as unknown as EDACorrelationResponse).features?.map((f) => {
                          const val = row.values[f];
                          const absVal = Math.abs(val);
                          // Flat contrast background
                          let bg = "transparent";
                          let color = "var(--text-main)";
                          if (val > 0.4) {
                            bg = "#eff6ff";
                            color = "#1d4ed8";
                          } else if (val < -0.3) {
                            bg = "#fef2f2";
                            color = "#b91c1c";
                          }
                          return (
                            <td
                              key={f}
                              style={{
                                textAlign: "center",
                                backgroundColor: bg,
                                color,
                                fontWeight: absVal > 0.4 ? "600" : "400",
                              }}
                            >
                              {val.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
