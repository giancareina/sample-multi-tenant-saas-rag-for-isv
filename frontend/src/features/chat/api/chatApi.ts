// src/features/chat/api/chatApi.ts
import apiClient from '../../../api/axios';
import axios from 'axios';
import { ApiResponseBody, Message, Source } from '../types';

export const sendChatMessage = async (message: string, conversationHistory: Message[] = []): Promise<{ message: string; sources: Source[] }> => {
  try {
    const response = await apiClient.post<ApiResponseBody>('/chat/messages', { 
      message,
      conversationHistory 
    });
    
    // Ensure sources is always an array
    return {
      message: response.data.message,
      sources: response.data.sources || []
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('API Error:', error.response?.data || error.message);
      throw new Error(`API Error: ${error.response?.data?.message || error.message}`);
    }
    console.error('Unexpected error:', error);
    throw new Error('An unexpected error occurred');
  }
};
