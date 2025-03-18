import apiClient from '../../../api/axios';
import { UploadResponse } from '../types';

export const getUploadUrl = async (fileName: string, fileType: string) => {
  const response = await apiClient.get<UploadResponse>('/documents/upload-url', {
    params: { fileName, fileType }
  });
  return response.data;
};

export const uploadFileToUrl = async (url: string, file: File) => {
  await apiClient.put(url, file, {
    headers: {
      'Content-Type': file.type,
      'x-amz-meta-original_filename': file.name
    },
    withCredentials: false,
    transformRequest: [(data, headers) => {
      Object.keys(headers).forEach(key => delete headers[key]);
      headers['Content-Type'] = file.type;
      headers['x-amz-meta-original_filename'] = file.name;
      return data;
    }]
  });
};
