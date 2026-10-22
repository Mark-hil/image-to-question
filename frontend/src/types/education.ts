export type EducationStage =
  | 'early_years'
  | 'primary'
  | 'junior_secondary'
  | 'senior_secondary'
  | 'diploma'
  | 'undergraduate'
  | 'postgraduate'
  | 'doctoral'
  | 'professional';

export interface EducationLevel {
  code: string;
  label: string;
  stage: EducationStage;
  ordinal: number;
  typical_age?: [number, number];
  description: string;
  max_choices: number;
  allowed_qtypes: string[];
}

export interface StageMetadata {
  code: EducationStage;
  label: string;
  description: string;
}

export interface EducationCatalogResponse {
  status: string;
  default_level: string;
  total_levels: number;
  stages: StageMetadata[];
  levels: EducationLevel[];
}

export interface LevelResolveResponse {
  status: string;
  query: string;
  matched: boolean;
  level?: EducationLevel;
  resolved?: EducationLevel;
  class_label?: string;
}
