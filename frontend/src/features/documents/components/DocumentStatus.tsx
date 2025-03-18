import { Document } from '../types';

interface DocumentStatusProps {
  document: Document;
  isSyncing: boolean;
}

export function DocumentStatus({ document, isSyncing }: DocumentStatusProps) {
  const getStatusStyle = () => {
    if (isSyncing) {
      return 'bg-yellow-100 text-yellow-800';
    }
    if (document.status === 'synced') {
      return 'bg-green-100 text-green-800';
    }
    return 'bg-blue-100 text-blue-800';
  };

  const getStatusText = () => {
    if (isSyncing) {
      return 'Syncing';
    }
    return document.status;
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle()}`}>
      {getStatusText()}
    </span>
  );
}