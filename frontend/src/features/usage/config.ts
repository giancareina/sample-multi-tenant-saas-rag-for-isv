export const USAGE_CONFIG = {
  // API endpoints
  ENDPOINTS: {
    DASHBOARD: '/consumption/dashboard'
  },
  
  // Display constants
  CURRENCY: {
    SYMBOL: '$',
    DECIMAL_PLACES: 4,
  },
  
  // Formatting
  NUMBER_FORMAT: {
    LARGE_NUMBER_THRESHOLD: 1000,
    DECIMAL_PLACES: 0,
  },
  
  // Error messages
  ERROR_MESSAGES: {
    FETCH_FAILED: 'Failed to load usage data. Please try again.',
    NETWORK_ERROR: 'Network error. Please check your connection.',
    UNAUTHORIZED: 'You are not authorized to view this data.',
    GENERIC_ERROR: 'An unexpected error occurred.',
  },
  
  // Loading states
  LOADING_TIMEOUT: 30000, // 30 seconds
} as const;

export const MODEL_DISPLAY_NAMES: Record<string, string> = {
  'anthropic.claude-3-5-sonnet-20241022-v2:0': 'Claude 3.5 Sonnet',
  'anthropic.claude-3-haiku-20240307-v1:0': 'Claude 3 Haiku',
  'amazon.titan-embed-text-v2:0': 'Titan Embed Text v2',
  'amazon.titan-embed-text-v1': 'Titan Embed Text v1',
} as const;