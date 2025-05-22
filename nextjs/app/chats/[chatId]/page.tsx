"use client"
import React, { useState, useEffect, useCallback, useRef } from "react"; // Import useRef
import { Card } from "@/components/ui/card";
import { ChatHistory, ChatInput } from "@/components/chat";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { getChatMessages, Message, ApiError } from "@/utils/api";

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>(); // Ensure chatId is typed
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null); // Add ref for the scrollable div

  // Define fetchMessages using useCallback
  const fetchMessages = useCallback(async () => {
    if (!chatId || !session) return; // Ensure chatId and session are available

    setIsLoading(true);
    setError(null);
    try {
      const fetchedMessages = await getChatMessages(chatId, session);
      setMessages(fetchedMessages);
    } catch (err) {
      console.error("Failed to fetch messages:", err);
      if (err instanceof ApiError) {
        setError(`Error fetching messages: ${err.message} (Status: ${err.status})`);
      } else if (err instanceof Error) {
        setError(`Error fetching messages: ${err.message}`);
      } else {
        setError("An unknown error occurred while fetching messages.");
      }
      setMessages([]); // Clear messages on error
    } finally {
      setIsLoading(false);
    }
  }, [chatId, session]); // Dependencies for useCallback

  // Initial fetch on component mount or when chatId/session change
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]); // fetchMessages is now stable due to useCallback

  // Effect to scroll to bottom when messages change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]); // Run whenever messages state updates

  // --- Loading and Error States ---
  if (isLoading && messages.length === 0) { // Show loading only initially
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
  return (
    <div className="flex flex-col h-full max-h-screen p-4 gap-4">
      {/* Attach the ref to the scrollable Card component */}
      <Card ref={scrollContainerRef} className="flex-1 overflow-auto">
        {/* Consider showing a subtle loading indicator during refresh? */}
        <ChatHistory messages={messages.map(msg => ({ ...msg, sender: msg.isSystem ? 'system' : 'user', createdAt: new Date(msg.createdAt) }))} />
      </Card>
      {/* Pass fetchMessages down as onNewMessage */}
      <ChatInput chatId={chatId as string} onNewMessage={fetchMessages} />
    </div>
  );
}
