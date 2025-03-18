import { useEffect, useState, useCallback } from 'react';
import { DocumentState } from './types';
import { SYNC_INTERVAL, DOCUMENT_STATUS } from './config';
import { fetchDocumentsList, syncDocument, deleteDocument } from './api/documentsApi';
import { LoadingSpinner } from './components/LoadingSpinner';
import { DocumentCard } from './components/DocumentCard';

export function DocumentListContainer() {
const initialState: DocumentState = {
    documents: [],
    loading: true,
    error: null,
    syncingDocuments: new Set<string>(),
    syncingStates: {}
    };
    const [state, setState] = useState<DocumentState>(initialState);

  const fetchDocuments = useCallback(async () => {
    try {
      const documents = await fetchDocumentsList();
      setState(prev => ({
        ...prev,
        documents,
        error: null,
        syncingDocuments: new Set([...prev.syncingDocuments].filter(id => 
          documents.find(doc => doc.id === id)?.status === DOCUMENT_STATUS.SYNCING
        )),
        syncingStates: documents.reduce((acc, doc) => ({
          ...acc,
          [doc.id]: doc.status === DOCUMENT_STATUS.SYNCING
        }), {})
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'An error occurred while fetching documents.',
        documents: []
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    setState(prev => ({ ...prev, loading: true }));
    fetchDocuments();
  }, []);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    if (state.syncingDocuments.size > 0) {
      intervalId = setInterval(fetchDocuments, SYNC_INTERVAL);
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [state.syncingDocuments.size, fetchDocuments]);

  const handleSync = async (id: string) => {
    try {
      setState(prev => ({
        ...prev,
        syncingStates: { ...prev.syncingStates, [id]: true }
      }));
      await syncDocument(id);
      setState(prev => ({
        ...prev,
        syncingDocuments: new Set([...prev.syncingDocuments, id])
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'An error occurred while syncing the document.',
        syncingStates: { ...prev.syncingStates, [id]: false }
      }));
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      setState(prev => ({
        ...prev,
        documents: prev.documents.filter(doc => doc.id !== id),
        syncingDocuments: new Set([...prev.syncingDocuments].filter(docId => docId !== id))
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'An error occurred while deleting the document.'
      }));
    }
  };

  if (state.loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Documents</h2>
        {state.error && <p className="text-red-500 mt-2">{state.error}</p>}
      </div>
      <div className="flex-1 overflow-y-auto space-y-3">
        {state.documents.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            onSync={handleSync}
            onDelete={handleDelete}
            isSyncing={state.syncingStates[document.id]}
            isDisabled={state.syncingDocuments.has(document.id)}
          />
        ))}
      </div>
    </div>
  );
}