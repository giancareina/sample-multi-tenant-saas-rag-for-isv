export type Source = {
    title: string;
    snippet: string;
    metadata?: Record<string, any>;
};

export type Message = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    loading?: boolean;
    sources?: Source[];
  };
  
  export type ApiResponseBody = {
    message: string;
    sources: Source[];
    timestamp?: string;
  };