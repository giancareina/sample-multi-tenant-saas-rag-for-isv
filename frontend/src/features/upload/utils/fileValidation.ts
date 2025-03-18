import { ALLOWED_FILE_TYPES } from '../config';

export const validateFile = (file: File): { isValid: boolean; errorMessage?: string } => {
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return {
      isValid: false,
      errorMessage: 'Only .txt and .csv files are allowed'
    };
  }
  return { isValid: true };
};