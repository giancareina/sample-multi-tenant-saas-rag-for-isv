export interface Document {
    id: string;
    title: string;
    uploadDate: string;
    fileType: string;
    size: string;
    bucket: string;
    key: string;
    status: string;
  }
  
  export interface DocumentState {
    documents: Document[];
    loading: boolean;
    error: string | null;
    syncingDocuments: Set<string>;
    syncingStates: { [key: string]: boolean };
  }