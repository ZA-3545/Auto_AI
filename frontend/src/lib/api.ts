/** Public Railway API — used when Vercel builds without NEXT_PUBLIC_API_URL. */
const PRODUCTION_API_URL = "https://autoai-production-e6a4.up.railway.app";

function resolveApiUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (process.env.NODE_ENV === "production") return PRODUCTION_API_URL;
  return "http://localhost:8000";
}

const API_URL = resolveApiUrl();

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
};

export type Vehicle = {
  id: number;
  make: string;
  model: string;
  year: number;
  price: number;
  city: string;
  condition: string;
  transmission: string;
  body_type: string;
  fuel_type: string;
  engine_capacity: number | null;
  mileage_km: number;
  fuel_average_kmpl: number | null;
  resale_rating: number;
  created_at: string;
};

export type VehicleSearchResponse = {
  total: number;
  limit: number;
  offset: number;
  items: Vehicle[];
};

export type VehicleSearchParams = {
  budget_min?: number;
  budget_max?: number;
  city?: string;
  condition?: string;
  transmission?: string;
  body_type?: string;
  fuel_type?: string;
  fuel_priority?: boolean;
  sort_by?: "price" | "year" | "mileage";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function searchVehicles(
  params: VehicleSearchParams = {},
): Promise<VehicleSearchResponse> {
  const query = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    query.set(key, String(value));
  }

  const response = await fetch(`${API_URL}/api/vehicles/search?${query}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Vehicle search failed with status ${response.status}`);
  }

  return response.json() as Promise<VehicleSearchResponse>;
}

export async function fetchVehicleById(id: number): Promise<Vehicle> {
  const response = await fetch(`${API_URL}/api/vehicles/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Vehicle lookup failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  return response.json() as Promise<Vehicle>;
}

export type ExtractedRequirements = {
  budget_min: number | null;
  budget_max: number | null;
  city: string | null;
  condition: "new" | "used" | null;
  transmission: "automatic" | "manual" | null;
  body_type: string | null;
  purpose: string | null;
  fuel_priority: boolean | null;
  resale_priority: boolean | null;
  needs_clarification: boolean;
  clarification_question: string | null;
};

export type ExtractResponse = {
  requirements: ExtractedRequirements;
  provider: string;
  model: string;
  conversation_id?: string | null;
  turn_requirements?: ExtractedRequirements | null;
  reset?: boolean;
};

const CONVERSATION_STORAGE_KEY = "autoai_conversation_id";

export function getStoredConversationId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(CONVERSATION_STORAGE_KEY);
}

export function setStoredConversationId(id: string | null): void {
  if (typeof window === "undefined") return;
  if (id) window.localStorage.setItem(CONVERSATION_STORAGE_KEY, id);
  else window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
}

export async function extractRequirements(
  message: string,
  options?: { conversationId?: string | null; reset?: boolean },
): Promise<ExtractResponse> {
  const response = await fetch(`${API_URL}/api/chat/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: options?.conversationId ?? undefined,
      reset: options?.reset ?? false,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Extraction failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  const data = (await response.json()) as ExtractResponse;
  if (data.conversation_id) {
    setStoredConversationId(data.conversation_id);
  }
  return data;
}

export async function resetConversation(
  conversationId: string,
): Promise<{ conversation_id: string; requirements: ExtractedRequirements }> {
  const response = await fetch(`${API_URL}/api/chat/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Reset failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  return response.json();
}

export type FactorScores = {
  budget_fit: number;
  purpose_suitability: number;
  fuel_economy: number;
  resale: number;
  mileage_condition: number;
};

export type RecommendedVehicle = {
  vehicle: Vehicle;
  match_score: number;
  factor_scores: FactorScores;
  explanation: string;
};

export type RecommendResponse = {
  total_candidates: number;
  requirements: ExtractedRequirements;
  items: RecommendedVehicle[];
};

export async function recommendVehicles(
  requirements: ExtractedRequirements,
  limit = 20,
): Promise<RecommendResponse> {
  const response = await fetch(`${API_URL}/api/vehicles/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ requirements, limit }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Recommendation failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  return response.json() as Promise<RecommendResponse>;
}

export type FactorValue = {
  vehicle_id: number;
  display: string;
  numeric: number | null;
};

export type FactorComparison = {
  factor: string;
  reliability: "fact" | "inference" | "unknown";
  values: FactorValue[];
  winner_vehicle_id: number | null;
  note: string | null;
};

export type BestForConclusion = {
  category: string;
  vehicle_id: number;
  vehicle_label: string;
  reason: string;
};

export type CompareResponse = {
  vehicles: Vehicle[];
  factors: FactorComparison[];
  best_for: BestForConclusion[];
  best_overall: BestForConclusion;
  narrative: string | null;
  narrative_source: string;
};

export async function compareVehicles(
  vehicleIds: number[],
  requirements: ExtractedRequirements,
  includeNarrative = true,
): Promise<CompareResponse> {
  const response = await fetch(`${API_URL}/api/vehicles/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      vehicle_ids: vehicleIds,
      requirements,
      include_narrative: includeNarrative,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Comparison failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  return response.json() as Promise<CompareResponse>;
}

export type DataReliability = "fact" | "inference" | "unknown";

export type ExtractedListing = {
  make: string | null;
  model: string | null;
  variant: string | null;
  year: number | null;
  asking_price: number | null;
  mileage_km: number | null;
  location: string | null;
  transmission: string | null;
  fuel_type: string | null;
  condition: string | null;
  engine_capacity: number | null;
  color: string | null;
  ownership_text: string | null;
  accident_text: string | null;
  service_history_text: string | null;
  other_details: string | null;
  claims_accident_free: boolean;
  claims_original_paint: boolean;
  claims_service_history: boolean;
  mentions_owners: boolean;
};

export type LabeledClaim = {
  text: string;
  reliability: DataReliability;
  category: string;
};

export type PriceAssessment = {
  relative: "higher" | "in_line" | "lower" | "insufficient_data";
  summary: string;
  reliability: DataReliability;
  dataset_disclaimer: string;
  asking_price: number | null;
  reference_median: number | null;
  reference_count: number;
  reference_min: number | null;
  reference_max: number | null;
  similar_vehicle_ids: number[];
};

export type AnalyzeListingResponse = {
  extracted: ExtractedListing;
  price_assessment: PriceAssessment;
  red_flags: LabeledClaim[];
  missing_information: LabeledClaim[];
  notes: LabeledClaim[];
  seller_questions: string[];
  advisor_summary: string | null;
  advisor_summary_source: string;
  provider: string;
  model: string;
};

export async function analyzeListing(
  listingText: string,
  includeAdvisorSummary = true,
): Promise<AnalyzeListingResponse> {
  const response = await fetch(`${API_URL}/api/listings/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      listing_text: listingText,
      include_advisor_summary: includeAdvisorSummary,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Listing analysis failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  return response.json() as Promise<AnalyzeListingResponse>;
}

export type RetrievedChunk = {
  id: number;
  source_id: string;
  title: string;
  content: string;
  similarity: number;
  chunk_index: number;
};

export type KnowledgeAskResponse = {
  question: string;
  answer: string;
  grounded: boolean;
  chunks: RetrievedChunk[];
  disclaimer: string;
  provider: string | null;
  model: string | null;
};

export async function askKnowledgeQuestion(
  question: string,
): Promise<KnowledgeAskResponse> {
  const response = await fetch(`${API_URL}/api/knowledge/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Knowledge ask failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  return response.json() as Promise<KnowledgeAskResponse>;
}

export type AdviceAskResponse = {
  question: string;
  answer: string;
  grounded: boolean;
  chunks: RetrievedChunk[];
  disclaimer: string;
  provider: string | null;
  model: string | null;
};

export async function askBuyingAdvice(
  question: string,
): Promise<AdviceAskResponse> {
  const response = await fetch(`${API_URL}/api/advice/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Buying advice failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  return response.json() as Promise<AdviceAskResponse>;
}

export type MaintenanceItem = {
  category: string;
  item: string;
  reason: string;
  source: "rule" | "knowledge";
  reliability: DataReliability;
};

export type VehicleProfile = {
  make: string | null;
  model: string | null;
  year: number | null;
  mileage_km: number | null;
  vehicle_id: number | null;
  source: "database" | "extracted";
};

export type KnowledgeExcerpt = {
  title: string;
  content: string;
  similarity: number;
};

export type MaintenanceResponse = {
  vehicle: VehicleProfile;
  checklist: MaintenanceItem[];
  knowledge_excerpts: KnowledgeExcerpt[];
  disclaimer: string;
  extraction_provider: string | null;
  extraction_model: string | null;
};

export type MaintenanceRequest =
  | { vehicle_id: number; description?: undefined }
  | { description: string; vehicle_id?: undefined };

export async function fetchMaintenanceChecklist(
  body: MaintenanceRequest,
): Promise<MaintenanceResponse> {
  const response = await fetch(`${API_URL}/api/vehicles/maintenance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Maintenance checklist failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  return response.json() as Promise<MaintenanceResponse>;
}

export { API_URL };

export type MetricStatus = "computed" | "not_available" | "manual";

export type MetricCard = {
  id: string;
  label: string;
  status: MetricStatus;
  value?: string | number | null;
  unit?: string | null;
  detail?: string | null;
  note?: string | null;
};

export type EndpointLatencyRow = {
  path: string;
  request_count: number;
  error_count: number;
  avg_latency_ms?: number | null;
  p95_latency_ms?: number | null;
};

export type AdminMetricsResponse = {
  generated_at: string;
  disclaimer: string;
  metrics: MetricCard[];
  endpoint_latency: EndpointLatencyRow[];
  llm_by_operation: Record<string, number>;
  conversations_with_llm_cost: number;
};

export async function fetchAdminMetrics(): Promise<AdminMetricsResponse> {
  const response = await fetch(`${API_URL}/api/admin/metrics`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Metrics failed with status ${response.status}`);
  }
  return response.json() as Promise<AdminMetricsResponse>;
}
