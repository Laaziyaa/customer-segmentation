import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, ChevronLeft, ChevronRight, SlidersHorizontal, ArrowUpDown } from "lucide-react";
import { api } from "../api/client";
import type { CustomerItem, CustomerDetailResponse } from "../api/types";
import { CustomerDrawer } from "../components/CustomerDrawer";
import { TableSkeleton } from "../components/Skeleton";
import { StatusNotice } from "../components/StatusNotice";
import { getSegmentColor } from "../components/Charts";

export const CustomersPage: React.FC = () => {
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(15);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [selectedSegment, setSelectedSegment] = useState<string>("");
  const [minAge, setMinAge] = useState<string>("");
  const [maxAge, setMaxAge] = useState<string>("");
  const [minBalance, setMinBalance] = useState<string>("");
  const [maxBalance, setMaxBalance] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("customer_id");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  // Selected customer for side drawer
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);

  // Debounce search input
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchTerm(val);
    setPage(1);
    const timeout = setTimeout(() => {
      setDebouncedSearch(val);
    }, 300);
    return () => clearTimeout(timeout);
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [
      "customers",
      page,
      pageSize,
      debouncedSearch,
      selectedSegment,
      minAge,
      maxAge,
      minBalance,
      maxBalance,
      sortBy,
      sortDir,
    ],
    queryFn: () =>
      api.getCustomers({
        page,
        page_size: pageSize,
        search: debouncedSearch || undefined,
        segment: selectedSegment !== "" ? Number(selectedSegment) : undefined,
        min_age: minAge ? Number(minAge) : undefined,
        max_age: maxAge ? Number(maxAge) : undefined,
        min_balance: minBalance ? Number(minBalance) : undefined,
        max_balance: maxBalance ? Number(maxBalance) : undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
  });

  // Query customer details for the side drawer
  const { data: customerDetail, isLoading: isDetailLoading } = useQuery({
    queryKey: ["customerDetail", selectedCustomerId],
    queryFn: () => api.getCustomerDetail(selectedCustomerId!),
    enabled: selectedCustomerId !== null,
  });

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortDir("asc");
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Customers</h1>
        <p className="page-desc">
          Browse customer records, filter by financial criteria, and inspect individual cluster assignments.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="card"
        style={{
          marginBottom: "20px",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
          {/* Search */}
          <div style={{ position: "relative", flex: "1 1 240px", minWidth: "200px" }}>
            <Search
              size={15}
              style={{
                position: "absolute",
                left: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              placeholder="Search by ID, job, education..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="form-input"
              style={{ paddingLeft: "32px", width: "100%" }}
            />
          </div>

          {/* Segment Filter */}
          <select
            value={selectedSegment}
            onChange={(e) => {
              setSelectedSegment(e.target.value);
              setPage(1);
            }}
            className="form-select"
            style={{ minWidth: "150px" }}
          >
            <option value="">All Segments</option>
            <option value="0">Segment 0</option>
            <option value="1">Segment 1</option>
            <option value="2">Segment 2</option>
            <option value="3">Segment 3</option>
          </select>

          {/* Age range */}
          <input
            type="number"
            placeholder="Min Age"
            value={minAge}
            onChange={(e) => {
              setMinAge(e.target.value);
              setPage(1);
            }}
            className="form-input"
            style={{ width: "95px" }}
          />
          <input
            type="number"
            placeholder="Max Age"
            value={maxAge}
            onChange={(e) => {
              setMaxAge(e.target.value);
              setPage(1);
            }}
            className="form-input"
            style={{ width: "95px" }}
          />

          {/* Balance range */}
          <input
            type="number"
            placeholder="Min Balance ($)"
            value={minBalance}
            onChange={(e) => {
              setMinBalance(e.target.value);
              setPage(1);
            }}
            className="form-input"
            style={{ width: "130px" }}
          />
          <input
            type="number"
            placeholder="Max Balance ($)"
            value={maxBalance}
            onChange={(e) => {
              setMaxBalance(e.target.value);
              setPage(1);
            }}
            className="form-input"
            style={{ width: "130px" }}
          />

          {(selectedSegment || minAge || maxAge || minBalance || maxBalance || searchTerm) && (
            <button
              onClick={() => {
                setSelectedSegment("");
                setMinAge("");
                setMaxAge("");
                setMinBalance("");
                setMaxBalance("");
                setSearchTerm("");
                setDebouncedSearch("");
                setPage(1);
              }}
              className="btn btn-secondary"
              style={{ fontSize: "12px", padding: "6px 12px" }}
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Main Table / State Render */}
      {isLoading ? (
        <TableSkeleton rows={12} columns={7} />
      ) : isError || !data ? (
        <StatusNotice
          type="error"
          title="Could not load customer records"
          message="Server error while retrieving customers. Try refreshing the page."
          actionText="Retry"
          onAction={() => refetch()}
        />
      ) : data.items.length === 0 ? (
        <div className="card" style={{ padding: "40px 20px", textAlign: "center" }}>
          <div style={{ color: "var(--text-main)", fontWeight: 600, fontSize: "15px" }}>
            No customers match these filters.
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Try widening your age, balance range, or clearing the search keyword.
          </div>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table" aria-label="Customer accounts table">
              <thead>
                <tr>
                  <th onClick={() => handleSort("customer_id")} style={{ cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      ID <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th>Segment</th>
                  <th onClick={() => handleSort("age")} style={{ cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      Age <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th>Job</th>
                  <th onClick={() => handleSort("annual_income")} style={{ cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      Annual Income <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th onClick={() => handleSort("account_balance")} style={{ cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      Balance <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th onClick={() => handleSort("credit_score")} style={{ cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      Credit Score <ArrowUpDown size={12} />
                    </div>
                  </th>
                  <th>Digital Score</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c: CustomerItem) => {
                  const segColor = getSegmentColor(c.cluster);
                  return (
                    <tr
                      key={c.customer_id}
                      onClick={() => setSelectedCustomerId(c.customer_id)}
                      title="Click to view details and explainability"
                    >
                      <td>
                        <strong>#{c.customer_id}</strong>
                      </td>
                      <td>
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            padding: "2px 8px",
                            borderRadius: "var(--radius-sm)",
                            fontSize: "12px",
                            backgroundColor: "var(--bg-subtle)",
                            border: `1px solid var(--border)`,
                          }}
                        >
                          <span
                            style={{
                              width: "7px",
                              height: "7px",
                              borderRadius: "50%",
                              backgroundColor: segColor,
                            }}
                          />
                          Segment {c.cluster}
                        </span>
                      </td>
                      <td>{c.age}</td>
                      <td style={{ textTransform: "capitalize" }}>{c.job || "—"}</td>
                      <td style={{ fontFeatureSettings: "tnum" }}>
                        ${Number(c.annual_income || 0).toLocaleString()}
                      </td>
                      <td style={{ fontFeatureSettings: "tnum" }}>
                        ${Number(c.account_balance || 0).toLocaleString()}
                      </td>
                      <td style={{ fontFeatureSettings: "tnum" }}>{c.credit_score || "—"}</td>
                      <td>{c.digital_banking_score ?? "—"}/100</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginTop: "16px",
              fontSize: "13px",
              color: "var(--text-muted)",
            }}
          >
            <div>
              Showing <strong>{((page - 1) * pageSize + 1).toLocaleString()}</strong> to{" "}
              <strong>{Math.min(page * pageSize, data.total).toLocaleString()}</strong> of{" "}
              <strong>{data.total.toLocaleString()}</strong> customers
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="btn btn-secondary"
                style={{ padding: "6px 10px" }}
                aria-label="Previous page"
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <span style={{ padding: "0 8px" }}>
                Page {page} of {data.total_pages}
              </span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="btn btn-secondary"
                style={{ padding: "6px 10px" }}
                aria-label="Next page"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Slide-out Customer Details Drawer */}
      <CustomerDrawer
        customerDetail={customerDetail || null}
        isLoading={isDetailLoading}
        onClose={() => setSelectedCustomerId(null)}
      />
    </div>
  );
};
