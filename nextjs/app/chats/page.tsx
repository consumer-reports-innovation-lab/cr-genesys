"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useChats, useCreateChat } from "@/utils/api-hooks";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";

export default function ChatListPage() {
  const { data: chats, isLoading, isError, refetch } = useChats();
  // FIX: Removed the unused 'session' variable to prevent a build error.
  const { status: sessionStatus } = useSession();
  const createChatMutation = useCreateChat();
  const router = useRouter();

  const handleCreateChat = () => {
    if (sessionStatus !== 'authenticated') {
      console.error('Cannot create chat: User not authenticated');
      return;
    }

    // --- THIS IS THE FIX ---
    // The mutate function for our mock setup doesn't require any arguments.
    // Calling it without 'undefined' resolves the TypeScript error.
    createChatMutation.mutate(undefined, {
      onSuccess: (newChat) => {
        router.push(`/chats/${newChat.id}`);
      },
      onError: (error) => {
        console.error("Failed to create chat:", error);
      },
    });
  };

  return (
    <div className="relative max-w-2xl mx-auto py-8 px-4 min-h-screen">
      {createChatMutation.isPending && (
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
          disabled={createChatMutation.isPending || sessionStatus !== 'authenticated'}
        >
          {createChatMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
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
            Unable to connect to the chat server. The FastAPI backend might not be running or is unresponsive.
          </p>
          <p className="text-red-700 text-sm mb-3">
            <b>Troubleshooting Tip:</b> Check the backend server logs by running the following command in your terminal: <code>docker-compose logs fastapi_app</code>
          </p>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
            >
              Retry Connection
            </Button>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {Array.isArray(chats) && chats.length === 0 && !isLoading && !isError && (
          <div className="text-center py-10">
            <p className="text-gray-500 mb-4">
              You don&apos;t have any chats yet.
            </p>
            <Button
              onClick={handleCreateChat}
              disabled={createChatMutation.isPending}
            >
              {createChatMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Start a new conversation"
              )}
            </Button>
          </div>
        )}

        {Array.isArray(chats) && chats.map(({ chat, latestMessage }) => (
          <Link key={chat.id} href={`/chats/${chat.id}`} passHref>
            <Card className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors cursor-pointer">
              <div>
                <div className="font-semibold">
                  {chat.title || `Chat #${chat.id.substring(0, 8)}`}
                </div>
                <div className="text-muted-foreground text-sm truncate max-w-xs">
                  {latestMessage?.content || "No messages yet"}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Last updated: {formatDistanceToNow(new Date(chat.updatedAt), { addSuffix: true })}
                </div>
              </div>
              <Button variant="outline" asChild>
                <span>Open</span>
              </Button>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}