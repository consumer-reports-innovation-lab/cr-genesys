"use client";
import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SendHorizonal } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || disabled) return;
    
    // Keep the original message to send, then clear the input
    const messageToSend = message;
    setMessage("");
    await onSendMessage(messageToSend);
  };

  return (
    <form onSubmit={handleSend} className="flex gap-2 sm:gap-3 items-center w-full">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Send a message..."
        disabled={disabled}
        className="flex-1 bg-white h-10 rounded-full px-4 text-sm sm:text-base"
      />
      <Button
        type="submit"
        disabled={disabled || !message.trim()}
        className="bg-indigo-500 hover:bg-indigo-600 text-white rounded-full w-10 h-10 p-2 shrink-0"
        aria-label="Send message"
      >
        <SendHorizonal size={20} />
      </Button>
    </form>
  );
}