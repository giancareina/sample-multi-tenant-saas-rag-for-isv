import { useRef } from 'react';
import { UploadIcon } from './UploadIcon';
import { FilePreview } from './FilePreview';

interface DropZoneProps {
  onDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  selectedFile: File | null;
  previewUrl: string | null;
}

export function DropZone({ onDrop, onFileSelect, selectedFile, previewUrl }: DropZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div
      onDrop={onDrop}
      onDragOver={handleDragOver}
      className="relative border-2 border-dashed border-gray-200 rounded-lg transition-all duration-300 hover:border-indigo-500 bg-gray-50 hover:bg-gray-50/50"
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={onFileSelect}
        className="hidden"
        id="fileInput"
        accept=".txt,.csv"
      />
      <label
        htmlFor="fileInput"
        className="flex flex-col items-center justify-center p-8 cursor-pointer"
      >
        <div className="w-12 h-12 mb-4 rounded-full bg-indigo-100 flex items-center justify-center">
          <UploadIcon />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-indigo-600">Drop files to upload</p>
          <p className="mt-1 text-xs text-gray-500">or click to browse</p>
        </div>
      </label>

      {selectedFile && <FilePreview file={selectedFile} previewUrl={previewUrl} />}
    </div>
  );
}
