"use client";
import React, { useState } from "react";
import TextareaAutosize from 'react-textarea-autosize';
import { Button } from "@/components/ui/button";
import { SendHorizonal } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  
  const handleSend = async () => {
    if (!message.trim() || disabled) return;
    
    // Keep the original message to send, then clear the input
    const messageToSend = message;
    setMessage("");
    await onSendMessage(messageToSend);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2 sm:gap-3 items-end w-full">
      <TextareaAutosize
        value={message}
        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Send a message..."
        disabled={disabled}
        minRows={1}
        maxRows={5}
        className="flex-1 resize-none rounded-full border border-input bg-white px-4 py-2 text-sm sm:text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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