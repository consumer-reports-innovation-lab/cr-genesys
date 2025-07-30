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
  // Safeguard against undefined messages
  if (!messages || !Array.isArray(messages)) {
    return <div className="flex flex-col gap-2 p-4">No messages</div>;
  }

  return (
    <div className="flex flex-col gap-2 p-4">
      {messages.map((msg) => {
        // Safeguard against undefined message properties
        if (!msg || !msg.id || !msg.sender || !msg.content) {
          return null;
        }

        const senderInitial = msg.sender && msg.sender.length > 0 ? msg.sender[0].toUpperCase() : "?";
        
        return (
          <div key={msg.id} className={`flex items-end gap-2 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
            {msg.sender !== "user" && <Avatar>{senderInitial}</Avatar>}
            <Card className={`px-3 py-2 rounded-lg max-w-xs ${msg.sender === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
              <div>{msg.content}</div>
              <div className="text-xs text-muted-foreground mt-1 text-right">
                {msg.createdAt ? msg.createdAt.toLocaleTimeString() : "Unknown time"}
              </div>
            </Card>
            {msg.sender === "user" && <Avatar>{senderInitial}</Avatar>}
          </div>
        );
      }).filter(Boolean)}
    </div>
  );
}
