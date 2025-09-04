'use client';

import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send } from 'lucide-react';
import { type ChangeEvent, type FormEvent, useState } from 'react';

// Define the shape of a message object
type Message = {
  name: string;
  message: string;
  isUser?: boolean; // Flag to identify user's own messages
};

// Define the props for the Chat component
type ChatProps = {
  messages: Message[];
  input: string;
  handleInputChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
};

export const Chat = ({
  messages,
  input,
  handleInputChange,
  handleSubmit,
  isLoading,
}: ChatProps) => {
  const [isSending, setIsSending] = useState(false);

  // Wrapper for the submit handler to manage the sending state
  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    setIsSending(true);
    handleSubmit(e);
    setIsSending(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable chat history */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              'flex items-start gap-3',
              m.isUser && 'flex-row-reverse', // Align user messages to the right
            )}
          >
            {/* Avatar */}
            <Avatar className="w-8 h-8">
              <AvatarImage />
              <AvatarFallback>
                {m.name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')}
              </AvatarFallback>
            </Avatar>

            {/* Message Bubble */}
            <div
              className={cn(
                'rounded-lg p-3 max-w-xs',
                // --- DIAGNOSTIC UI CHANGE ---
                // Applying a bright pink background to user messages
                m.isUser
                  ? 'bg-pink-500 text-white' // User's message style
                  : 'bg-gray-200', // Other messages' style
              )}
            >
              <p className="font-semibold text-sm">{m.name}</p>
              <p className="text-sm">{m.message}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Message input form */}
      <form
        onSubmit={onSubmit}
        className="border-t p-4 flex items-center gap-2"
      >
        <Input
          value={input}
          placeholder="Type a message..."
          onChange={handleInputChange}
          className="flex-1"
        />
        <Button type="submit" size="icon" disabled={isLoading || isSending}>
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
};
