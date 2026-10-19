/**
 * Complete TypeScript type definitions matching backend API contracts.
 */

export interface HealthResponse {
  status: string;
  message: string;
  version: string;
  active_dataset_id: string;
  total_customers: number;
  total_segments: number;
  last_updated: string;
}

export interface SchemaField {
  name: string;
  label: string;
  type: "number" | "select";
  min?: number;
  max?: number;
  default: number | string;
  options?: string[];
  mean?: number;
  std?: number;
  is_synthetic: boolean;
}

export interface DatasetSchemaResponse {
  dataset_id: string;
  total_rows: number;
  total_features: number;
  fields: SchemaField[];
  categorical_options: Record<string, string[]>;
  synthetic_columns: string[];
}

export interface SegmentItem {
  cluster: number;
  persona: string;
  customers: number;
  percentage: number;
  summary: string;
  average_income: number;
  average_balance: number;
  average_credit_score: number;
  average_digital_score: number;
  average_transactions: number;
  average_investment: number;
  average_products: number;
  recommended_products: string[];
}

export interface SegmentsResponse {
  total_customers: number;
  number_of_segments: number;
  last_updated: string;
  segments: SegmentItem[];
}

export interface CustomerItem {
  customer_id: number;
  cluster: number;
  persona?: string;
  age: number;
  job?: string;
  marital?: string;
  education?: string;
  housing?: string;
  loan?: string;
  annual_income?: number;
  credit_score?: number;
  account_balance?: number;
  digital_banking_score?: number;
  monthly_transactions?: number;
  investment_amount?: number;
  account_tenure?: number;
  number_of_products?: number;
  [key: string]: any;
}

export interface CustomersListResponse {
  items: CustomerItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FeatureComparison {
  feature: string;
  label: string;
  customer_value: string;
  cluster_average: string;
  direction: string;
  diff_pct: number;
  sentence: string;
}

export interface CustomerDetailResponse {
  customer: CustomerItem;
  cluster: number;
  persona: string;
  recommendations: string[];
  explanation: FeatureComparison[];
}

export interface RecommendationItem {
  title: string;
  category: string;
  reason: string;
}

export interface PredictResponse {
  predicted_cluster: number;
  persona: string;
  confidence: number;
  reasons: string[];
  recommendations: RecommendationItem[];
  warnings: string[];
  input_values: Record<string, any>;
}

export interface CurvePoint {
  k: number;
  inertia?: number;
  score?: number;
}

export interface ModelEvaluationResponse {
  silhouette: number;
  davies_bouldin: number;
  calinski_harabasz: number;
  optimal_k: number;
  stability_score: number;
  elbow_curve: CurvePoint[];
  silhouette_curve: CurvePoint[];
  metrics_explanation: Record<string, string>;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  label: string;
  count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface EDADistributionResponse {
  metric: "distributions";
  column: string;
  label: string;
  type: "numeric" | "categorical";
  count: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  bins?: HistogramBin[];
  categories?: CategoryCount[];
  is_synthetic: boolean;
}

export interface EDAMissingResponse {
  metric: "missing";
  total_rows: number;
  columns: Array<{
    column: string;
    missing_count: number;
    missing_pct: number;
  }>;
}

export interface EDACorrelationRow {
  feature: string;
  label: string;
  values: Record<string, number>;
}

export interface EDACorrelationResponse {
  metric: "correlations";
  features: string[];
  matrix: EDACorrelationRow[];
}

export interface EDAOverviewResponse {
  metric: "overview";
  total_rows: number;
  total_columns: number;
  numerical_columns: number;
  categorical_columns: number;
  clusters_count: number;
  synthetic_columns_count: number;
}

export type EDAResponse =
  | EDADistributionResponse
  | EDAMissingResponse
  | EDACorrelationResponse
  | EDAOverviewResponse;

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  execution_plan?: string[];
  results?: any;
  timestamp: string;
}

export interface ChatResponse {
  response: string;
  execution_plan: string[];
  results: any;
}

export interface ChatStatusResponse {
  configured: boolean;
  active_mode: "groq" | "rule_based";
  provider: string;
  model: string;
  message: string;
}

export interface KeyActionResponse {
  success: boolean;
  message: string;
}

export interface UploadResponse {
  dataset_id: string;
  filename: string;
  sample_rows: number;
  total_columns: number;
  detected_numerical: string[];
  detected_categorical: string[];
  suggested_k: number;
  message: string;
}

export interface PipelineStatusResponse {
  job_id: string;
  status: "running" | "completed" | "failed" | "unknown";
  progress: number;
  message: string;
  started_at?: string;
}

export interface DatasetResetResponse {
  success: boolean;
  message: string;
  total_rows: number;
}
