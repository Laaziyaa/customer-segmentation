import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { SegmentDistributionChart, getSegmentColor } from "../components/Charts";
import { CardSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";

export const OverviewPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["segments"],
    queryFn: api.getSegments,
  });

  if (isLoading) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Overview</h1>
          <p className="page-desc">Customer segmentation summary and portfolio distribution.</p>
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
          <h1 className="page-title">Overview</h1>
        </div>
        <StatusNotice
          type="error"
          title="Could not load segment overview"
          message="Unable to retrieve segment data from the server. Check your connection or retry."
          actionText="Retry"
          onAction={() => refetch()}
        />
      </div>
    );
  }

  const { segments, total_customers, number_of_segments, last_updated } = data;

  const avgIncome =
    segments.reduce((acc, s) => acc + s.average_income * s.customers, 0) /
    maxTotal(total_customers);
  const avgBalance =
    segments.reduce((acc, s) => acc + s.average_balance * s.customers, 0) /
    maxTotal(total_customers);
  const avgCredit =
    segments.reduce((acc, s) => acc + s.average_credit_score * s.customers, 0) /
    maxTotal(total_customers);

  function maxTotal(n: number) {
    return n > 0 ? n : 1;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-desc">
          Customer portfolio segmented by transactional behavior, balance holding, and digital engagement.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="metrics-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Customers</div>
          <div className="kpi-val">{total_customers.toLocaleString()}</div>
          <div className="kpi-sub">In active dataset</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Customer Segments</div>
          <div className="kpi-val">{number_of_segments}</div>
          <div className="kpi-sub">K-Means clusters</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Avg. Annual Income</div>
          <div className="kpi-val">${Math.round(avgIncome).toLocaleString()}</div>
          <div className="kpi-sub">Portfolio average (synthetic)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Avg. Account Balance</div>
          <div className="kpi-val">${Math.round(avgBalance).toLocaleString()}</div>
          <div className="kpi-sub">Portfolio average (synthetic)</div>
        </div>
      </div>

      {/* Segment Size Distribution Bar Chart */}
      <div className="card" style={{ marginBottom: "28px" }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Segment Distribution</h2>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Customer count and relative share per segment
            </div>
          </div>
        </div>
        <SegmentDistributionChart segments={segments} />
      </div>

      {/* Plain-language Segment Summaries */}
      <div>
        <h2 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "14px", color: "var(--text-main)" }}>
          Segment Summaries
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
          {segments.map((s) => (
            <div key={s.cluster} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                <div>
                  <h3 style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-main)" }}>
                    {s.persona}
                  </h3>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Segment {s.cluster} · {s.customers.toLocaleString()} customers ({s.percentage}%)
                  </div>
                </div>
                <span
                  style={{
                    width: "24px",
                    height: "24px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: getSegmentColor(s.cluster),
                    color: "#ffffff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "12px",
                  }}
                >
                  {s.cluster}
                </span>
              </div>

              <p style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: 1.45, marginBottom: "12px" }}>
                {s.summary}
              </p>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "8px",
                  fontSize: "12px",
                  paddingTop: "10px",
                  borderTop: "1px solid var(--border)",
                  color: "var(--text-muted)",
                }}
              >
                <div>
                  Income: <strong style={{ color: "var(--text-main)" }}>${Math.round(s.average_income).toLocaleString()}</strong>
                </div>
                <div>
                  Balance: <strong style={{ color: "var(--text-main)" }}>${Math.round(s.average_balance).toLocaleString()}</strong>
                </div>
                <div>
                  Digital Score: <strong style={{ color: "var(--text-main)" }}>{Math.round(s.average_digital_score)}/100</strong>
                </div>
                <div>
                  Monthly Trans: <strong style={{ color: "var(--text-main)" }}>{Math.round(s.average_transactions)}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
