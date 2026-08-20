export type DataStatus = "verified" | "placeholder";

export type SourceRef = {
  file: string;
  upstream_origin: string;
  kind: string;
  sha256: string;
  bytes: number;
};

export type Envelope = {
  schema_version: string;
  dataset: string;
  description: string;
  generated_utc: string;
  data_status: DataStatus;
  provenance: { sources: SourceRef[] };
  notes: string[];
  models?: Record<string, string>;
  n_rows: number | null;
};

export type ManifestDataset = {
  file: string;
  dataset: string;
  description: string;
  data_status: DataStatus;
  n_rows: number | null;
  sources: string[];
};

export type Manifest = {
  schema_version: string;
  generated_utc: string;
  repository: string;
  contains_individual_level_data: boolean;
  datasets: ManifestDataset[];
};

export type SampleDef = {
  sample_definition: string;
  n_samples: number;
  n_donors: number | null;
  n_donors_note?: string;
  source: string;
};

export type Cohort = {
  city: string;
  role: string;
  period_start_year: number | null;
  period_end_year: number | null;
  weather_record_start: string | null;
  weather_record_end: string | null;
  weather_days_observed: number | null;
  samples: SampleDef[];
};

export type QuartileRow = {
  city: string;
  median: number;
  p25: number;
  p75: number;
  n: number;
  source: string;
};

export type ExposureDist = QuartileRow & {
  metric: string;
  metric_label: string;
  unit: string;
  window: string;
  window_label: string;
  window_phase: string;
  window_days_before: number[];
};

export type CovariateRow = QuartileRow & {
  variable: string;
  variable_label: string;
  unit: string;
};

export type SamplesByYear = {
  city: string;
  year: number;
  n_samples: number;
  n_donors: number;
};

export type WeatherMonth = {
  city: string;
  month: number;
  n_days: number;
  mean_tmax: number;
  p10_tmax: number;
  p90_tmax: number;
};

export type WeatherHotDays = {
  city: string;
  year: number;
  n_days_observed: number;
  days_tmax_ge_30: number;
  days_tmax_ge_32: number;
  days_tmax_ge_35: number;
  max_tmax: number;
};

export type CohortSummary = Envelope & {
  cohorts: Cohort[];
  exposure_distributions: ExposureDist[];
  covariates: CovariateRow[];
  samples_by_year: SamplesByYear[];
  weather_monthly: WeatherMonth[];
  weather_annual_hot_days: WeatherHotDays[];
};

export type BaselineRow = {
  cohort: string;
  stratum: string;
  outcome: string;
  outcome_label: string;
  outcome_unit: string;
  stage: string;
  native_unit: string;
  median: number | null;
  p25: number | null;
  p75: number | null;
  mean: number | null;
  sd: number | null;
  n: number | null;
  source: string;
};

export type BaselineTable = Envelope & { rows: BaselineRow[] };

export type NativeEffect = {
  unit: string;
  effect: number | null;
  ci_low: number | null;
  ci_high: number | null;
  percent_of_median: number | null;
  analysis_sample_sd: number | null;
  analysis_sample_median: number | null;
  source: string;
};

export type ExposureRow = {
  cohort: string;
  outcome: string;
  outcome_label: string;
  outcome_unit: string;
  stage: string;
  exposure_metric: string;
  exposure_label: string;
  exposure_contrast: string;
  exposure_kind: string;
  window: string;
  window_label: string;
  window_phase: string;
  window_days_before: number[];
  beta_sd: number | null;
  se_sd: number | null;
  ci_low_sd: number | null;
  ci_high_sd: number | null;
  p_value: number | null;
  q_value: number | null;
  fdr_significant: boolean;
  p_below_0_05: boolean;
  n: number | null;
  n_donors: number | null;
  model_id: string;
  family: string;
  source: string;
  native?: NativeEffect;
};

export type VocabEntry = { label: string; unit?: string; stage?: string; phase?: string; contrast?: string; kind?: string; days_before?: number[] };

export type ExposureResponse = Envelope & {
  rows: ExposureRow[];
  vocabularies: {
    outcomes: Record<string, VocabEntry>;
    windows: Record<string, VocabEntry>;
    exposures: Record<string, VocabEntry>;
  };
};

export type InteractionRow = {
  test_set: string;
  outcome: string;
  outcome_label: string;
  outcome_unit?: string;
  stage?: string;
  exposure_metric: string;
  exposure_label?: string;
  exposure_contrast: string;
  window: string | null;
  window_label: string;
  window_phase?: string;
  window_days_before?: number[];
  beta_interaction_sd: number | null;
  se_interaction: number | null;
  ci_low_interaction: number | null;
  ci_high_interaction: number | null;
  p_interaction: number | null;
  heterogeneous_at_0_05: boolean;
  n_obs: number | null;
  n_donors: number | null;
  n_obs_wuhan?: number | null;
  n_obs_chongqing?: number | null;
  beta_wuhan_sd: number | null;
  beta_chongqing_sd: number | null;
  se_chongqing?: number | null;
  tier?: string;
  sample: string;
  model_id: string;
  source: string;
};

export type InteractionTests = Envelope & { rows: InteractionRow[] };

export type SensitivityComparison = {
  base_full_beta?: number | null;
  base_full_p?: number | null;
  n_full?: number | null;
  base_subset_beta?: number | null;
  base_subset_p?: number | null;
  n_subset?: number | null;
  heat_index_beta?: number | null;
  heat_index_p?: number | null;
  bmi_only_beta?: number | null;
  bmi_only_p?: number | null;
};

export type SensitivityRow = {
  family: string;
  family_label: string;
  cohort: string;
  outcome: string;
  outcome_label: string;
  outcome_unit: string;
  stage: string;
  exposure_metric: string;
  exposure_label: string;
  exposure_contrast: string;
  exposure_kind: string;
  window: string;
  window_label: string;
  window_phase: string;
  window_days_before: number[];
  variant: string;
  verdict_code?: string;
  beta_sd: number | null;
  se_sd: number | null;
  p_value: number | null;
  q_value?: number | null;
  n: number | null;
  n_donors?: number | null;
  comparison?: SensitivityComparison;
  model_id: string;
  source: string;
};

export type Sensitivity = Envelope & {
  rows: SensitivityRow[];
  families: string[];
};

export type ProvenanceConfidence = "HIGH" | "MEDIUM" | "LOW" | "UNRESOLVED";

export type ProvenanceEntry = {
  figure_id: string;
  in_article?: boolean;
  script?: string | null;
  input_files?: string[];
  confidence?: ProvenanceConfidence | string;
  unresolved_reason?: string | null;
  panel_letters?: string[];
  script_path?: string;
  input_data_paths?: string[];
  output_paths?: string[];
  mtime?: string;
  status: string;
};

export type ProvenanceManifest = Envelope & {
  entries: ProvenanceEntry[];
  confidence_definitions?: Record<string, string>;
  confidence_counts?: Record<string, number>;
};
