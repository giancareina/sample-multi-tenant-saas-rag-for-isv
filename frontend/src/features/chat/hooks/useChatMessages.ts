// src/features/chat/hooks/useChatMessages.ts
import { useState } from 'react';
import { Message, Source } from '../types';
import { sendChatMessage } from '../api/chatApi';

export function useChatMessages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const sendMessage = async (input: string) => {
    if (isSubmitting || !input.trim()) return;
    
    setIsSubmitting(true);

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    const loadingMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true
    };

    try {
      setMessages(prev => [...prev, userMessage, loadingMessage]);
      const response = await sendChatMessage(input.trim(), [...messages, userMessage]);

      // Ensure sources is always an array
      const sources: Source[] = response.sources || [];
      console.log('Response sources:', sources);

      setMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id
            ? {
                id: msg.id,
                role: 'assistant',
                content: response.message,
                timestamp: new Date(),
                sources: sources
              }
            : msg
        )
      );
    } catch (error) {
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== loadingMessage.id),
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'An error occurred while sending the message.',
          timestamp: new Date(),
          sources: []
        }
      ]);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    messages,
    isSubmitting,
    sendMessage
  };
}