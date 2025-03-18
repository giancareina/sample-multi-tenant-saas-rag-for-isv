// components/UserInfo.tsx
import { fetchAuthSession } from 'aws-amplify/auth';
import { useState, useEffect } from 'react';

function UserInfo() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [tokens, setTokens] = useState<{
    accessToken?: string;
    idToken?: string;
  }>({});

  useEffect(() => {
    const getSession = async () => {
      try {
        const session = await fetchAuthSession();
        setTokens({
          accessToken: session.tokens?.accessToken?.toString(),
          idToken: session.tokens?.idToken?.toString(),
        });
      } catch (error) {
        // Fallback silently on error
      }
    };

    getSession();
  }, []);

  return (
    <div className="relative">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
      >
        <svg 
          className="h-8 w-8 text-gray-400 bg-gray-100 rounded-full p-1" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth="2" 
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
          />
        </svg>
        <span>User Details</span>
        <svg className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${isExpanded ? 'transform rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isExpanded && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-md shadow-lg overflow-hidden z-50 border border-gray-200">
          <div className="px-4 py-3 space-y-4">
            <div>
              {/* eslint-disable-next-line jsx-not-internationalized */}
              <h4 className="text-sm font-medium text-gray-500">Access Token</h4>
              <div className="mt-1 bg-gray-50 p-2 rounded-md overflow-auto max-h-20">
                <code className="text-xs text-gray-700 break-all">{tokens.accessToken}</code>
              </div>
            </div>
            <div>
              {/* eslint-disable-next-line jsx-not-internationalized */}
              <h4 className="text-sm font-medium text-gray-500">ID Token</h4>
              <div className="mt-1 bg-gray-50 p-2 rounded-md overflow-auto max-h-20">
                <code className="text-xs text-gray-700 break-all">{tokens.idToken}</code>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserInfo;