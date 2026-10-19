import React from "react";

export const Skeleton: React.FC<{
  width?: string;
  height?: string;
  borderRadius?: string;
  style?: React.CSSProperties;
}> = ({ width = "100%", height = "18px", borderRadius = "var(--radius-sm)", style }) => {
  return (
    <div
      style={{
        width,
        height,
        backgroundColor: "var(--border)",
        borderRadius,
        opacity: 0.6,
        ...style,
      }}
    />
  );
};

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 6,
}) => {
  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i}>
                <Skeleton height="14px" width="70%" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r}>
              {Array.from({ length: columns }).map((_, c) => (
                <td key={c}>
                  <Skeleton height="16px" width={c === 0 ? "50px" : "80%"} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <Skeleton height="20px" width="40%" />
      <Skeleton height="14px" width="85%" />
      <Skeleton height="14px" width="70%" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "10px" }}>
        <Skeleton height="35px" />
        <Skeleton height="35px" />
      </div>
    </div>
  );
};
