import { getExternalScopeIdentity } from "./auth-scope";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

type RequestOptions = RequestInit & {
  token?: string | null;
};

async function parseResponse<T>(res: Response, label: string): Promise<T> {
  const text = await res.text();

  if (!res.ok) {
    throw new Error(`${label} failed: ${res.status}\n${text}`);
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return text as T;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const identity = getExternalScopeIdentity();
  if (identity.username) {
    headers.set("X-Auth-User", identity.username);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  return parseResponse<T>(res, path);
}

export type AccessScope = {
  username?: string | null;
  display_name?: string | null;
  role: string;
  accessible_plantations: string[];
  accessible_estates: string[];
  resolved_estate?: string | null;
  access_mode: string;
  access_message?: string | null;
  source?: string;
};

export type DashboardStatus = {
  has_dataset: boolean;
  selected_month?: string | null;
  month_label?: string;
  row_count?: number;
  regions?: string[];
  plantations?: string[];
  estates?: string[];
  divisions?: string[];
  uploaded_months?: {
    selected_month: string;
    available_regions: string[];
    uploaded_at?: string;
    row_count?: number;
  }[];
  active_report?: ReportResponse | null;
  access?: AccessScope;
};

export type FilterOptions = {
  plantations: string[];
  regions: string[];
  estates: string[];
  years: string[];
  metrics: { value: string; label: string }[];
  benchmarks: { value: string; label: string }[];
  divisions: {
    division_key: string;
    plantation: string;
    region: string;
    estate: string;
    division: string;
    code: string;
  }[];
};

export type QueryRow = {
  plantation: string;
  plantation_label?: string;
  region: string;
  region_label?: string;
  estate: string;
  division: string;
  division_key: string;
  code: string;
  year?: string;
  year_label?: string;
  value?: number;
  metric?: string;
  metric_label?: string;
  average_rounds?: number;
  bush_count?: number;
  regional_average?: number;
  benchmark?: number;
  map_url?: string;
};

export type QueryResponse = {
  selected_month?: string;
  mode: string;
  answer: string;
  rows: QueryRow[];
  metric: string;
  question?: string;
  inferred?: Record<string, string | number | null>;
  access?: AccessScope;
};

export type EstateSummary = {
  plantation: string;
  plantation_label?: string;
  region: string;
  region_label?: string;
  estate: string;
  year: string;
  estate_extent: number;
  estate_yield: number;
  regional_average: number;
  benchmark: number;
  estate_percentage: number;
  divisional_yield?: number;
  divisional_extend?: number;
  divisional_percentage?: number;
};

export type RegionSummary = {
  region: string;
  region_label?: string;
  year: string;
  regional_average: number;
  benchmark: number;
};

export type ChartResponse = {
  title: string;
  metric: string;
  metric_label: string;
  bars: { label: string; value: number; highlight: boolean }[];
  reference?: { benchmark?: number; regional_average?: number };
  focus_label?: string;
};

export type LoginResponse = {
  authenticated: boolean;
  token: string;
  username: string;
  expires_at: string;
};

export type UploadResponse = {
  message: string;
  selected_month: string;
  regions: string[];
  validation: Record<string, {
    missing_columns: string[];
    region_issues: string[];
    row_count: number;
    columns: string[];
    detected_month: string;
    filename: string;
    mapping_file_used?: string | null;
    mapping_rows?: number;
    mapped_code_count?: number;
    mapping_warning?: string;
  }>;
  dashboard_stats: {
    row_count: number;
    region_count: number;
    estate_count: number;
    division_count: number;
    year_count: number;
  };
};

export type ReportResponse = {
  message: string;
  selected_month: string;
  output_mode: string;
  run_dir: string;
  regions: string[];
  downloads: {
    excel: string;
    pdf: string;
    zip: string;
  };
  preview_images: string[];
  preview_images_png: string[];
  preview_images_svg: string[];
  manifest: string;
  region_outputs: {
    region: string;
    template_id: string;
    company: string;
    assets: {
      title: string;
      kind: string;
      png: string;
      jpg: string;
      svg: string;
      page_png: string;
    }[];
    downloads?: { pdf: string };
  }[];
};

export type QueryFilters = {
  plantation: string;
  region: string;
  estate: string;
  division: string;
  year: string;
  metric: string;
  operator: string;
  value: string;
  rankDir: string;
  count: string;
  benchmarkMetric: string;
};

export async function loginAdmin(username: string, password: string) {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export async function fetchMe(token: string) {
  return request<{ authenticated: boolean; username: string; expires_at: string }>("/auth/me", {
    token,
  });
}

export async function logoutAdmin(token: string) {
  return request<{ authenticated: boolean }>("/auth/logout", {
    method: "POST",
    token,
  });
}

export async function getDashboardStatus() {
  return request<DashboardStatus>("/dashboard/status");
}

export async function getDashboardOptions() {
  return request<{ selected_month: string; options: FilterOptions; access: AccessScope }>("/dashboard/options");
}

function buildQueryString(filters: Partial<QueryFilters>) {
  const params = new URLSearchParams();
  if (filters.plantation) params.set("plantation", filters.plantation);
  if (filters.region) params.set("region", filters.region);
  if (filters.estate) params.set("estate", filters.estate);
  if (filters.division) params.set("division", filters.division);
  if (filters.year) params.set("year", filters.year);
  if (filters.metric) params.set("metric", filters.metric);
  if (filters.operator) params.set("operator", filters.operator);
  if (filters.value) params.set("value", filters.value);
  if (filters.rankDir) params.set("rank_dir", filters.rankDir);
  if (filters.count) params.set("count", filters.count);
  if (filters.benchmarkMetric) params.set("benchmark_metric", filters.benchmarkMetric);
  return params.toString();
}

export async function runDashboardQuery(filters: Partial<QueryFilters>) {
  const qs = buildQueryString(filters);
  return request<QueryResponse>(`/dashboard/query${qs ? `?${qs}` : ""}`);
}

export async function askDashboardQuestion(question: string) {
  const params = new URLSearchParams({ question });
  return request<QueryResponse>(`/dashboard/ask?${params.toString()}`);
}

export async function getEstateSummary(params: {
  plantation: string;
  estate: string;
  year: string;
  division?: string;
}) {
  const query = new URLSearchParams({
    plantation: params.plantation,
    estate: params.estate,
    year: params.year,
  });
  if (params.division) query.set("division", params.division);
  return request<EstateSummary>(`/dashboard/estate-summary?${query.toString()}`);
}

export async function getRegionSummary(params: { region: string; year: string }) {
  const query = new URLSearchParams(params);
  return request<RegionSummary>(`/dashboard/region-summary?${query.toString()}`);
}

export async function getChart(params: {
  region: string;
  year: string;
  metric: string;
  focusEstate?: string;
  focusDivision?: string;
}) {
  const query = new URLSearchParams({
    region: params.region,
    year: params.year,
    metric: params.metric,
  });
  if (params.focusEstate) query.set("focus_estate", params.focusEstate);
  if (params.focusDivision) query.set("focus_division", params.focusDivision);
  return request<ChartResponse>(`/dashboard/chart?${query.toString()}`);
}

export async function uploadMonthlyDatasets(token: string, files: File[]) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  return request<UploadResponse>("/upload/monthly-datasets", {
    method: "POST",
    body: formData,
    token,
  });
}

export async function generateReports(token: string, selectedMonth: string, outputMode: string) {
  return request<ReportResponse>("/reports/generate", {
    method: "POST",
    token,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_month: selectedMonth,
      output_mode: outputMode,
    }),
  });
}

export async function getLatestPackage() {
  return request<ReportResponse>("/download/package");
}

export function buildExportCsvUrl(filters: Partial<QueryFilters>) {
  const qs = buildQueryString(filters);
  const identity = typeof window !== "undefined" ? getExternalScopeIdentity() : { username: null };
  const params = new URLSearchParams(qs);
  if (identity.username) {
    params.set("username", identity.username);
  }
  const finalQs = params.toString();
  return `${API_BASE}/dashboard/export.csv${finalQs ? `?${finalQs}` : ""}`;
}

export function mediaUrl(path: string) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path}`;
}
