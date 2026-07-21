/** Types mirroring the Python pipeline's output schema.
 *  Source of truth: src/engine.py (decide, affordability_assess, rule_score)
 *  and src/run_pipeline.py. Keep in step with src/webdata.py. */

export type Verdict = 'green' | 'yellow' | 'red'
export type AffordVerdict = 'pass' | 'strain' | 'fail'
export type IndicatorStatus = AffordVerdict
export type Tier = 'low' | 'moderate' | 'elevated' | 'high'

export interface AffordIndicator {
  label: string
  value: string
  status: IndicatorStatus
  detail: string
}

export interface Affordability {
  verdict: AffordVerdict
  label: 'AFFORDABLE' | 'STRAINED' | 'NOT JUSTIFIED'
  premium: number
  premium_monthly: number
  /** premium as a share of gross income */
  pti: number
  /** monthly disposable income left after expenses and premium */
  disposable: number
  /** (requested + existing cover) ÷ income */
  cov_mult: number
  /** age-banded ceiling on cov_mult */
  cov_cap: number
  /** debt service as a share of net monthly income */
  dsr: number
  indicators: AffordIndicator[]
  reasons: string[]
}

export interface Conflict {
  type: string
  severity: 'major' | 'minor'
  description: string
}

/** [factor name, observed value, points contributed] */
export type RuleFactor = [string, string, number]

export interface Extraction {
  form_dob?: string
  name?: string
  form_income?: number
  form_debt?: number
  form_tobacco_yes?: boolean
  conditions_yes?: boolean
  family_history_yes?: boolean
  conditions_detail?: string
  payslip_name?: string
  payslip_income?: number
  employment_status?: string
  paramed_dob?: string
  height_cm?: number
  weight_kg?: number
  blood_pressure?: string
  cholesterol?: number
  cotinine?: string
  bureau_debt?: number
  bank_deposit_monthly?: number
  bank_outflow_monthly?: number
  bank_closing_balance?: number
  tax_income?: number
  tax_year?: string
}

export interface Case {
  id: string
  name: string
  sex: 'M' | 'F'
  age: number
  dob: string
  city: string
  state: string
  occupation: string
  employer: string
  emp_status: string
  years_emp: number

  income: number
  net_worth: number
  debt: number
  expenses: number
  bank: number
  credit: number
  dti: number

  policy: string
  coverage: number
  existing_cov: number
  replacing: number
  premium: number

  height: number
  weight: number
  bmi: number
  smoker: string
  conditions: string
  family: number
  bp: string
  chol: number
  hazard: string
  violations: number
  alcohol: string
  decl: Record<string, number>
  unique: string | null

  /** blended event probability learned from public datasets */
  ext_prior: number
  /** Framingham office-based general-CVD model */
  pub_prior: number

  afford: Affordability
  label: number
  rule_score: number
  rule_factors: RuleFactor[]
  ml_score: number
  ml_score_lr: number

  has_docs: boolean
  /** null for the cases scored from structured data alone — only a subset of
   *  the book has a rendered PDF packet to extract from */
  extraction: Extraction | null
  conflicts: Conflict[]
  injected?: string | null

  decision: 'APPROVE' | 'MANUAL REVIEW' | 'DECLINE'
  rate_class: string
  verdict: Verdict
  risk_score: number
  tier: Tier
  reasons: string[]
  referred: boolean

  /** referral routing — set only on MANUAL REVIEW cases; null when auto-decided */
  difficulty: number | null
  difficulty_drivers: string[]
  assigned_desk: Desk | null

  /** the narrative the underwriter reads first — LLM-written when the pipeline
   *  ran with a key, deterministic template otherwise */
  ai_summary: string
}

/** which underwriter desk a referred case routes to, by difficulty */
export type Desk = 'senior' | 'review' | 'analyst'

export interface DatasetCard {
  name: string
  rows: number
  features: string[]
  auc: number
  event_rate: number
  included_in_prior: boolean
  source: string
  cached: boolean
}

export interface FairnessRow {
  band: string
  n: number
  green: number
  yellow: number
  red: number
  model_fpr: number
  model_fnr: number
}

export interface CalibrationBin {
  bin: string
  predicted: number
  actual: number
  n: number
}

export interface ModelMetrics {
  auc: number
  accuracy: number
  precision: number
  recall: number
}

export interface Report {
  generated_at: string
  n_applicants: number
  n_packets: number
  external_learning: {
    datasets: DatasetCard[]
    [k: string]: unknown
  }
  model_history: {
    run: number
    date: string
    n_train_pool: number
    gb_auc: number
    lr_auc: number
    external_datasets: number
    external_rows: number
  }[]
  extraction: {
    field_level_accuracy: number
    per_field: Record<string, number>
  }
  conflict_screening: {
    injected_rate: number
    detection_recall: number
    detection_precision: number
    tp: number
    fp: number
    fn: number
  }
  risk_models: {
    n_train: number
    n_test: number
    positive_rate: number
    calibration: CalibrationBin[]
    logistic_regression: ModelMetrics
    gradient_boosting: ModelMetrics
    gb_feature_importance: Record<string, number>
    lr_coefficients: Record<string, number>
    lr_export: {
      features: string[]
      coef: number[]
      intercept: number
      scaler_mean: number[]
      scaler_std: number[]
    }
    prior_export?: unknown[]
  }
  affordability: {
    affordable_rate: number
    strained_rate: number
    not_justified_rate: number
    n_affordable: number
    n_strained: number
    n_not_justified: number
    avg_premium_to_income: number
    avg_annual_premium: number
    indicator_fail_rates: Record<string, number>
  }
  decisioning: {
    straight_through_rate: number
    rule_ml_tier_agreement: number
    n_overrides_learned: number
    thresholds: {
      a_line: number
      d_line: number
      stp_est: number
      approve_risk_rate: number
      decline_precision: number
      n_auto_approve: number
      n_auto_decline: number
      approve_risk_ceiling_used: number | null
      evaluation: string
    }
  }
  fairness_by_age: FairnessRow[]
  fairness_by_sex: FairnessRow[]
  routing: {
    n_referred: number
    by_desk: { desk: Desk; label: string; n: number; avg_difficulty: number }[]
  }
}
