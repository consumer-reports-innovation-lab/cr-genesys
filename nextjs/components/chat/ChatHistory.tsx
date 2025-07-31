import React from "react";
import { Avatar } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";

export interface ChatMessage {
  id: string;
  content: string;
  sender: string;
  createdAt: Date;
  sentToGenesys?: boolean;
  messageType?: 'user' | 'system' | 'system_to_genesys' | 'genesys';
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
        const messageType = msg.messageType || (msg.sender === "user" ? "user" : "system");
        
        // Determine styling based on message type
        const getMessageStyling = () => {
          switch (messageType) {
            case 'user':
              return {
                justify: "justify-end",
                avatar: senderInitial,
                avatarClass: "",
                cardClass: "max-w-xs bg-primary text-primary-foreground",
                textClass: "",
                showAvatar: true,
                avatarPosition: "right",
                indicator: null
              };
            case 'system':
              return {
                justify: "justify-start",
                avatar: "AI",
                avatarClass: "",
                cardClass: "max-w-xs bg-blue-100 text-blue-900 border-blue-200",
                textClass: "",
                showAvatar: true,
                avatarPosition: "left",
                indicator: null
              };
            case 'system_to_genesys':
              return {
                justify: "justify-start",
                avatar: "→G",
                avatarClass: "h-6 w-6 text-xs",
                cardClass: "max-w-sm bg-gray-50 text-gray-600 border-gray-200 text-sm",
                textClass: "text-sm italic",
                showAvatar: true,
                avatarPosition: "left",
                indicator: "→ Genesys"
              };
            case 'genesys':
              return {
                justify: "justify-start",
                avatar: "G",
                avatarClass: "h-6 w-6 text-xs bg-gray-200 text-gray-600",
                cardClass: "max-w-sm bg-gray-100 text-gray-700 border-gray-200 text-sm",
                textClass: "text-sm italic",
                showAvatar: true,
                avatarPosition: "left",
                indicator: "← Genesys"
              };
            default:
              return {
                justify: "justify-start",
                avatar: senderInitial,
                avatarClass: "",
                cardClass: "max-w-xs bg-muted",
                textClass: "",
                showAvatar: true,
                avatarPosition: "left",
                indicator: null
              };
          }
        };

        const styling = getMessageStyling();
        
        return (
          <div key={msg.id} className={`flex items-end gap-2 ${styling.justify}`}>
            {styling.showAvatar && styling.avatarPosition === "left" && (
              <Avatar className={styling.avatarClass}>
                {styling.avatar}
              </Avatar>
            )}
            <Card className={`px-3 py-2 rounded-lg ${styling.cardClass}`}>
              <div className={styling.textClass}>{msg.content}</div>
              <div className="text-xs text-muted-foreground mt-1 text-right">
                {styling.indicator && <span className="text-xs text-gray-400 mr-1">{styling.indicator}</span>}
                {msg.createdAt ? msg.createdAt.toLocaleTimeString() : "Unknown time"}
              </div>
            </Card>
            {styling.showAvatar && styling.avatarPosition === "right" && (
              <Avatar className={styling.avatarClass}>
                {styling.avatar}
              </Avatar>
            )}
          </div>
        );
      }).filter(Boolean)}
    </div>
  );
}
