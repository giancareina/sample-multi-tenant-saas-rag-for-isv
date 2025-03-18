import { useState, useEffect } from 'react';
import { validateFile } from './utils/fileValidation';
import { getUploadUrl, uploadFileToUrl } from './api/uploadApi';
import { SUCCESS_MESSAGE_DURATION } from './config';
import { SuccessMessage } from './components/SuccessMessage';
import { DropZone } from './components/DropZone';
import { UploadButton } from './components/UploadButton';

export function UploadContainer() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const validation = validateFile(file);
      if (validation.isValid) {
        setSelectedFile(file);
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else if (validation.errorMessage) {
        setUploadError(validation.errorMessage);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const validation = validateFile(file);
      if (validation.isValid) {
        setSelectedFile(file);
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else if (validation.errorMessage) {
        setUploadError(validation.errorMessage);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadError(null);
    
    try {
      const { signedUrl } = await getUploadUrl(selectedFile.name, selectedFile.type);
      await uploadFileToUrl(signedUrl, selectedFile);

      setSelectedFile(null);
      setPreviewUrl(null);
      setSuccessMessage(`${selectedFile.name} has been successfully uploaded!`);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
      }, SUCCESS_MESSAGE_DURATION);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6 flex items-center justify-center">
      <div className="w-full max-w-xl bg-white rounded-xl shadow-lg p-8">
        <div className="space-y-6">
          <SuccessMessage message={successMessage} />
          {uploadError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{uploadError}</p>
            </div>
          )}
          <DropZone
            onDrop={handleDrop}
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
            previewUrl={previewUrl}
          />
          <UploadButton
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            uploading={uploading}
          />
        </div>
      </div>
    </div>
  );
}