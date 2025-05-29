"use client";
import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { createChatMessage } from "@/utils/api";
import { useSession } from "next-auth/react";

interface ChatInputProps {
  chatId: string;
  onNewMessage: () => void;
  disabled?: boolean;
}

export function ChatInput({ chatId, onNewMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const { data: session } = useSession();

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    try {
      // You can adjust systemPrompt as needed or make it a prop
      const systemPrompt = "default system prompt";
      await createChatMessage(chatId, systemPrompt, message, session);
      setMessage("");
    } catch (error) {
      // Optionally handle error (toast, etc)
      console.error(error);
    } finally {
      setLoading(false);
      onNewMessage();
    }
  };

  return (
    <form onSubmit={handleSend} className="flex gap-2 items-center w-full">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
        disabled={loading || disabled}
        className="flex-1"
      />
      <Button type="submit" disabled={loading || !message.trim() || disabled}>
        Send
      </Button>
    </form>
  );
}
