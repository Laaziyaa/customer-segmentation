import React from "react";
import { AlertCircle, AlertTriangle, CheckCircle, RefreshCw, Server } from "lucide-react";

interface StatusNoticeProps {
  type?: "info" | "warning" | "error" | "waking";
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

export const StatusNotice: React.FC<StatusNoticeProps> = ({
  type = "info",
  title,
  message,
  actionText,
  onAction,
}) => {
  const getIcon = () => {
    switch (type) {
      case "waking":
        return <Server size={18} className="spin" style={{ color: "var(--accent)", flexShrink: 0 }} />;
      case "warning":
        return <AlertTriangle size={18} style={{ color: "var(--status-warn)", flexShrink: 0 }} />;
      case "error":
        return <AlertCircle size={18} style={{ color: "var(--status-bad)", flexShrink: 0 }} />;
      default:
        return <CheckCircle size={18} style={{ color: "var(--accent)", flexShrink: 0 }} />;
    }
  };

  const getClassName = () => {
    switch (type) {
      case "warning":
        return "notice notice-warning";
      case "error":
        return "notice notice-error";
      default:
        return "notice notice-info";
    }
  };

  return (
    <div className={getClassName()} role="alert">
      {getIcon()}
      <div style={{ flex: 1 }}>
        {title && <div style={{ fontWeight: 600, marginBottom: "2px" }}>{title}</div>}
        <div style={{ lineHeight: 1.45 }}>{message}</div>
      </div>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="btn btn-secondary"
          style={{ padding: "4px 10px", fontSize: "12px", alignSelf: "center", marginLeft: "12px" }}
        >
          <RefreshCw size={12} />
          {actionText}
        </button>
      )}
    </div>
  );
};
