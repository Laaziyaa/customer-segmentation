import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Users,
  PieChart,
  UserCheck,
  Award,
  BarChart2,
  MessageSquare,
  Database,
  Server,
} from "lucide-react";
import { api } from "../api/client";
import { StatusNotice } from "./StatusNotice";

const NAV_ITEMS = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/customers", label: "Customers", icon: Users },
  { path: "/segments", label: "Segments", icon: PieChart },
  { path: "/predict", label: "Check a new customer", icon: UserCheck },
  { path: "/evaluation", label: "Model quality", icon: Award },
  { path: "/eda", label: "Data insights", icon: BarChart2 },
  { path: "/chat", label: "Ask the assistant", icon: MessageSquare },
  { path: "/data", label: "Data", icon: Database },
];

export const Layout: React.FC = () => {
  const { data: health, isError, isLoading, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  });

  const isWakingUp = isLoading || (isError && !health);

  return (
    <div className="app-container">
      {/* Desktop Slim Sidebar */}
      <aside className="sidebar" aria-label="Main Navigation">
        <div className="sidebar-header">
          <div className="brand-title">Customer Intelligence</div>
          <div className="brand-subtitle">Retail Banking Segmentation</div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                end={item.path === "/"}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="server-status-pill">
            <span
              className={`status-dot ${
                health?.status === "healthy" ? "healthy" : isWakingUp ? "connecting" : "error"
              }`}
            />
            <span>
              {health?.status === "healthy"
                ? "Server connected"
                : isWakingUp
                ? "Waking up server..."
                : "Server offline"}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-bar">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span className="active-dataset-tag">
              <Database size={13} />
              Dataset: <strong>{health?.active_dataset_id || "default"}</strong>
            </span>
            {health?.total_customers ? (
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                {health.total_customers.toLocaleString()} customers across {health.total_segments} segments
              </span>
            ) : null}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "12px", color: "var(--text-muted)" }}>
            {health?.last_updated && (
              <span>Updated: {new Date(health.last_updated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
            )}
          </div>
        </header>

        <main className="page-content">
          {/* Cold start waking notice */}
          {isWakingUp && (
            <StatusNotice
              type="waking"
              title="Connecting to Server"
              message="The model is still waking up (free server). This can take up to a minute."
              actionText="Retry"
              onAction={() => refetch()}
            />
          )}

          {isError && !health && !isLoading && (
            <StatusNotice
              type="error"
              title="Server Unreachable"
              message="Could not connect to the backend server. Verify your internet connection or check if the API is active."
              actionText="Try Again"
              onAction={() => refetch()}
            />
          )}

          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Tab Bar */}
      <nav className="mobile-tabs" aria-label="Mobile Navigation">
        {NAV_ITEMS.slice(0, 5).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `mobile-tab-btn ${isActive ? "active" : ""}`}
              end={item.path === "/"}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        <NavLink to="/chat" className={({ isActive }) => `mobile-tab-btn ${isActive ? "active" : ""}`}>
          <MessageSquare size={18} />
          <span>Ask</span>
        </NavLink>
        <NavLink to="/data" className={({ isActive }) => `mobile-tab-btn ${isActive ? "active" : ""}`}>
          <Database size={18} />
          <span>Data</span>
        </NavLink>
      </nav>
    </div>
  );
};
