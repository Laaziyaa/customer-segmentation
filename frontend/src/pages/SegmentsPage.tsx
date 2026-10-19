import React from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, TrendingUp, TrendingDown, Users } from "lucide-react";
import { api } from "../api/client";
import { CardSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";
import { getSegmentColor } from "../components/Charts";

export const SegmentsPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["segments"],
    queryFn: api.getSegments,
  });

  if (isLoading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Segments</h1>
          <p className="page-desc">Customer segmentation analysis and behavioral comparisons.</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
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
          <h1 className="page-title">Segments</h1>
        </div>
        <StatusNotice
          type="error"
          title="Could not load customer segments"
          message="Server error while retrieving segment profiles. Try refreshing the page."
          actionText="Retry"
          onAction={() => refetch()}
        />
      </div>
    );
  }

  const { segments, total_customers } = data;

  // Portfolio overall averages to compute comparative traits
  const popIncome =
    segments.reduce((acc, s) => acc + s.average_income * s.customers, 0) /
    (total_customers || 1);
  const popBalance =
    segments.reduce((acc, s) => acc + s.average_balance * s.customers, 0) /
    (total_customers || 1);
  const popDigital =
    segments.reduce((acc, s) => acc + s.average_digital_score * s.customers, 0) /
    (total_customers || 1);
  const popTrans =
    segments.reduce((acc, s) => acc + s.average_transactions * s.customers, 0) /
    (total_customers || 1);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Segments</h1>
        <p className="page-desc">
          Distinct behavioral clusters derived from financial activity. Each segment includes trait comparisons against portfolio averages and suggested retention actions.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "20px" }}>
        {segments.map((s) => {
          const color = getSegmentColor(s.cluster);

          // Calculate comparative differences vs portfolio averages
          const traits = [
            {
              name: "Annual Income",
              clusterVal: s.average_income,
              popVal: popIncome,
              unit: "$",
              formatted: `$${Math.round(s.average_income).toLocaleString()}`,
              diffPct: Math.round(((s.average_income - popIncome) / popIncome) * 100),
            },
            {
              name: "Account Balance",
              clusterVal: s.average_balance,
              popVal: popBalance,
              unit: "$",
              formatted: `$${Math.round(s.average_balance).toLocaleString()}`,
              diffPct: Math.round(((s.average_balance - popBalance) / popBalance) * 100),
            },
            {
              name: "Digital Engagement",
              clusterVal: s.average_digital_score,
              popVal: popDigital,
              unit: "/100",
              formatted: `${Math.round(s.average_digital_score)}/100`,
              diffPct: Math.round(((s.average_digital_score - popDigital) / popDigital) * 100),
            },
            {
              name: "Monthly Transactions",
              clusterVal: s.average_transactions,
              popVal: popTrans,
              unit: "",
              formatted: `${Math.round(s.average_transactions)}`,
              diffPct: Math.round(((s.average_transactions - popTrans) / popTrans) * 100),
            },
          ];

          return (
            <div key={s.cluster} className="card" style={{ display: "flex", flexDirection: "column" }}>
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <div>
                  <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--text-main)" }}>
                    {s.persona}
                  </h2>
                  <div style={{ fontSize: "12.5px", color: "var(--text-muted)", marginTop: "2px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <Users size={13} />
                    <span>
                      Segment {s.cluster} · <strong>{s.customers.toLocaleString()}</strong> customers ({s.percentage}%)
                    </span>
                  </div>
                </div>
                <span
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: color,
                    color: "#ffffff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "13px",
                    flexShrink: 0,
                  }}
                >
                  {s.cluster}
                </span>
              </div>

              {/* Natural language summary */}
              <p style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: 1.45, marginBottom: "16px" }}>
                {s.summary}
              </p>

              {/* Trait Comparison Bars vs Average */}
              <div style={{ marginBottom: "18px", borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
                <div style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "10px" }}>
                  How it differs from portfolio average
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
                  {traits.map((trait) => {
                    const isPositive = trait.diffPct >= 0;
                    return (
                      <div key={trait.name} style={{ fontSize: "12.5px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                          <span style={{ color: "var(--text-muted)" }}>{trait.name}</span>
                          <span style={{ fontFeatureSettings: "tnum" }}>
                            <strong>{trait.formatted}</strong>{" "}
                            <span
                              style={{
                                color: isPositive ? "var(--status-good)" : "var(--status-warn)",
                                fontSize: "11.5px",
                                fontWeight: 600,
                              }}
                            >
                              ({isPositive ? "+" : ""}
                              {trait.diffPct}%)
                            </span>
                          </span>
                        </div>

                        {/* Flat comparison mini bar */}
                        <div
                          style={{
                            height: "6px",
                            backgroundColor: "var(--bg-subtle)",
                            borderRadius: "var(--radius-sm)",
                            overflow: "hidden",
                          }}
                        >
                          <div
                            style={{
                              width: `${Math.min(100, Math.max(10, 50 + trait.diffPct / 2))}%`,
                              backgroundColor: color,
                              height: "100%",
                              borderRadius: "var(--radius-sm)",
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recommended Retention & Cross-Sell Actions */}
              <div style={{ marginTop: "auto", borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
                <div style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "8px" }}>
                  Recommended Banking Products
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {s.recommended_products.map((prod, i) => (
                    <span
                      key={i}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "4px 8px",
                        fontSize: "12px",
                        backgroundColor: "var(--bg-subtle)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                        color: "var(--text-main)",
                      }}
                    >
                      <CheckCircle2 size={12} style={{ color: "var(--status-good)" }} />
                      {prod}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
