/**
 * Lightweight, accessible, flat SVG charts with zero gradients.
 * Uses a fixed, color-blind-safe quiet palette with text alternatives.
 */

import React, { useState } from "react";

export const SEGMENT_COLORS = [
  "#2563eb", // Blue
  "#0d9488", // Teal
  "#d97706", // Amber
  "#7c3aed", // Violet
  "#ea580c", // Orange
  "#0284c7", // Sky
];

export function getSegmentColor(cluster: number): string {
  return SEGMENT_COLORS[cluster % SEGMENT_COLORS.length];
}

// ----------------------------------------------------
// 1. Segment Distribution Bar Chart
// ----------------------------------------------------

interface SegmentBarProps {
  segments: Array<{
    cluster: number;
    persona: string;
    customers: number;
    percentage: number;
  }>;
}

export const SegmentDistributionChart: React.FC<SegmentBarProps> = ({ segments }) => {
  const maxCount = Math.max(...segments.map((s) => s.customers), 1);

  return (
    <div className="chart-wrapper" aria-label="Segment customer distribution bar chart">
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {segments.map((s) => {
          const color = getSegmentColor(s.cluster);
          const widthPct = Math.max(3, (s.customers / maxCount) * 100);

          return (
            <div
              key={s.cluster}
              style={{
                display: "grid",
                gridTemplateColumns: "180px 1fr 110px",
                alignItems: "center",
                gap: "12px",
                fontSize: "13px",
              }}
            >
              <div style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: "8px",
                    height: "8px",
                    borderRadius: "2px",
                    backgroundColor: color,
                    marginRight: "6px",
                  }}
                />
                {s.persona || `Segment ${s.cluster}`}
              </div>

              {/* Solid flat bar */}
              <div
                style={{
                  height: "18px",
                  backgroundColor: "var(--bg-subtle)",
                  borderRadius: "var(--radius-sm)",
                  overflow: "hidden",
                  display: "flex",
                }}
              >
                <div
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: color,
                    height: "100%",
                    borderRadius: "var(--radius-sm)",
                    transition: "width 0.2s ease",
                  }}
                  title={`${s.persona}: ${s.customers.toLocaleString()} customers (${s.percentage}%)`}
                />
              </div>

              <div style={{ textAlign: "right", fontFeatureSettings: "tnum", color: "var(--text-muted)" }}>
                <strong>{s.customers.toLocaleString()}</strong> ({s.percentage}%)
              </div>
            </div>
          );
        })}
      </div>

      {/* Accessible Screen Reader Table */}
      <table className="sr-only" style={{ position: "absolute", width: "1px", height: "1px", overflow: "hidden", clip: "rect(0,0,0,0)" }}>
        <caption>Customer distribution across segments</caption>
        <thead>
          <tr>
            <th>Segment</th>
            <th>Customers</th>
            <th>Percentage</th>
          </tr>
        </thead>
        <tbody>
          {segments.map((s) => (
            <tr key={s.cluster}>
              <td>{s.persona}</td>
              <td>{s.customers}</td>
              <td>{s.percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ----------------------------------------------------
// 2. Histogram Chart (for EDA Distributions)
// ----------------------------------------------------

interface HistogramProps {
  bins: Array<{
    label: string;
    count: number;
    bin_start?: number;
    bin_end?: number;
  }>;
  unit?: string;
}

export const HistogramChart: React.FC<HistogramProps> = ({ bins, unit = "" }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const maxCount = Math.max(...bins.map((b) => b.count), 1);

  const chartHeight = 180;
  const barWidth = 38;
  const gap = 12;
  const chartWidth = Math.max(500, bins.length * (barWidth + gap) + 40);

  return (
    <div style={{ width: "100%", overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight + 45}`}
        style={{ width: "100%", height: "auto", minWidth: `${chartWidth}px`, display: "block" }}
        role="img"
        aria-label="Distribution histogram chart"
      >
        {/* Baseline */}
        <line x1="30" y1={chartHeight} x2={chartWidth - 10} y2={chartHeight} stroke="var(--border-strong)" strokeWidth="1" />

        {bins.map((bin, i) => {
          const barHeight = Math.max(2, (bin.count / maxCount) * (chartHeight - 30));
          const x = 35 + i * (barWidth + gap);
          const y = chartHeight - barHeight;
          const isHovered = hoveredIndex === i;

          return (
            <g key={i} onMouseEnter={() => setHoveredIndex(i)} onMouseLeave={() => setHoveredIndex(null)}>
              {/* Bar */}
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={isHovered ? "#1d4ed8" : "#3b82f6"}
                rx="3"
                style={{ cursor: "pointer", transition: "fill 0.12s ease" }}
              />

              {/* Value label on top of bar */}
              <text
                x={x + barWidth / 2}
                y={y - 6}
                textAnchor="middle"
                fontSize="11"
                fill={isHovered ? "var(--text-main)" : "var(--text-muted)"}
                fontWeight={isHovered ? "600" : "400"}
              >
                {bin.count.toLocaleString()}
              </text>

              {/* X Axis Label */}
              <text
                x={x + barWidth / 2}
                y={chartHeight + 18}
                textAnchor="middle"
                fontSize="10.5"
                fill="var(--text-muted)"
              >
                {bin.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ----------------------------------------------------
// 3. Line Curve Chart (Elbow & Silhouette)
// ----------------------------------------------------

interface LineCurveProps {
  data: Array<{ k: number; value: number }>;
  yLabel: string;
  recommendedK?: number;
}

export const LineCurveChart: React.FC<LineCurveProps> = ({ data, yLabel, recommendedK }) => {
  if (!data || data.length === 0) return <div>No curve points available.</div>;

  const width = 520;
  const height = 220;
  const padding = { top: 25, right: 30, bottom: 40, left: 55 };

  const values = data.map((d) => d.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const valRange = maxVal - minVal || 1;

  const getX = (k: number) => {
    const minK = data[0].k;
    const maxK = data[data.length - 1].k;
    return padding.left + ((k - minK) / (maxK - minK || 1)) * (width - padding.left - padding.right);
  };

  const getY = (val: number) => {
    return height - padding.bottom - ((val - minVal) / valRange) * (height - padding.top - padding.bottom);
  };

  const points = data.map((d) => `${getX(d.k)},${getY(d.value)}`).join(" ");

  return (
    <div style={{ width: "100%", overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "auto", display: "block" }}
        role="img"
        aria-label={`${yLabel} curve line chart`}
      >
        {/* Y Axis Grid lines & Labels */}
        {[0, 0.5, 1].map((step, idx) => {
          const val = minVal + step * valRange;
          const yPos = getY(val);
          return (
            <g key={idx}>
              <line
                x1={padding.left}
                y1={yPos}
                x2={width - padding.right}
                y2={yPos}
                stroke="var(--border)"
                strokeDasharray="4 4"
              />
              <text x={padding.left - 8} y={yPos + 4} textAnchor="end" fontSize="10.5" fill="var(--text-muted)">
                {val > 100 ? Math.round(val).toLocaleString() : val.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* Solid Line (NO gradients) */}
        <polyline fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinejoin="round" points={points} />

        {/* Data points */}
        {data.map((d) => {
          const cx = getX(d.k);
          const cy = getY(d.value);
          const isOptimal = recommendedK === d.k;

          return (
            <g key={d.k}>
              <circle
                cx={cx}
                cy={cy}
                r={isOptimal ? 6 : 4}
                fill={isOptimal ? "#15803d" : "#ffffff"}
                stroke={isOptimal ? "#15803d" : "#2563eb"}
                strokeWidth="2"
              />
              {/* Point value tag */}
              <text
                x={cx}
                y={cy - 10}
                textAnchor="middle"
                fontSize="10"
                fill={isOptimal ? "#15803d" : "var(--text-muted)"}
                fontWeight={isOptimal ? "700" : "500"}
              >
                {d.value > 100 ? Math.round(d.value).toLocaleString() : d.value.toFixed(2)}
              </text>

              {/* X Axis label (K) */}
              <text x={cx} y={height - padding.bottom + 18} textAnchor="middle" fontSize="11" fill="var(--text-main)">
                K={d.k}
              </text>
            </g>
          );
        })}

        {/* Axes lines */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke="var(--border-strong)"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="var(--border-strong)"
        />
      </svg>
    </div>
  );
};
