import apiClient from '../../../api/axios';
import { Document } from '../types';

export const fetchDocumentsList = async () => {
  const response = await apiClient.get<Document[]>('/documents');
  return response.data;
};

export const syncDocument = async (docId: string) => {
  await apiClient.post('/documents/sync', 
    { docId },
    {
      headers: {
        'X-Amz-Invocation-Type': 'Event'
      }
    }
  );
};

export const deleteDocument = async (id: string) => {
  await apiClient.delete('/documents', { data: { id } });
};
