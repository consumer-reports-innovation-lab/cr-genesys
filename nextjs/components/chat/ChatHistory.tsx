import React, { useState, useEffect, useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronRight } from "lucide-react";

export interface ChatMessage {
  id: string;
  content: string;
  sender: string;
  createdAt: Date;
  messageType?: 'user' | 'system' | 'agent_action' | 'agent_thinking';
}

interface ChatHistoryProps {
  messages: ChatMessage[];
  userInitials: string;
}

// --- NEW ANIMATION COMPONENT (No Framer Motion) ---
const SmoothReveal = ({ text }: { text: string }) => {
  const words = useMemo(() => text.split(' '), [text]);
  const [visibleWords, setVisibleWords] = useState(0);

  useEffect(() => {
    setVisibleWords(0); // Reset on text change
    const timer = setInterval(() => {
      setVisibleWords(prev => {
        if (prev < words.length) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, 60); // Adjust word reveal speed here

    return () => clearInterval(timer);
  }, [text, words.length]);

  return (
    <div className="flex flex-wrap">
      {words.map((word, index) => (
        <span
          key={index}
          className={`mr-[0.25em] transition-opacity duration-500 ${index < visibleWords ? 'opacity-100' : 'opacity-0'}`}
        >
          {word}
        </span>
      ))}
    </div>
  );
};


const ThinkingIndicator = () => (
  <div className="flex items-center space-x-1 p-2">
    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
    <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></span>
  </div>
);

const AgentThread = ({ messages }: { messages: ChatMessage[] }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (messages.length === 0) return null;

  const getAgentInfo = (sender: string) => {
    switch (sender) {
      case 'AskCR': return { name: 'Your CR Agent', color: 'bg-green-600', initial: 'CR' };
      case 'Genesys': return { name: 'Sharkninja', color: 'bg-purple-500', initial: 'S' };
      default: return { name: 'Agent', color: 'bg-gray-500', initial: 'A' };
    }
  };

  return (
    <div className="pl-12 py-2">
      <div className="relative border-l-2 border-gray-300 pl-6">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="absolute -left-[13px] top-1 flex items-center justify-center w-6 h-6 bg-white border-2 border-gray-300 rounded-full hover:bg-gray-100 transition-colors"
        >
          {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        
        {!isOpen && (
           <div className="text-sm text-gray-500 cursor-pointer" onClick={() => setIsOpen(true)}>
            {messages.length} agent messages...
           </div>
        )}
        
        {isOpen && (
          <div className="flex flex-col gap-4 pt-2 pb-1">
            {messages.map(msg => {
              const agentInfo = getAgentInfo(msg.sender);
              return (
                <div key={msg.id} className="flex items-start gap-3">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className={`${agentInfo.color} text-white text-xs`}>{agentInfo.initial}</AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col items-start">
                    <div className="text-sm font-semibold text-gray-800">{agentInfo.name}</div>
                    {msg.messageType === 'agent_thinking' ? <ThinkingIndicator /> : <div className="text-gray-600"><SmoothReveal text={msg.content} /></div>}
                    <span className="text-xs text-gray-400 mt-1">
                      {msg.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export function ChatHistory({ messages, userInitials }: ChatHistoryProps) {
  if (messages.length === 0) {
    return <div className="flex-1 flex items-center justify-center text-gray-400">Send a message to begin</div>;
  }
  
  const groupedMessages: (ChatMessage | { type: 'thread'; messages: ChatMessage[] })[] = [];
  let currentThread: ChatMessage[] = [];

  messages.forEach(msg => {
    if (msg.messageType === 'agent_action' || msg.messageType === 'agent_thinking') {
      currentThread.push(msg);
    } else {
      if (currentThread.length > 0) {
        groupedMessages.push({ type: 'thread', messages: currentThread });
        currentThread = [];
      }
      groupedMessages.push(msg);
    }
  });

  if (currentThread.length > 0) {
    groupedMessages.push({ type: 'thread', messages: currentThread });
  }

  return (
    <div className="flex flex-col gap-2 p-4">
      {groupedMessages.map((item, index) => {
        if ('type' in item && item.type === 'thread') {
          return <AgentThread key={`thread-${index}`} messages={item.messages} />;
        }
        
        const msg = item as ChatMessage;
        const isUser = msg.messageType === 'user';
        
        return (
          <div key={msg.id} className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}>
            {!isUser && (
              <Avatar className="w-10 h-10">
                <AvatarFallback className="bg-green-600 text-white font-bold">CR</AvatarFallback>
              </Avatar>
            )}
            <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-lg`}>
              <Card className={`px-4 py-2 rounded-lg ${isUser ? 'bg-indigo-500 text-white' : 'bg-green-50 text-gray-800'}`}>
                {isUser ? msg.content : <SmoothReveal text={msg.content} />}
              </Card>
              <span className="text-xs text-gray-400 mt-1 px-1">
                {msg.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            {isUser && (
              <Avatar className="w-10 h-10">
                <AvatarFallback className="bg-gray-700 text-white font-bold">{userInitials}</AvatarFallback>
              </Avatar>
            )}
          </div>
        );
      })}
    </div>
  );
}