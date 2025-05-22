/**
 * React hooks for API calls
 */

import * as api from "@/utils/api";
import { Session } from "next-auth";
import { useSession } from "next-auth/react";
import { useState } from "react";

/**
 * Hook for handling loading and error states with API calls
 */
export function useApiCall<T, P extends unknown[]>(
  apiFunction: (session: Session | null, ...args: P) => Promise<T>
) {
  const { data: session } = useSession();
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = async (...args: P) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiFunction(session, ...args);
      setData(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return { execute, data, isLoading, error };
}

/**
 * Hook for fetching user chats
 */
export function useUserChats() {
  return useApiCall(api.getUserChats);
}

/**
 * Hook for creating a new chat
 */
export function useCreateChat() {
  return useApiCall(api.createChat);
}

/**
 * Hook for fetching a specific chat
 */
export function useChat() {
  return useApiCall<api.Chat, [string]>((session, chatId) =>
    api.getChat(chatId, session)
  );
}

/**
 * Hook for fetching chat messages
 */
export function useChatMessages() {
  return useApiCall<api.Message[], [string]>((session, chatId) =>
    api.getChatMessages(chatId, session)
  );
}

/**
 * Hook for creating a chat message
 */
export function useCreateChatMessage() {
  return useApiCall<api.Message, [string, string, string]>(
    (session, chatId, systemPrompt, question) =>
      api.createChatMessage(chatId, systemPrompt, question, session)
  );
}

/**
 * Hook for fetching PureCloud permissions
 */
export function usePureCloudPermissions() {
  return useApiCall(api.getPureCloudPermissions);
}
