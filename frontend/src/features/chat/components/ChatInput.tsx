import { useRef } from 'react';

interface ChatInputProps {
  input: string;
  isSubmitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onCompositionStart: () => void;
  onCompositionEnd: () => void;
}

export function ChatInput({ 
  input, 
  isSubmitting, 
  onSubmit, 
  onChange, 
  onKeyDown,
  onCompositionStart,
  onCompositionEnd
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <div className="border-t bg-white p-4 shadow-sm">
      <form onSubmit={onSubmit} className="max-w-4xl mx-auto">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={onChange}
            onKeyDown={onKeyDown}
            onCompositionStart={onCompositionStart}
            onCompositionEnd={onCompositionEnd}
            disabled={isSubmitting}
            className="flex-1 rounded-xl px-4 py-3 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none min-h-[44px] max-h-[200px] disabled:opacity-50 text-sm"
            placeholder="Type a message... (Shift + Enter for new line)"
          />
          <button
            type="submit"
            disabled={isSubmitting || !input.trim()}
            className="h-11 px-6 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium flex items-center justify-center min-w-[100px]"
          >
            {isSubmitting ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              'Send'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}