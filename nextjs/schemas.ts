// cr-genesys/nextjs/schemas.ts

export type Message = {
  id: string;
  content: string;
  chatId: string;
  isSystem: boolean;
  isMarkdown: boolean;
  sentToGenesys: boolean;
  genesysMessageId: string | null;
  messageType: string;
  createdAt: Date;
  updatedAt: Date;
};

export type Chat = {
  id: string;
  title: string | null;
  status: 'OPEN' | 'CLOSED';
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  genesysOpenMessageSessionId: string | null;
  genesysOpenMessageActive: boolean;
};

export type ChatWithLatestMessage = {
  chat: Chat;
  latestMessage: Message | null;
};