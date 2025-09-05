// nextjs/utils/api-hooks.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import {
  createChatMessage,
  getChat,
  getUserChats,
  createChat as apiCreateChat,
} from "./api";
import type { Chat, ChatWithLatestMessage, Message } from "../schemas";

const USE_MOCK_DATA = true;

let mockChats: ChatWithLatestMessage[] = [
  {
    chat: {
      id: "mock-chat-1",
      title: "Hardcoded Demo Chat",
      updatedAt: new Date(),
      createdAt: new Date(),
      userId: 'mock-user',
      status: 'OPEN',
      genesysOpenMessageSessionId: null,
      genesysOpenMessageActive: true,
    },
    latestMessage: {
      id: "mock-msg-1",
      content: "This is a local-only mock chat.",
      createdAt: new Date(),
      updatedAt: new Date(),
      chatId: "mock-chat-1",
      isSystem: false,
      isMarkdown: false,
      sentToGenesys: false,
      genesysMessageId: null,
      messageType: "user",
    },
  },
];

export const useChats = () => {
  const { data: session } = useSession();

  if (USE_MOCK_DATA) {
    return {
      data: mockChats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: () => {},
    };
  }
  
  return useQuery<ChatWithLatestMessage[], Error>({
    queryKey: ["chats", session?.user?.id],
    queryFn: () => getUserChats(session),
    enabled: !!session,
  });
};

export const useCreateChat = () => {
  const queryClient = useQueryClient();
  const { data: session } = useSession();

  const mutationFn = async (): Promise<Chat> => {
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 500));
      const newChatId = `mock-chat-${Date.now()}`;
      const newChat: ChatWithLatestMessage = {
        chat: {
          id: newChatId,
          title: `New Mock Chat`,
          updatedAt: new Date(),
          createdAt: new Date(),
          userId: 'mock-user',
          status: 'OPEN',
          genesysOpenMessageSessionId: null,
          genesysOpenMessageActive: true,
        },
        latestMessage: null,
      };
      mockChats.push(newChat);
      return newChat.chat;
    }

    if (!session) {
      throw new Error("User not authenticated");
    }
    return apiCreateChat(session);
  };

  return useMutation<Chat, Error, void>({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
};

export const useChat = (chatId: string) => {
    const { data: session } = useSession();
    return useQuery<{ chat: Chat }, Error>({
        queryKey: ["chat", chatId],
        queryFn: () => getChat(chatId, session),
        enabled: !!chatId && !!session,
    });
};

export const useCreateChatMessage = (chatId: string) => {
  const queryClient = useQueryClient();
  const { data: session } = useSession();

  return useMutation<Message, Error, string>({
    mutationFn: (content: string) => {
        if (!session) {
            return Promise.reject(new Error("User not authenticated"));
        }
        const systemPrompt = "You are a helpful assistant.";
        return createChatMessage(chatId, systemPrompt, content, session);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", chatId] });
    },
  });
};