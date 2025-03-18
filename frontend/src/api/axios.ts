// api/axios.ts
import axios from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_ENDPOINT,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
});

apiClient.interceptors.request.use(async (config) => {
  const session = await fetchAuthSession();
  const idToken = session.tokens?.idToken?.toString();
  if (idToken) {
    config.headers.Authorization = `Bearer ${idToken}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default apiClient;
