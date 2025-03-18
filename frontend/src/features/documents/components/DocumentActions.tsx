interface DocumentActionsProps {
    onSync: () => void;
    onDelete: () => void;
    isSyncing: boolean;
    isDisabled: boolean;
  }
  
  export function DocumentActions({ onSync, onDelete, isSyncing, isDisabled }: DocumentActionsProps) {
    return (
      <div className="flex items-center space-x-4">
        <button
          onClick={onSync}
          disabled={isSyncing || isDisabled}
          className={`text-sm font-medium ${
            isSyncing
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'text-indigo-600 hover:text-indigo-800'
          }`}
        >
          {isSyncing ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Syncing...
            </span>
          ) : (
            'Sync'
          )}
        </button>
  
        <div className="w-px h-4 bg-gray-200"></div>
        <button
          onClick={onDelete}
          className="text-sm font-medium text-gray-600 hover:text-red-600"
          disabled={isDisabled}
        >
          Delete
        </button>
      </div>
    );
  }