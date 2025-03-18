interface FileTypeIconProps {
    fileType: string;
  }
  
  export function FileTypeIcon({ fileType }: FileTypeIconProps) {
    const iconClasses = "w-5 h-5";
    
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return (
          <svg className={`${iconClasses} text-red-500`} viewBox="0 0 24 24">
            <rect x="4" y="2" width="16" height="20" rx="2" fill="currentColor" />
            <path d="M8 7h8M8 12h8M8 17h5" stroke="white" strokeWidth="1.5" />
          </svg>
        );
      case 'excel':
        return (
          <svg className={`${iconClasses} text-green-500`} viewBox="0 0 24 24">
            <rect x="4" y="2" width="16" height="20" rx="2" fill="currentColor" />
            <path d="M8 7h8M8 12h8M8 17h8" stroke="white" strokeWidth="1.5" />
          </svg>
        );
      default:
        return (
          <svg className={`${iconClasses} text-gray-500`} viewBox="0 0 24 24">
            <rect x="4" y="2" width="16" height="20" rx="2" fill="currentColor" />
            <path d="M8 7h8M8 12h8" stroke="white" strokeWidth="1.5" />
          </svg>
        );
    }
  }