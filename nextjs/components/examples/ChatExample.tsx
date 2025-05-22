"use client";

import {
  useChat,
  useChatMessages,
  useCreateChat,
  useCreateChatMessage,
  useUserChats,
} from "@/hooks/useApi";
import { useEffect, useState } from "react";

export default function ChatExample() {
  // State
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const systemPrompt = "You are a helpful assistant for Consumer Reports.";

  // API hooks
  const {
    execute: fetchChats,
    data: chats,
    isLoading: chatsLoading,
    error: chatsError,
  } = useUserChats();
  const { execute: createNewChat, isLoading: createChatLoading } =
    useCreateChat();
  const {
    execute: fetchChat,
    data: currentChat,
    // We use this in the JSX for conditional rendering
    isLoading: chatLoading,
  } = useChat();
  const {
    execute: fetchMessages,
    data: messages,
    isLoading: messagesLoading,
  } = useChatMessages();
  const { execute: sendMessage, isLoading: sendingMessage } =
    useCreateChatMessage();

  // Load chats on mount
  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  // Load messages when chat is selected
  useEffect(() => {
    if (selectedChatId) {
      fetchChat(selectedChatId);
      fetchMessages(selectedChatId);
    }
  }, [selectedChatId, fetchChat, fetchMessages]);

  // Handlers
  const handleCreateChat = async () => {
    try {
      const newChat = await createNewChat();
      setSelectedChatId(newChat.id);
      fetchChats(); // Refresh the list
    } catch (error) {
      console.error("Failed to create chat:", error);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedChatId || !question.trim()) return;

    try {
      await sendMessage(selectedChatId, systemPrompt, question);
      setQuestion(""); // Clear input
      fetchMessages(selectedChatId); // Refresh messages
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  // Render functions
  const renderChatList = () => {
    if (chatsLoading) return <div>Loading chats...</div>;
    if (chatsError) return <div>Error loading chats: {chatsError.message}</div>;
    if (!chats || chats.length === 0)
      return <div>No chats found. Create your first chat!</div>;

    return (
      <div className="space-y-2">
        {/* {chats.map((chat) => (
          <div
            key={chat.id}
            className={`p-3 border rounded cursor-pointer ${
              selectedChatId === chat.id ? "bg-blue-100" : ""
            }`}
            onClick={() => setSelectedChatId(chat.id)}
          >
            <h3 className="font-medium">{chat.title || "Untitled Chat"}</h3>
            {chat.latestMessage && (
              <p className="text-sm text-gray-600 truncate">
                {chat.latestMessage.content}
              </p>
            )}
          </div>
        ))} */}
      </div>
    );
  };

  const renderMessages = () => {
    if (!selectedChatId) return <div>Select a chat to view messages</div>;
    if (messagesLoading) return <div>Loading messages...</div>;
    if (!messages || messages.length === 0)
      return <div>No messages yet. Start the conversation!</div>;

    return (
      <div className="space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`p-3 rounded ${
              message.isSystem ? "bg-blue-100 ml-auto" : "bg-gray-100"
            }`}
          >
            <div className="text-sm text-gray-500">
              {message.isSystem ? "Assistant" : "You"}
            </div>
            <div className={message.isMarkdown ? "prose" : ""}>
              {message.content}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Chat Example</h1>

      <div className="grid grid-cols-3 gap-4">
        {/* Chat List */}
        <div className="col-span-1 border rounded p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Your Chats</h2>
            <button
              onClick={handleCreateChat}
              disabled={createChatLoading}
              className="px-3 py-1 bg-blue-500 text-white rounded"
            >
              {createChatLoading ? "Creating..." : "New Chat"}
            </button>
          </div>
          {renderChatList()}
        </div>

        {/* Chat Messages */}
        <div className="col-span-2 border rounded p-4">
          <h2 className="text-xl font-semibold mb-4">
            {chatLoading
              ? "Loading chat..."
              : currentChat
              ? currentChat.title || "Untitled Chat"
              : "Select a Chat"}
          </h2>

          <div className="h-96 overflow-y-auto mb-4">{renderMessages()}</div>

          {selectedChatId && (
            <div className="space-y-2">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Type your message..."
                className="w-full p-2 border rounded"
                rows={3}
                disabled={sendingMessage}
              />

              <div className="flex justify-end">
                <button
                  onClick={handleSendMessage}
                  disabled={!question.trim() || sendingMessage}
                  className="px-4 py-2 bg-blue-500 text-white rounded"
                >
                  {sendingMessage ? "Sending..." : "Send"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
