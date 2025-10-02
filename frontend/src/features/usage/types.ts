export interface ModelUsage {
  invocations: number;
  input_tokens: number;
  output_tokens: number;
  cost: number;
}

export interface CurrentMonthUsage {
  total_cost: number;
  total_invocations: number;
  total_tokens: number;
  chat_invocations: number;
  embedding_invocations: number;
  model_breakdown: Record<string, ModelUsage>;
}

export interface UsageTrends {
  cost_trend: number;
  usage_trend: number;
}

export interface UsageDashboardData {
  current_month: CurrentMonthUsage;
  trends: UsageTrends;
}

export interface UsageApiResponse {
  current_month: CurrentMonthUsage;
  trends: UsageTrends;
}

export interface UsageState {
  data: UsageDashboardData | null;
  loading: boolean;
  error: string | null;
}