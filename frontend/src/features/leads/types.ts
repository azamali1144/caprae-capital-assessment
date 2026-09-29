// mirrors backend/app/schemas/company.py + common.py

export type Grade = "A" | "B" | "C" | "D";
export type Stage = "new" | "qualified" | "contacted" | "disqualified";
export type EmailStatus = "valid_mx" | "no_mx" | "invalid_syntax" | "disposable" | "unknown";
export type WebsiteStatus = "alive" | "dead" | "blocked" | "timeout";

export const GRADES: Grade[] = ["A", "B", "C", "D"];
export const STAGES: Stage[] = ["new", "qualified", "contacted", "disqualified"];

export interface Contact {
  id: string;
  full_name: string | null;
  title: string | null;
  email: string | null;
  email_status: EmailStatus;
  email_type: "personal" | "role" | null;
  phone_e164: string | null;
  phone_valid: boolean;
  linkedin_url: string | null;
  is_decision_maker: boolean;
  source: string;
}

export interface ScoreItem {
  rule: string;
  points: number;
  reason: string;
}

export interface Lead {
  id: string;
  name: string;
  domain: string | null;
  website_url: string | null;
  industry: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  employee_count: number | null;
  score: number | null;
  grade: Grade | null;
  stage: Stage;
  website_status: WebsiteStatus | null;
  last_enriched_at: string | null;
  created_at: string;
  best_contact: Contact | null;
  contacts_count: number;
  top_reasons: string[];
}

export interface LeadDetail extends Lead {
  description: string | null;
  founded_year: number | null;
  copyright_year: number | null;
  revenue_estimate: number | null;
  tech_stack: string[];
  socials: Partial<Record<"linkedin" | "facebook" | "instagram" | "x" | "youtube", string>>;
  signals: {
    has_ssl?: boolean;
    hiring?: boolean;
    hiring_evidence?: string[];
    modern_stack?: boolean;
    family_owned?: boolean;
    family_owned_hint?: string | null;
    pages_crawled?: string[];
  };
  score_breakdown: ScoreItem[];
  notes: string | null;
  source: string;
  import_job_id: string | null;
  contacts: Contact[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeadFilters {
  q?: string;
  grade?: Grade[];
  min_score?: number;
  industry?: string;
  country?: string;
  stage?: Stage;
  email_status?: EmailStatus;
  import?: string;
  sort?: "score" | "name" | "created_at" | "last_enriched_at" | "employee_count" | "founded_year";
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export type BulkAction =
  | { ids: string[]; action: "set_stage"; value: Stage }
  | { ids: string[]; action: "re_enrich" | "delete" };
