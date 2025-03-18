import { Message } from '../types';
import { LoadingIndicator } from './LoadingIndicator';
import { MessageContent } from './MessageContent';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div
      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[70%] rounded-2xl p-4 ${
          message.role === 'user'
            ? 'bg-indigo-600 text-white'
            : 'bg-white shadow-sm border border-gray-100'
        }`}
      >
        {message.loading ? (
          <LoadingIndicator />
        ) : (
          <MessageContent message={message} />
        )}
      </div>
    </div>
  );
}