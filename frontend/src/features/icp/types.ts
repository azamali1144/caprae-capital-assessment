// mirrors backend/app/schemas/icp_profile.py

export type IcpMode = "sales" | "acquisition";

export interface IcpRules {
  industries?: string[];
  countries?: string[];
  states?: string[];
  employee_min?: number | null;
  employee_max?: number | null;
  min_years_in_business?: number | null;
  tech_include?: string[];
  weights?: Record<string, number>;
}

export interface IcpProfile {
  id: string;
  name: string;
  mode: IcpMode;
  is_active: boolean;
  rules: IcpRules;
  created_at: string;
  updated_at: string;
}

export interface IcpProfileInput {
  name: string;
  mode: IcpMode;
  rules: IcpRules;
}
