'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import { 
  getUserChats, 
  createChat, 
  getChat, 
  getChatMessages, 
  createChatMessage,
  getPureCloudPermissions
} from './api';

// Query keys
export const QUERY_KEYS = {
  chats: 'chats',
  chat: (id: string) => ['chat', id],
  messages: (chatId: string) => ['messages', chatId],
  pureCloudPermissions: 'pureCloudPermissions',
};

/**
 * Hook to fetch all chats for the current user
 */
export function useChats() {
  const { data: session } = useSession();
  
  return useQuery({
    queryKey: [QUERY_KEYS.chats],
    queryFn: () => getUserChats(session),
    enabled: !!session,
  });
}

/**
 * Hook to create a new chat
 */
export function useCreateChat() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => createChat(session),
    onSuccess: (newChat) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.chats] });
      return newChat;
    },
  });
}

/**
 * Hook to fetch a specific chat by ID
 */
export function useChat(chatId: string) {
  const { data: session } = useSession();
  
  return useQuery({
    queryKey: QUERY_KEYS.chat(chatId),
    queryFn: () => getChat(chatId, session),
    enabled: !!chatId && !!session,
  });
}

/**
 * Hook to fetch all messages for a specific chat
 */
export function useChatMessages(chatId: string) {
  const { data: session } = useSession();
  
  return useQuery({
    queryKey: QUERY_KEYS.messages(chatId),
    queryFn: () => getChatMessages(chatId, session),
    enabled: !!chatId && !!session,
  });
}

/**
 * Hook to create a new message in a chat
 */
export function useCreateChatMessage(chatId: string) {
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ systemPrompt, question }: { systemPrompt: string, question: string }) => 
      createChatMessage(chatId, systemPrompt, question, session),
    onSuccess: (newMessage) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chat(chatId) });
      return newMessage;
    },
  });
}

/**
 * Hook to fetch PureCloud permissions
 */
export function usePureCloudPermissions() {
  const { data: session } = useSession();
  
  return useQuery({
    queryKey: [QUERY_KEYS.pureCloudPermissions],
    queryFn: () => getPureCloudPermissions(session),
    enabled: !!session,
  });
}
