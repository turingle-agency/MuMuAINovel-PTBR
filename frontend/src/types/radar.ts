export type ResearchStatus = 'pending' | 'running' | 'complete' | 'partial' | 'failed';
export type ProductType = 'lowticket' | 'fiction';
export type ResearchMode = 'manual' | 'weekly';
export type SourceStatus = 'ok' | 'empty' | 'not_configured' | 'unsupported' | 'budget_blocked' |
  'error' | 'partial' | 'not_applicable';
export type SourceName = 'firecrawl' | 'youtube' | 'trends' | 'amazon' | 'meta' | 'agent_reach' | 'apify';
export type SecretSource = Extract<SourceName, 'firecrawl' | 'youtube' | 'meta' | 'apify'>;

export interface PageParams { page?: number; page_size?: number }
export interface ResearchFilters extends PageParams {
  country?: string;
  product_type?: ProductType;
  mode?: ResearchMode;
  week_key?: string;
}
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export interface ResearchRequest {
  topic: string;
  country: string;
  product_type: ProductType;
  request_id: string;
}
export interface ResearchAccepted { id: string; status: ResearchStatus }
export interface ResearchListItem extends ResearchAccepted {
  topic: string;
  country: string | null;
  product_type: string | null;
  mode: ResearchMode | null;
  week_key: string | null;
  created_at: string | null;
  finished_at: string | null;
  legacy: boolean;
  score: number | null;
  direction_points: number | null;
  currency: string | null;
  amazon_average: string | null;
  amazon_count: number;
  kindle_category: string | null;
  kindle_best_rank: number | null;
  meta_ads_count: number | null;
  source_statuses: Record<string, SourceStatus>;
  citable_count: number;
}

export interface EvidenceItem {
  id: string;
  url: string | null;
  label: string;
  observed_date: string | null;
  kind: 'trend' | 'related' | 'book' | 'ad' | 'content';
  data: {
    excerpt: string | null;
    related_query: string | null;
    asin: string | null;
    category: string | null;
    rank: number | null;
    search_position: number | null;
    price: string | null;
    currency: string | null;
    price_kind: 'purchase' | 'subscription' | 'list' | null;
    format: 'kindle' | 'print' | 'other' | null;
    sponsored: boolean | null;
    active: boolean | null;
    commercial: boolean | null;
    started_at: string | null;
    value: number | null;
  };
}
export interface SourceResult {
  source: string;
  status: SourceStatus;
  scope: string;
  method_version: string;
  collected_at: string;
  from_cache: boolean;
  limits: { notes: string[]; sample_limit: number | null };
  items: EvidenceItem[];
}
export interface Weights { demand: number; competition: number; price: number }
export interface ResearchSnapshot {
  version: 1;
  input: {
    query: string;
    country: string;
    language: string;
    currency: string;
    category: string | null;
    start_date: string;
    end_date: string;
  } | null;
  writing_language: string;
  weights: Weights;
  price_reference: string | null;
  enabled_sources: string[];
  sources: Record<string, SourceResult>;
  progress: { done: number; total: number; current_source: string | null };
  score: {
    demand: number | null;
    competition: number | null;
    price: number | null;
    formula_version: number;
  } | null;
  summary: {
    status: 'skipped' | 'ok' | 'error';
    detail: string | null;
    items: Array<{ text: string; evidence_ids: string[] }>;
  };
}
export interface ResearchDetail extends ResearchListItem {
  snapshot: ResearchSnapshot | null;
  score_delta: number | null;
}
export interface BriefItem { id: string; status: string; created_at: string; research: ResearchListItem }
export interface BriefDetail extends BriefItem { research: ResearchDetail }
export interface MarketProfile {
  country: string;
  language: string;
  currency: string;
  active: boolean;
  sources: SourceName[];
  kindle_categories: Record<string, string>;
  price_references: Partial<Record<ProductType, string>>;
}
export interface RadarConfig {
  profiles: MarketProfile[];
  weights: Weights;
  schedule: {
    enabled: boolean;
    timezone: string;
    entries: Array<{ topic: string; country: string; product_type: ProductType }>;
  };
  budget: { monthly_limit_usd: string; threshold_percent: 80; per_run_limit_usd: '0.10' };
}
export interface Coverage { enabled: boolean; status: 'ready' | 'not_configured' | 'unsupported' | 'disabled'; detail: string }
export interface RadarSettingsView extends RadarConfig {
  encryption_available: boolean;
  credentials: Record<SecretSource, { present: boolean; usable: boolean }>;
  coverage: Record<string, Record<SourceName, Coverage>>;
}
export type SettingsPatch = Partial<RadarConfig> & { secrets?: Partial<Record<SecretSource, string | null>> };
export interface SourceCheck {
  source: SourceName;
  configured: boolean;
  access: 'ok' | 'error' | 'not_tested';
  last_status: SourceStatus | null;
  detail: string;
}
export interface BudgetView {
  month: string;
  limit_microusd: number;
  charged_microusd: number;
  reserved_microusd: number;
  committed_microusd: number;
  blocked: boolean;
  pending_count: number;
}
