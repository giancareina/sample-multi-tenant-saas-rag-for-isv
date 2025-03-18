interface FilePreviewProps {
    file: File;
    previewUrl: string | null;
  }
  
  export function FilePreview({ file, previewUrl }: FilePreviewProps) {
    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-900">{file.name}</p>
            <p className="text-xs text-gray-500">{Math.round(file.size / 1024)} KB</p>
          </div>
        </div>
        {previewUrl && file.type.startsWith('image/') && (
          <img
            src={previewUrl}
            alt="Preview"
            className="mt-4 max-h-48 rounded-lg object-contain"
          />
        )}
      </div>
    );
  }