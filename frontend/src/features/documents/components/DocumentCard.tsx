import { Document } from '../types';
import { FileTypeIcon } from './FileTypeIcon';
import { DocumentStatus } from './DocumentStatus';
import { DocumentActions } from './DocumentActions';

interface DocumentCardProps {
  document: Document;
  onSync: (id: string) => void;
  onDelete: (id: string) => void;
  isSyncing: boolean;
  isDisabled: boolean;
}

export function DocumentCard({ document, onSync, onDelete, isSyncing, isDisabled }: DocumentCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-all duration-200">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <FileTypeIcon fileType={document.fileType} />
          <div>
            <h3 className="text-base font-medium text-gray-900">{document.title}</h3>
            <div className="mt-1 flex items-center space-x-3 text-sm text-gray-500">
              <span>{new Date(document.uploadDate).toLocaleDateString()}</span>
              <span>•</span>
              <span>{document.size}</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {document.fileType}
              </span>
              <DocumentStatus document={document} isSyncing={isSyncing} />
            </div>
          </div>
        </div>
        <DocumentActions
          onSync={() => onSync(document.id)}
          onDelete={() => onDelete(document.id)}
          isSyncing={isSyncing}
          isDisabled={isDisabled}
        />
      </div>
    </div>
  );
}