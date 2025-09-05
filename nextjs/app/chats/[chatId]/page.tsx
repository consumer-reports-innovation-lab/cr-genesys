"use client";
import { ChatHistory, ChatInput } from "@/components/chat";
import type { ChatMessage } from "@/components/chat";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const createUIMessage = (
  sender: string,
  content: string,
  messageType: ChatMessage['messageType']
): ChatMessage => ({
  id: crypto.randomUUID(),
  sender,
  content,
  messageType,
  createdAt: new Date(),
});

type ConversationState = 'start' | 'awaiting_model_number' | 'completed';

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { data: session } = useSession();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const [conversationState, setConversationState] = useState<ConversationState>('start');
  const [isAgentReplying, setIsAgentReplying] = useState(false);

  const userInitials = session?.user?.name
    ? session.user.name.split(' ').map(n => n[0]).join('')
    : 'U';

  // --- LOCAL STORAGE: Load messages on initial render ---
  useEffect(() => {
    if (typeof window !== 'undefined' && chatId) {
      const savedMessages = localStorage.getItem(`chat_${chatId}`);
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages).map((msg: ChatMessage) => ({
          ...msg,
          createdAt: new Date(msg.createdAt),
        }));
        setMessages(parsedMessages);
      }
    }
  }, [chatId]);

  // --- LOCAL STORAGE: Save messages whenever they change ---
  useEffect(() => {
    if (typeof window !== 'undefined' && chatId && messages.length > 0) {
      localStorage.setItem(`chat_${chatId}`, JSON.stringify(messages));
    }
  }, [messages, chatId]);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  };

  const agentReply = async (sender: string, content: string, thinkTime: number) => {
    const thinkingMessage = createUIMessage(sender, "Thinking", "agent_thinking");
    addMessage(thinkingMessage);
    await new Promise(resolve => setTimeout(resolve, thinkTime));
    
    setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id));
    addMessage(createUIMessage(sender, content, "agent_action"));
    
    const wordCount = content.split(' ').length;
    const animationDuration = wordCount * 60 + 1000;
    await new Promise(resolve => setTimeout(resolve, animationDuration));
  };

  const systemReplyToUser = async (content: string) => {
      addMessage(createUIMessage("AskCR", content, "system"));
      const wordCount = content.split(' ').length;
      const animationDuration = wordCount * 60 + 1000;
      await new Promise(resolve => setTimeout(resolve, animationDuration));
  }

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isAgentReplying) return;

    setIsAgentReplying(true);
    addMessage(createUIMessage("user", content, "user"));
    await new Promise(resolve => setTimeout(resolve, 500));

    if (conversationState === 'start') {
      setConversationState('awaiting_model_number');

      await agentReply("AskCR", "On it! Let me connect with Sharkninja's support system for you.", 2000);
      await agentReply("AskCR", "Okay, I'm connected. Submitting your feedback about the packaging.", 1800);
      
      await agentReply("Genesys", "Thank you for contacting Sharkninja. To process your feedback, please provide the customer's full name and email address for verification.", 3000);
      
      await agentReply("AskCR", "Of course. The customer is Kennion Gubler, email kennion.gubler@example.com.", 2000);
      
      await agentReply("Genesys", "Verification successful. Please provide the product name and purchase date.", 3500);

      await agentReply("AskCR", "The product is a 'Sharkninja Pro Blender'. Checking purchase history... purchased on August 15, 2025.", 2500);
      
      await agentReply("Genesys", "Information confirmed. For feedback related to `Packaging`, a product model number is required for our engineering and logistics teams. Please provide the model number.", 4000);

      await agentReply("AskCR", "Got it. I don't have the model number in the purchase record. I'll ask the user for it now.", 1500);

      await systemReplyToUser("The Sharkninja system needs a model number to file the feedback. Could you provide it for me, please? It's usually on the bottom of the blender.");

    } else if (conversationState === 'awaiting_model_number') {
      setConversationState('completed');
      
      await agentReply("AskCR", `Perfect, thank you! I'll pass this along. The model number is ${content}.`, 2500);
      
      const ticketId = `SN-${Math.floor(Math.random() * 90000) + 10000}`;
      await agentReply("Genesys", `Model number ${content} accepted. Your feedback has been logged. Your ticket ID is ${ticketId}. Do you require further assistance?`, 3500);
      
      await agentReply("AskCR", "That's everything, thank you for your help!", 2000);

      await systemReplyToUser(`All set! Your feedback is officially submitted to Sharkninja. The reference number is ${ticketId}. Thanks for helping me out! ✨`);
    }
    setIsAgentReplying(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-49px)] bg-white">
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        <div className="pt-4 pb-32 sm:pb-24">
          <ChatHistory messages={messages} userInitials={userInitials} isAgentReplying={isAgentReplying} />
        </div>
      </div>
      <div className="px-3 py-2 sm:px-4 sm:py-3 border-t bg-gray-50">
        <ChatInput onSendMessage={handleSendMessage} disabled={isAgentReplying} />
      </div>
    </div>
  );
}