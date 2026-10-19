import React, { useEffect } from "react";
import { X, CheckCircle, HelpCircle, Layers } from "lucide-react";
import type { CustomerDetailResponse } from "../api/types";
import { getSegmentColor } from "./Charts";

interface CustomerDrawerProps {
  customerDetail: CustomerDetailResponse | null;
  onClose: () => void;
  isLoading: boolean;
}

export const CustomerDrawer: React.FC<CustomerDrawerProps> = ({
  customerDetail,
  onClose,
  isLoading,
}) => {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!customerDetail && !isLoading) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Customer profile details">
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid var(--border)", paddingBottom: "16px" }}>
          <div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
              Customer Profile
            </div>
            <h2 style={{ fontSize: "20px", fontWeight: 700, marginTop: "2px" }}>
              #{customerDetail?.customer?.customer_id || "..."}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: "6px", borderRadius: "50%" }}
            aria-label="Close drawer"
          >
            <X size={18} />
          </button>
        </div>

        {isLoading ? (
          <div style={{ padding: "20px 0", color: "var(--text-muted)" }}>
            Loading customer profile and segment comparisons...
          </div>
        ) : customerDetail ? (
          <>
            {/* Segment Assignment Badge Card */}
            <div
              style={{
                backgroundColor: "var(--bg-subtle)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
                padding: "16px",
                display: "flex",
                alignItems: "center",
                gap: "14px",
              }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: getSegmentColor(customerDetail.cluster),
                  color: "#ffffff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "16px",
                  flexShrink: 0,
                }}
              >
                {customerDetail.cluster}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: "15px", color: "var(--text-main)" }}>
                  {customerDetail.persona}
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Segment {customerDetail.cluster} assignment
                </div>
              </div>
            </div>

            {/* Why This Segment Section */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
                <HelpCircle size={15} style={{ color: "var(--accent)" }} />
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-main)" }}>
                  Why this segment?
                </h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {customerDetail.explanation?.map((exp, idx) => (
                  <div
                    key={idx}
                    style={{
                      fontSize: "12.5px",
                      padding: "8px 12px",
                      backgroundColor: "var(--bg-surface)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      lineHeight: 1.4,
                    }}
                  >
                    <strong>{exp.label}:</strong> {exp.sentence}
                  </div>
                ))}
              </div>
            </div>

            {/* Financial & Demographic Attributes */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
                <Layers size={15} style={{ color: "var(--accent)" }} />
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-main)" }}>
                  Attributes & Behavioral Data
                </h3>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "10px 14px",
                  fontSize: "12.5px",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  padding: "14px",
                  backgroundColor: "var(--bg-surface)",
                }}
              >
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Age & Marital</span>
                  <strong>{customerDetail.customer.age} yrs · {customerDetail.customer.marital || "—"}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Job</span>
                  <strong>{customerDetail.customer.job || "—"}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Annual Income *</span>
                  <strong>${Number(customerDetail.customer.annual_income || 0).toLocaleString()}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Credit Score *</span>
                  <strong>{customerDetail.customer.credit_score || "—"}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Account Balance *</span>
                  <strong>${Number(customerDetail.customer.account_balance || 0).toLocaleString()}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Digital Score *</span>
                  <strong>{customerDetail.customer.digital_banking_score || "—"}/100</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Monthly Transactions *</span>
                  <strong>{customerDetail.customer.monthly_transactions || "—"}</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)", display: "block" }}>Account Tenure *</span>
                  <strong>{customerDetail.customer.account_tenure || "—"} yrs</strong>
                </div>
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px" }}>
                * Synthetic columns added to standard UCI dataset for banking analytics demonstration.
              </div>
            </div>

            {/* Recommended Products */}
            <div>
              <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "10px", color: "var(--text-main)" }}>
                Recommended Banking Actions
              </h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {customerDetail.recommendations?.map((product, i) => (
                  <span
                    key={i}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "5px",
                      padding: "5px 10px",
                      fontSize: "12px",
                      backgroundColor: "var(--bg-subtle)",
                      border: "1px solid var(--border-strong)",
                      borderRadius: "var(--radius-sm)",
                      color: "var(--text-main)",
                    }}
                  >
                    <CheckCircle size={13} style={{ color: "var(--status-good)" }} />
                    {product}
                  </span>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
