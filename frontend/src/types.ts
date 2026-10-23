export type CommentRow = {
  id: number;
  comment_id: number;
  original_text: string;
  normalized_text: string;
  published_at?: string | null;
  language: string;
  language_confidence: number;
  script: string;
  is_code_mixed: boolean;
  code_mix_tokens: { token: string; language: string }[];
  classification: string;
  confidence: number;
  risk: string;
  categories: Record<string, number>;
  category: string;
  xai: {
    method?: string;
    highlights?: { term?: string; contribution: number; direction: string }[];
    structured_evidence?: { summary?: string; top_harmful_terms?: string[] };
    important_features?: { feature?: string; token?: string; contribution: number; direction: string }[];
  };
  genai_explanation?: string | null;
  why?: string;
  active_categories?: { id: string; label: string; score: number }[];
  primary_category?: string;
  moderation_recommendation?: string;
};

export type AnalysisPayload = {
  ok: boolean;
  empty?: boolean;
  analysis_id?: number;
  demo_mode?: boolean;
  demo_notice?: string | null;
  source?: string;
  model_name?: string;
  created_at?: string;
  video?: {
    video_id?: string | null;
    title?: string | null;
    channel?: string | null;
    published_at?: string | null;
    thumbnail_url?: string | null;
  };
  stats?: Record<string, any>;
  comments?: CommentRow[];
  recent_high_risk?: CommentRow[];
  ethics?: string;
  model_status?: Record<string, any>;
};
