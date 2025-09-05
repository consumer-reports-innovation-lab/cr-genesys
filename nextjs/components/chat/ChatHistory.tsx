import React, { useState, useEffect, useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
  isAgentReplying?: boolean;
}

const SmoothReveal = ({ text }: { text: string }) => {
  const words = useMemo(() => text.split(' '), [text]);
  const [visibleWords, setVisibleWords] = useState(0);

  useEffect(() => {
    setVisibleWords(0);
    const timer = setInterval(() => {
      setVisibleWords(prev => {
        if (prev < words.length) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, 60); 

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

const ConversingAvatars = ({ onClick }: { onClick: () => void }) => {
  const statusText = "Chatting with Made In...";

  return (
    <div className="flex items-center gap-3 cursor-pointer" onClick={onClick}>
      <div className="flex -space-x-2">
        <motion.div
           animate={{ x: [0, -4, 0], scale: [1, 1.05, 1] }}
           transition={{ duration: 1.5, repeat: Infinity, repeatType: "mirror" }}
        >
            <Avatar className="w-6 h-6 sm:w-8 sm:h-8 border-2 border-white">
                <AvatarFallback className="bg-green-600 text-white text-xs">CR</AvatarFallback>
            </Avatar>
        </motion.div>
        <motion.div
            animate={{ x: [0, 4, 0], scale: [1, 1.05, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, repeatType: "mirror", delay: 0.2 }}
        >
            <Avatar className="w-6 h-6 sm:w-8 sm:h-8 border-2 border-white">
                <AvatarFallback className="bg-blue-600 text-white text-xs">MI</AvatarFallback>
            </Avatar>
        </motion.div>
      </div>
      <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-500">
         <AnimatePresence mode="wait">
            <motion.span
                key={statusText}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.3 }}
            >
                {statusText}
            </motion.span>
        </AnimatePresence>
      </div>
    </div>
  );
};

const CollapsedThreadSummary = ({ messages, onClick }: { messages: ChatMessage[], onClick: () => void }) => {
  return (
    <div className="flex items-center gap-3 cursor-pointer" onClick={onClick}>
      <div className="flex items-center -space-x-2">
        <Avatar className="w-6 h-6 sm:w-8 sm:h-8 border-2 border-white">
          <AvatarFallback className="bg-green-600 text-white text-xs">CR</AvatarFallback>
        </Avatar>
        <Avatar className="w-6 h-6 sm:w-8 sm:h-8 border-2 border-white">
          <AvatarFallback className="bg-blue-600 text-white text-xs">MI</AvatarFallback>
        </Avatar>
      </div>
      <div className="text-xs sm:text-sm text-gray-500">
        <span>Agent Conversation ({messages.length} messages)</span>
      </div>
    </div>
  )
}

interface AgentThreadProps {
  messages: ChatMessage[];
  isCurrentlyActive: boolean;
}

const AgentThread = ({ messages, isCurrentlyActive }: AgentThreadProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const getAgentInfo = (sender: string) => {
    switch (sender) {
      case 'AskCR': return { name: 'Your Agent', color: 'bg-green-600', initial: 'CR' };
      case 'Genesys': return { name: 'Made In System', color: 'bg-blue-600', initial: 'MI' };
      default: return { name: 'Agent', color: 'bg-gray-500', initial: 'A' };
    }
  };
  
  if (messages.length === 0) return null;

  return (
    <div className="pl-8 sm:pl-12 py-2">
      <div className="relative border-l-2 border-gray-300 pl-4 sm:pl-6">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="absolute -left-3.5 top-1 flex items-center justify-center w-6 h-6 bg-white border-2 border-gray-300 rounded-full hover:bg-gray-100 transition-colors z-10"
        >
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        
        {!isOpen ? (
          isCurrentlyActive ? (
            <ConversingAvatars onClick={() => setIsOpen(true)} />
          ) : (
            <CollapsedThreadSummary messages={messages} onClick={() => setIsOpen(true)} />
          )
        ) : (
          <div className="flex flex-col gap-3 sm:gap-4 pt-2 pb-1">
            {messages.map(msg => {
              const agentInfo = getAgentInfo(msg.sender);
              return (
                <div key={msg.id} className="flex items-start gap-2 sm:gap-3">
                  <Avatar className="w-6 h-6 sm:w-8 sm:h-8 flex-shrink-0">
                    <AvatarFallback className={`${agentInfo.color} text-white text-xs`}>{agentInfo.initial}</AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col items-start min-w-0 flex-1">
                    <div className="text-xs sm:text-sm font-semibold text-gray-800">{agentInfo.name}</div>
                    {msg.messageType === 'agent_thinking' ? <ThinkingIndicator /> : <div className="text-gray-600 text-sm sm:text-base"><SmoothReveal text={msg.content} /></div>}
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

export function ChatHistory({ messages, userInitials, isAgentReplying = false }: ChatHistoryProps) {
  if (messages.length === 0) {
    return <div className="h-full flex items-center justify-center text-gray-400">Send a message to begin</div>;
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
    <div className="flex flex-col gap-2">
      {groupedMessages.map((item, index) => {
        if ('type' in item && item.type === 'thread') {
          const isCurrentlyActive = isAgentReplying && index === groupedMessages.length - 1;
          return <AgentThread key={`thread-${index}`} messages={item.messages} isCurrentlyActive={isCurrentlyActive} />;
        }
        
        const msg = item as ChatMessage;
        const isUser = msg.messageType === 'user';
        
        return (
          <div key={msg.id} className={`flex items-start gap-2 sm:gap-3 ${isUser ? 'justify-end' : ''}`}>
            {!isUser && (
              <Avatar className="w-8 h-8 sm:w-10 sm:h-10 flex-shrink-0">
                <AvatarFallback className="bg-green-600 text-white font-bold text-xs sm:text-sm">CR</AvatarFallback>
              </Avatar>
            )}
            <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-lg`}>
              <Card className={`px-3 py-2 sm:px-4 sm:py-2 rounded-lg text-sm sm:text-base ${isUser ? 'bg-indigo-500 text-white' : 'bg-green-50 text-gray-800'}`}>
                {isUser ? msg.content : <SmoothReveal text={msg.content} />}
              </Card>
              <span className="text-xs text-gray-400 mt-1 px-1">
                {msg.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            {isUser && (
              <Avatar className="w-8 h-8 sm:w-10 sm:h-10 flex-shrink-0">
                <AvatarFallback className="bg-gray-700 text-white font-bold text-xs sm:text-sm">{userInitials}</AvatarFallback>
              </Avatar>
            )}
          </div>
        );
      })}
    </div>
  );
}