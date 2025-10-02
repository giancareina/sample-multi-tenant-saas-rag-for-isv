import apiClient from '../../../api/axios';
import axios from 'axios';
import { UsageApiResponse } from '../types';

export const fetchUsageDashboard = async (): Promise<UsageApiResponse> => {
  try {
    const response = await apiClient.get<UsageApiResponse>('/consumption/dashboard');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Usage API Error:', error.response?.data || error.message);
      throw new Error(`Failed to fetch usage data: ${error.response?.data?.message || error.message}`);
    }
    console.error('Unexpected error:', error);
    throw new Error('An unexpected error occurred while fetching usage data');
  }
};