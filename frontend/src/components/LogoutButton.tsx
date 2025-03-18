// components/LogoutButton.tsx
import { useAuthenticator } from '@aws-amplify/ui-react';

function LogoutButton() {
  const { signOut } = useAuthenticator();

  return (
    <button
      onClick={signOut}
      className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded-md border border-gray-300 shadow-sm transition-all duration-200 group"
    >
      <svg 
        className="w-4 h-4 mr-2 text-gray-500 group-hover:text-gray-600" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth="2" 
          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
        />
      </svg>
      Sign out
    </button>
  );
}

export default LogoutButton;
