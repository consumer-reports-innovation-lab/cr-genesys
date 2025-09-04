import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createChatMessage,
  getChat,
  getChats,
  createChat as apiCreateChat,
} from "./api";
import type { Chat, ChatWithLatestMessage } from "../schemas";

// --- START OF MOCK IMPLEMENTATION ---

// This flag controls whether we use mock data or the real API.
// To switch back to the real API, simply change this to false.
const USE_MOCK_DATA = true;

// A simple in-memory "database" for our mock chats
let mockChats: ChatWithLatestMessage[] = [
  {
    chat: {
      id: "mock-chat-1",
      title: "Example Chat",
      updatedAt: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      userId: 'mock-user',
      status: 'OPEN',
      genesysConversationId: null,
    },
    latestMessage: {
      id: "mock-msg-1",
      content: "This is a mock chat run locally.",
      createdAt: new Date().toISOString(),
    },
  },
];

export const useChats = () => {
  if (USE_MOCK_DATA) {
    console.log("HOOK: useChats (MOCKED)");
    return {
      data: mockChats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: () => console.log("Mock refetch called."),
    };
  }
  // Original implementation
  return useQuery<ChatWithLatestMessage[], Error>({
    queryKey: ["chats"],
    queryFn: getChats,
  });
};

export const useCreateChat = () => {
  const queryClient = useQueryClient();
  
  if (USE_MOCK_DATA) {
    console.log("HOOK: useCreateChat (MOCKED)");
    return useMutation<Chat, Error, void>({
      mutationFn: async () => {
        console.log("Creating a mock chat...");
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500));

        const newChatId = `mock-chat-${Date.now()}`;
        const newChat: ChatWithLatestMessage = {
          chat: {
            id: newChatId,
            title: `New Mock Chat`,
            updatedAt: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            userId: 'mock-user',
            status: 'OPEN',
            genesysConversationId: null,
          },
          latestMessage: null,
        };
        mockChats.push(newChat);
        return newChat.chat;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["chats"] });
      },
    });
  }

  // Original implementation
  return useMutation({
    mutationFn: apiCreateChat,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });
};

// --- We will not mock the other hooks for now ---

export const useChat = (chatId: string) => {
  return useQuery<Chat, Error>({
    queryKey: ["chat", chatId],
    queryFn: () => getChat(chatId),
    enabled: !!chatId,
  });
};

export const useCreateChatMessage = (chatId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => createChatMessage(chatId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", chatId] });
    },
  });
};