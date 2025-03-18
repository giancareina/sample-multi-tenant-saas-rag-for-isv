import { Message } from '../types';
import { SimpleSourcesList } from './SimpleSourcesList';
interface MessageContentProps {
  message: Message;
}

export function MessageContent({ message }: MessageContentProps) {
  const isAssistantMessage = message.role === 'assistant';
  
  // Check if sources exists and is an array (even if empty)
  const hasSources = isAssistantMessage && Array.isArray(message.sources);
  const sourceCount = hasSources ? message.sources!.length : 0;
  
  return (
    <div className="space-y-1">
      <p className="text-sm leading-relaxed break-words whitespace-pre-wrap">
        {message.content}
      </p>
      {isAssistantMessage && (
        <>
          {hasSources ? (
            <SimpleSourcesList sourceCount={sourceCount} isAssistantMessage={isAssistantMessage} />
          ) : (
            <p className="text-xs text-gray-500 mt-2 italic">
              No sources found
            </p>
          )}
        </>
      )}
      <p className={`text-[10px] ${
        message.role === 'user' ? 'text-indigo-200' : 'text-gray-400'
      }`}>
        {message.timestamp.toLocaleTimeString()}
      </p>
    </div>
  );
}