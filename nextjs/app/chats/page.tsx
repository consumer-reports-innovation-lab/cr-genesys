"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useChats, useCreateChat } from "@/utils/api-hooks";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export default function ChatListPage() {
  const { data: chats, isLoading, error, isError } = useChats();
  const createChatMutation = useCreateChat();

  const [isCreating, setIsCreating] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);

  const handleCreateChat = async () => {
    try {
      setIsCreating(true);
      setShowOverlay(true);
      const newChat = await createChatMutation.mutateAsync();
      // Navigate to the new chat
      window.location.href = `/chats/${newChat.id}`;
    } catch (error) {
      console.error("Failed to create chat:", error);
      setIsCreating(false);
      setShowOverlay(false);
    }
  };

  // Clean up loading state if component unmounts
  useEffect(() => {
    return () => {
      setIsCreating(false);
      setShowOverlay(false);
    };
  }, []);

  return (
    <div className="relative max-w-2xl mx-auto py-8 px-4 min-h-screen">
      {/* Loading Overlay */}
      {(isCreating || showOverlay) && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="flex flex-col items-center gap-4 p-8 bg-card rounded-lg shadow-lg">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p className="text-lg font-medium">Creating new chat...</p>
          </div>
        </div>
      )}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Your Chats</h1>
        <Button
          onClick={handleCreateChat}
          disabled={createChatMutation.isPending || isCreating}
          className="relative"
        >
          {isCreating ? (
            <>
              <span className="opacity-0">New Chat</span>
              <Loader2 className="h-4 w-4 animate-spin absolute" />
            </>
          ) : (
            "New Chat"
          )}
        </Button>
      </div>

      {isLoading && <p className="text-gray-500">Loading chats...</p>}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <h3 className="text-red-800 font-medium mb-2">Connection Error</h3>
          <p className="text-red-700 text-sm mb-3">
            Unable to connect to the chat server. The FastAPI server at
            http://localhost:8000 might not be running.
          </p>
          <p className="text-red-700 text-sm mb-3">
            Technical details:{" "}
            {(error as Error)?.message || "Network connection reset"}
          </p>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Retry Connection
            </Button>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {chats?.length === 0 && !isLoading && (
          <div className="text-center py-10">
            <p className="text-gray-500 mb-4">
              You don&apos;t have any chats yet
            </p>
            <Button
              onClick={handleCreateChat}
              disabled={createChatMutation.isPending || isCreating}
              className="relative"
            >
              {isCreating ? (
                <>
                  <span className="opacity-0">Creating...</span>
                  <Loader2 className="h-4 w-4 animate-spin absolute" />
                </>
              ) : (
                "Start a new conversation"
              )}
            </Button>
          </div>
        )}

        {chats?.map(({ chat, latestMessage }, idx) => (
          <Card
            key={chat.id || idx}
            className="flex items-center justify-between p-4"
          >
            <div>
              <div className="font-semibold">
                {chat.title ||
                  (chat.id && typeof chat.id === 'string' ? `Chat #${chat.id.substring(0, 8)}` : "Chat")}
              </div>
              <div className="text-muted-foreground text-sm truncate max-w-xs">
                {latestMessage?.content || "No messages yet"}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Last updated:
                {chat.updatedAt && !isNaN(new Date(chat.updatedAt).getTime())
                  ? formatDistanceToNow(new Date(chat.updatedAt), {
                      addSuffix: true,
                    })
                  : "Unknown"}
              </div>
            </div>
            <Link href={`/chats/${chat.id}`} passHref>
              <Button variant="outline" asChild>
                <a>Open</a>
              </Button>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  );
}
