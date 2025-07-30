'use client';

import { ReactNode, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
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
  // Get the current session for authentication
  const { data: session, status } = useSession();
  
  // Debug session state
  console.log('ChatSocketProvider - session status:', status);
  console.log('ChatSocketProvider - session data:', session);
  console.log('ChatSocketProvider - accessToken:', session?.accessToken);
  
  // Track the current chat ID to prevent race conditions
  const currentChatId = useRef(chatId);
  
  // Update the current chat ID when it changes
  useEffect(() => {
    currentChatId.current = chatId;
  }, [chatId]);

  // Set up WebSocket connection and event listeners (only if authenticated)
  console.log('ChatSocketProvider - about to call useSocket, session exists:', !!session);
  console.log('ChatSocketProvider - session accessToken:', session?.accessToken);
  
  const { joinRoom, leaveRoom } = useSocket(session ? {
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
    url: getWebSocketUrl(),
    // Pass the session token for authentication
    token: session?.accessToken
  } : {});

  // Handle room changes when chatId changes
  useEffect(() => {
    // Only manage rooms if we have a session and socket functions
    if (!session || !joinRoom || !leaveRoom) return;
    
    const previousChatId = currentChatId.current;
    
    if (previousChatId !== chatId) {
      // Leave the previous room and join the new one
      leaveRoom(previousChatId);
      joinRoom(chatId);
    }
    
    // Cleanup on unmount
    return () => {
      leaveRoom(chatId);
    };
  }, [chatId, joinRoom, leaveRoom, session]);

  // No need to render anything, just manage the WebSocket connection
  return <>{children}</>;
}
