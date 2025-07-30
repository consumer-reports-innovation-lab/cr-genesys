"use client";
import { ChatHistory, ChatInput } from "@/components/chat";
import { Card } from "@/components/ui/card";
import { ApiError, getChat, getChatMessages } from "@/utils/api";
import type { Message } from "@prisma/client";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatSocketProvider } from "@/providers";

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>(); // Ensure chatId is typed
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]); // Initialize as empty array
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null); // Add ref for the scrollable div

  // Define fetchData using useCallback
  const fetchData = useCallback(async () => {
    if (!chatId || !session) return; // Ensure chatId and session are available

    setIsLoading(true);
    setError(null);
    try {
      // Fetch both chat and messages in parallel
      const [{ chat: chatData }, fetchedMessages] = await Promise.all([
        getChat(chatId, session, { includeChatHistory: false }),
        getChatMessages(chatId, session),
      ]);

      setMessages(fetchedMessages);

      // Return whether the chat is closed to be used in the effect
      return chatData.status === "CLOSED";
    } catch (err) {
      console.error("Failed to fetch chat data:", err);
      if (err instanceof ApiError) {
        setError(`Error: ${err.message} (Status: ${err.status})`);
      } else if (err instanceof Error) {
        setError(`Error: ${err.message}`);
      } else {
        setError("An unknown error occurred while fetching chat data.");
      }
      setMessages([]); // Clear messages on error
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [chatId, session]); // Dependencies for useCallback

  // State to track if chat is closed
  const [isChatClosed, setIsChatClosed] = useState(false);

  // Handle new messages from WebSocket
  const handleNewMessage = useCallback(async () => {
    try {
      const updatedMessages = await getChatMessages(chatId, session!);
      setMessages(updatedMessages);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to refresh messages');
      console.error('Failed to refresh messages after receiving new message:', error);
      setError(error.message);
    }
  }, [chatId, session]);
  
  // Handle WebSocket errors
  const handleSocketError = useCallback((error: Error) => {
    console.error('WebSocket error:', error);
    setError(`Connection error: ${error.message}`);
  }, []);

  // Define fetchMessages for backward compatibility
  const fetchMessages = useCallback(async () => {
    const isClosed = await fetchData();
    if (isClosed !== undefined) {
      setIsChatClosed(isClosed);
    }
  }, [fetchData]);

  // Initial fetch on component mount or when chatId/session change
  useEffect(() => {
    const loadData = async () => {
      const isClosed = await fetchData();
      if (isClosed !== undefined) {
        setIsChatClosed(isClosed);
      }
    };
    
    // Only fetch data if we have a session
    if (session) {
      loadData();
    }
  }, [fetchData, session]);

  // Effect to scroll to bottom when messages change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
  }, [messages]); // Run whenever messages state updates

  // --- Loading and Error States ---
  if (isLoading && messages?.length === 0) {
    // Show loading only initially
    return (
      <div className="flex items-center justify-center h-full">
        Loading chat messages...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-600">
        <p>Failed to load chat:</p>
        <p>{error}</p>
        {/* Optionally add a retry button */}
        {/* <button onClick={fetchMessages}>Retry</button> */}
      </div>
    );
  }

  // --- Render Chat ---
  // Don't render if chatId is not available yet
  if (!chatId) {
    return (
      <div className="flex items-center justify-center h-full">
        Loading...
      </div>
    );
  }

  return (
    <ChatSocketProvider 
      chatId={chatId as string} 
      onNewMessage={handleNewMessage}
      onError={handleSocketError}
    >
      <div className="flex flex-col h-full">
        <Card className="flex-1 overflow-hidden flex flex-col">
          {isLoading && messages?.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              Loading messages...
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full text-red-600">
              Failed to load messages: {error}
            </div>
          ) : (
            <ChatHistory
              messages={
                messages?.map((msg) => {
                  // Safeguard against incomplete message data
                  if (!msg || !msg.id || !msg.content) {
                    console.warn('Incomplete message data:', msg);
                    return null;
                  }
                  
                  return {
                    id: msg.id,
                    content: msg.content || '',
                    sender: msg.isSystem ? "system" : "user",
                    createdAt: msg.createdAt ? new Date(msg.createdAt) : new Date(),
                  };
                }).filter(Boolean) || []
              }
            />
          )}
        </Card>
        {/* Pass fetchMessages down as onNewMessage and disable if chat is closed */}
        <ChatInput
          chatId={chatId}
          onNewMessage={fetchMessages || (() => console.error('fetchMessages is undefined'))}
          disabled={isChatClosed}
        />
      </div>
    </ChatSocketProvider>
  );
}
