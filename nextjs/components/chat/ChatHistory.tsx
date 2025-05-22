import React from "react";
import { Avatar } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";

export interface ChatMessage {
  id: string;
  content: string;
  sender: string;
  createdAt: Date;
}

interface ChatHistoryProps {
  messages: ChatMessage[];
}

export function ChatHistory({ messages }: ChatHistoryProps) {
  return (
    <div className="flex flex-col gap-2 p-4">
      {messages.map((msg) => (
        <div key={msg.id} className={`flex items-end gap-2 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
          {msg.sender !== "user" && <Avatar>{msg.sender[0].toUpperCase()}</Avatar>}
          <Card className={`px-3 py-2 rounded-lg max-w-xs ${msg.sender === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
            <div>{msg.content}</div>
            <div className="text-xs text-muted-foreground mt-1 text-right">
              {msg.createdAt.toLocaleTimeString()}
            </div>
          </Card>
          {msg.sender === "user" && <Avatar>{msg.sender[0].toUpperCase()}</Avatar>}
        </div>
      ))}
    </div>
  );
}
