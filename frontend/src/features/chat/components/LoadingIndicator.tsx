export function LoadingIndicator() {
    return (
      <div className="flex items-center space-x-1.5 h-6 px-2">
        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" />
        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:200ms]" />
        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:400ms]" />
      </div>
    );
  }