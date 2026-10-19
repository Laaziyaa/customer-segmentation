import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Play, CheckCircle2, AlertCircle, FileText, Database, RotateCcw } from "lucide-react";
import { api } from "../api/client";
import type { UploadResponse, PipelineStatusResponse } from "../api/types";
import { StatusNotice } from "../components/StatusNotice";

export const DataPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [customK, setCustomK] = useState<number>(4);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Poll background job progress when active
  const { data: jobStatus } = useQuery<PipelineStatusResponse>({
    queryKey: ["jobStatus", activeJobId],
    queryFn: () => api.getPipelineStatus(activeJobId!),
    enabled: !!activeJobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "completed" || data?.status === "failed") {
        return false;
      }
      return 1500;
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDataset(file),
    onSuccess: (data) => {
      setUploadResult(data);
      setCustomK(data.suggested_k || 4);
    },
  });

  // Train mutation
  const trainMutation = useMutation({
    mutationFn: ({ datasetId, k }: { datasetId: string; k: number }) =>
      api.trainDataset(datasetId, k),
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
    },
  });

  const [resetFeedback, setResetFeedback] = useState<string | null>(null);

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: () => api.resetDataset(),
    onSuccess: (data) => {
      setResetFeedback(data.message);
      setSelectedFile(null);
      setUploadResult(null);
      setActiveJobId(null);
      queryClient.invalidateQueries({ queryKey: ["health"] });
      queryClient.invalidateQueries({ queryKey: ["segments"] });
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["datasetSchema"] });
      queryClient.invalidateQueries({ queryKey: ["modelEvaluation"] });
      queryClient.invalidateQueries({ queryKey: ["eda"] });
    },
  });

  const handleFileDrop = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadResult(null);
      setActiveJobId(null);
      uploadMutation.mutate(file);
    }
  };

  const handleStartPipeline = () => {
    if (!uploadResult) return;
    trainMutation.mutate({
      datasetId: uploadResult.dataset_id,
      k: customK,
    });
  };

  // If job completed, invalidate all queries so entire app updates without reload
  React.useEffect(() => {
    if (jobStatus?.status === "completed") {
      queryClient.invalidateQueries({ queryKey: ["health"] });
      queryClient.invalidateQueries({ queryKey: ["segments"] });
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["datasetSchema"] });
      queryClient.invalidateQueries({ queryKey: ["modelEvaluation"] });
      queryClient.invalidateQueries({ queryKey: ["eda"] });
    }
  }, [jobStatus?.status, queryClient]);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Data management</h1>
        <p className="page-desc">
          Upload new customer datasets, review detected feature types, configure cluster targets, and execute the segmentation pipeline.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Restore Original Dataset Option */}
        <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-main)" }}>
              Active Customer Portfolio
            </div>
            <div style={{ fontSize: "12.5px", color: "var(--text-muted)", marginTop: "2px" }}>
              Switch back to the complete baseline portfolio (41,188 customers, 4 personas) at any time.
            </div>
          </div>
          <button
            type="button"
            onClick={() => resetMutation.mutate()}
            disabled={resetMutation.isPending}
            className="btn btn-secondary"
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <RotateCcw size={14} />
            <span>{resetMutation.isPending ? "Restoring..." : "Restore Default Portfolio (41,188)"}</span>
          </button>
        </div>

        {resetFeedback && (
          <StatusNotice
            type="success"
            title="Portfolio Restored"
            message={resetFeedback}
          />
        )}

        {/* Upload Zone */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Upload Customer CSV</h2>
          </div>

          <div
            style={{
              border: "2px dashed var(--border-strong)",
              borderRadius: "var(--radius-md)",
              padding: "36px 20px",
              textAlign: "center",
              backgroundColor: "var(--bg-subtle)",
              cursor: "pointer",
            }}
            onClick={() => document.getElementById("csv-file-input")?.click()}
          >
            <input
              id="csv-file-input"
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={handleFileDrop}
            />
            <Upload size={28} style={{ color: "var(--accent)", margin: "0 auto 10px" }} />
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-main)" }}>
              {selectedFile ? selectedFile.name : "Click to select a CSV file or drag here"}
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Accepts comma or semicolon delimited CSV files (e.g. bank-additional-full.csv).
            </div>
          </div>

          {uploadMutation.isPending && (
            <div style={{ marginTop: "14px", color: "var(--text-muted)", fontSize: "13px" }}>
              Uploading and analyzing column schema...
            </div>
          )}

          {uploadMutation.isError && (
            <div style={{ marginTop: "14px" }}>
              <StatusNotice
                type="error"
                title="Upload failed"
                message={(uploadMutation.error as Error)?.message || "Could not parse CSV file."}
              />
            </div>
          )}
        </div>

        {/* Schema Inspection & Training Trigger */}
        {uploadResult && (
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Detected Schema: {uploadResult.filename}</h2>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                  Dataset ID: <strong>{uploadResult.dataset_id}</strong> · {uploadResult.sample_rows} sample rows analyzed
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
              {/* Numerical features */}
              <div style={{ padding: "12px", backgroundColor: "var(--bg-subtle)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Numerical Columns ({uploadResult.detected_numerical.length})
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                  {uploadResult.detected_numerical.map((c) => (
                    <span
                      key={c}
                      style={{
                        padding: "2px 6px",
                        fontSize: "11px",
                        backgroundColor: "var(--bg-surface)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              {/* Categorical features */}
              <div style={{ padding: "12px", backgroundColor: "var(--bg-subtle)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Categorical Columns ({uploadResult.detected_categorical.length})
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                  {uploadResult.detected_categorical.map((c) => (
                    <span
                      key={c}
                      style={{
                        padding: "2px 6px",
                        fontSize: "11px",
                        backgroundColor: "var(--bg-surface)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Target K and Execution */}
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "14px",
                paddingTop: "16px",
                borderTop: "1px solid var(--border)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <label className="form-label" style={{ marginBottom: 0 }}>
                  Number of Segments (K):
                </label>
                <input
                  type="number"
                  min="2"
                  max="10"
                  value={customK}
                  onChange={(e) => setCustomK(Number(e.target.value))}
                  className="form-input"
                  style={{ width: "70px" }}
                />
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  (Recommended: {uploadResult.suggested_k})
                </span>
              </div>

              <button
                type="button"
                onClick={handleStartPipeline}
                disabled={trainMutation.isPending || (jobStatus?.status === "running")}
                className="btn btn-primary"
              >
                <Play size={15} />
                Run Pipeline & Activate
              </button>
            </div>
          </div>
        )}

        {/* Live Progress Bar for Background Pipeline */}
        {jobStatus && (
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <div style={{ fontWeight: 600, fontSize: "14px" }}>
                {jobStatus.status === "completed"
                  ? "Pipeline Finished"
                  : jobStatus.status === "failed"
                  ? "Training Failed"
                  : "Pipeline in Progress"}
              </div>
              <div style={{ fontSize: "12px", fontFeatureSettings: "tnum", color: "var(--text-muted)" }}>
                {jobStatus.progress}%
              </div>
            </div>

            {/* Flat Solid Progress Bar */}
            <div
              style={{
                height: "10px",
                backgroundColor: "var(--bg-subtle)",
                borderRadius: "var(--radius-sm)",
                overflow: "hidden",
                marginBottom: "10px",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${jobStatus.progress}%`,
                  backgroundColor:
                    jobStatus.status === "failed"
                      ? "var(--status-bad)"
                      : jobStatus.status === "completed"
                      ? "var(--status-good)"
                      : "var(--accent)",
                  transition: "width 0.3s ease",
                }}
              />
            </div>

            <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>{jobStatus.message}</div>
          </div>
        )}

        {/* Synthetic Data Transparency Notice */}
        <div className="notice notice-info" style={{ marginTop: "10px" }}>
          <FileText size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <strong style={{ display: "block", marginBottom: "2px" }}>
              Dataset Transparency: UCI Bank Marketing + Synthetic Attributes
            </strong>
            The base dataset is the UCI Bank Marketing dataset (41,188 rows). Because the original dataset lacks financial balance and digital engagement scores, columns including <em>annual income</em>, <em>credit score</em>, <em>account balance</em>, <em>investment amount</em>, and <em>digital banking score</em> were synthetically generated to simulate realistic retail banking customer portfolios.
          </div>
        </div>
      </div>
    </div>
  );
};
