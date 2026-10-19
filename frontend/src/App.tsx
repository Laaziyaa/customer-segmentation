import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./api/client";
import { Layout } from "./components/Layout";
import { CardSkeleton } from "./components/Skeleton";

// Route-level code splitting for performance and small initial bundle
const OverviewPage = lazy(() =>
  import("./pages/OverviewPage").then((m) => ({ default: m.OverviewPage }))
);
const CustomersPage = lazy(() =>
  import("./pages/CustomersPage").then((m) => ({ default: m.CustomersPage }))
);
const SegmentsPage = lazy(() =>
  import("./pages/SegmentsPage").then((m) => ({ default: m.SegmentsPage }))
);
const PredictPage = lazy(() =>
  import("./pages/PredictPage").then((m) => ({ default: m.PredictPage }))
);
const EvaluationPage = lazy(() =>
  import("./pages/EvaluationPage").then((m) => ({ default: m.EvaluationPage }))
);
const EdaPage = lazy(() =>
  import("./pages/EdaPage").then((m) => ({ default: m.EdaPage }))
);
const AssistantPage = lazy(() =>
  import("./pages/AssistantPage").then((m) => ({ default: m.AssistantPage }))
);
const DataPage = lazy(() =>
  import("./pages/DataPage").then((m) => ({ default: m.DataPage }))
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route
              index
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <OverviewPage />
                </Suspense>
              }
            />
            <Route
              path="customers"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <CustomersPage />
                </Suspense>
              }
            />
            <Route
              path="segments"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <SegmentsPage />
                </Suspense>
              }
            />
            <Route
              path="predict"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <PredictPage />
                </Suspense>
              }
            />
            <Route
              path="evaluation"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <EvaluationPage />
                </Suspense>
              }
            />
            <Route
              path="eda"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <EdaPage />
                </Suspense>
              }
            />
            <Route
              path="chat"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <AssistantPage />
                </Suspense>
              }
            />
            <Route
              path="data"
              element={
                <Suspense fallback={<CardSkeleton />}>
                  <DataPage />
                </Suspense>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
