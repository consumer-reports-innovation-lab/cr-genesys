'use client';

import { ReactNode, useEffect, useRef } from 'react';
import { useSocket } from '@/hooks/useSocket';
import { Message } from '@prisma/client';
import { getWebSocketUrl } from '@/utils/websocket';

interface ChatSocketProviderProps {
  children: ReactNode;
  chatId: string;
  onNewMessage?: (message: Message) => void;
  onError?: (error: Error) => void;
}

export function ChatSocketProvider({ 
  children, 
  chatId, 
  onNewMessage, 
  onError 
}: ChatSocketProviderProps) {
  // Track the current chat ID to prevent race conditions
  const currentChatId = useRef(chatId);
  
  // Update the current chat ID when it changes
  useEffect(() => {
    currentChatId.current = chatId;
  }, [chatId]);

  // Set up WebSocket connection and event listeners
  const { joinRoom, leaveRoom } = useSocket({
    events: {
      // When a new message is received, validate it before calling the callback
      new_message: (data: unknown) => {
        try {
          // Basic validation of the message structure
          if (!data || typeof data !== 'object') {
            throw new Error('Invalid message format');
          }
          
          const message = data as Message;
          
          // Validate the message has required fields
          if (!message.id || !message.chatId || !message.content) {
            throw new Error('Invalid message: missing required fields');
          }
          
          // Verify the message is for the current chat
          if (message.chatId !== currentChatId.current) {
            console.warn('Received message for different chat ID', {
              expected: currentChatId.current,
              received: message.chatId
            });
            return;
          }
          
          // Call the callback if provided
          onNewMessage?.(message);
          
        } catch (err) {
          const error = err instanceof Error ? err : new Error('Unknown error handling message');
          console.error('Error handling new message:', error);
          onError?.(error);
        }
      },
      // Add other socket events here if needed
    },
    onConnect: () => {
      console.log('Connected to WebSocket server');
      // Join the chat room when connected
      joinRoom?.(currentChatId.current);
    },
    onDisconnect: () => {
      console.log('Disconnected from WebSocket server');
    },
    // Connect to the backend WebSocket server
    url: getWebSocketUrl()
  });

  // Handle room changes when chatId changes
  useEffect(() => {
    const previousChatId = currentChatId.current;
    
    if (previousChatId !== chatId) {
      // Leave the previous room and join the new one
      leaveRoom?.(previousChatId);
      joinRoom?.(chatId);
    }
    
    // Cleanup on unmount
    return () => {
      leaveRoom?.(chatId);
    };
  }, [chatId, joinRoom, leaveRoom]);

  // No need to render anything, just manage the WebSocket connection
  return <>{children}</>;
}
