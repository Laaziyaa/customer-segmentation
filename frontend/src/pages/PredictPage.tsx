import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { CheckCircle, AlertTriangle, UserCheck, RotateCcw, Sparkles } from "lucide-react";
import { api } from "../api/client";
import type { PredictResponse, SchemaField } from "../api/types";
import { CardSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";
import { getSegmentColor } from "../components/Charts";

export const PredictPage: React.FC = () => {
  const { data: schema, isLoading: isSchemaLoading, isError: isSchemaError } = useQuery({
    queryKey: ["datasetSchema"],
    queryFn: api.getSchema,
  });

  const [formData, setFormData] = useState<Record<string, any>>({});
  const [result, setResult] = useState<PredictResponse | null>(null);

  // Initialize form state dynamically from schema defaults
  useEffect(() => {
    if (schema?.fields) {
      const initial: Record<string, any> = {};
      schema.fields.forEach((f) => {
        initial[f.name] = f.default;
      });
      setFormData(initial);
    }
  }, [schema]);

  const predictMutation = useMutation({
    mutationFn: (payload: Record<string, any>) => api.predict(payload),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleFieldChange = (name: string, value: any, type: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: type === "number" ? (value === "" ? "" : Number(value)) : value,
    }));
  };

  const handleResetSample = () => {
    if (schema?.fields) {
      const initial: Record<string, any> = {};
      schema.fields.forEach((f) => {
        initial[f.name] = f.default;
      });
      setFormData(initial);
      setResult(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    predictMutation.mutate(formData);
  };

  if (isSchemaLoading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Check a new customer</h1>
          <p className="page-desc">Loading schema from active dataset...</p>
        </div>
        <CardSkeleton />
      </div>
    );
  }

  if (isSchemaError || !schema) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Check a new customer</h1>
        </div>
        <StatusNotice
          type="error"
          title="Could not load customer schema"
          message="Server schema endpoint is unavailable. Please verify connection or retry."
        />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Check a new customer</h1>
        <p className="page-desc">
          Enter customer financial and demographic characteristics to score their segment and receive real-time product recommendations. Form structure is generated dynamically from the model schema.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: result ? "1fr 1fr" : "1fr", gap: "24px", alignItems: "start" }}>
        {/* Dynamic Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Customer Profile Form</h2>
            <button
              type="button"
              onClick={handleResetSample}
              className="btn btn-secondary"
              style={{ fontSize: "12px", padding: "4px 8px" }}
            >
              <RotateCcw size={12} />
              Reset defaults
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                gap: "14px 16px",
              }}
            >
              {schema.fields.map((field: SchemaField) => {
                const isSelect = field.type === "select";

                return (
                  <div key={field.name} className="form-group" style={{ marginBottom: "0" }}>
                    <label className="form-label" htmlFor={`field-${field.name}`}>
                      {field.label}
                      {field.is_synthetic && (
                        <span
                          title="Synthetic feature"
                          style={{
                            fontSize: "10.5px",
                            color: "var(--text-muted)",
                            marginLeft: "4px",
                            fontWeight: 400,
                          }}
                        >
                          (synthetic)
                        </span>
                      )}
                    </label>

                    {isSelect ? (
                      <select
                        id={`field-${field.name}`}
                        value={formData[field.name] ?? field.default}
                        onChange={(e) => handleFieldChange(field.name, e.target.value, "select")}
                        className="form-select"
                        required
                      >
                        {field.options?.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        id={`field-${field.name}`}
                        type="number"
                        step="any"
                        min={field.min}
                        max={field.max}
                        value={formData[field.name] ?? ""}
                        onChange={(e) => handleFieldChange(field.name, e.target.value, "number")}
                        className="form-input"
                        required
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: "24px", display: "flex", gap: "10px" }}>
              <button
                type="submit"
                disabled={predictMutation.isPending}
                className="btn btn-primary"
                style={{ padding: "10px 20px", fontSize: "14px" }}
              >
                <UserCheck size={16} />
                {predictMutation.isPending ? "Scoring profile..." : "Predict Segment"}
              </button>
            </div>
          </form>

          {predictMutation.isError && (
            <div style={{ marginTop: "16px" }}>
              <StatusNotice
                type="error"
                title="Prediction failed"
                message={(predictMutation.error as Error)?.message || "Check all fields and try again."}
              />
            </div>
          )}
        </div>

        {/* Prediction Result Display */}
        {result && (
          <div className="card" style={{ borderLeft: `4px solid ${getSegmentColor(result.predicted_cluster)}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
              <div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "var(--text-muted)",
                  }}
                >
                  Model Prediction
                </span>
                <h3 style={{ fontSize: "18px", fontWeight: 700, color: "var(--text-main)", marginTop: "2px" }}>
                  {result.persona}
                </h3>
                <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                  Assigned to Segment {result.predicted_cluster} ·{" "}
                  <strong>{Math.round(result.confidence * 100)}% confidence</strong>
                </div>
              </div>

              <span
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: getSegmentColor(result.predicted_cluster),
                  color: "#ffffff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "16px",
                  flexShrink: 0,
                }}
              >
                {result.predicted_cluster}
              </span>
            </div>

            {/* Warnings if any */}
            {result.warnings && result.warnings.length > 0 && (
              <div
                style={{
                  padding: "10px 14px",
                  backgroundColor: "var(--status-warn-bg)",
                  border: "1px solid var(--status-warn-border)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "12.5px",
                  color: "var(--status-warn)",
                  marginBottom: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                }}
              >
                {result.warnings.map((w, idx) => (
                  <div key={idx} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <AlertTriangle size={13} />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Assignment Reasons */}
            <div style={{ marginBottom: "18px" }}>
              <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Why this segment?
              </div>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", display: "flex", flexDirection: "column", gap: "4px" }}>
                {result.reasons?.map((reason, i) => (
                  <li key={i} style={{ color: "var(--text-main)" }}>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Recommendations */}
            <div style={{ borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
              <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "10px" }}>
                Suggested Next-Best Products
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {result.recommendations?.map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "10px 12px",
                      backgroundColor: "var(--bg-subtle)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <strong style={{ fontSize: "13.5px", color: "var(--text-main)" }}>{rec.title}</strong>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                        {rec.category}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "3px" }}>
                      {rec.reason}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
