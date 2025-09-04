// cr-genesys/nextjs/schemas.ts
import type { Chat as PrismaChat, Message as PrismaMessage } from "@prisma/client";

export type Message = PrismaMessage;

export type Chat = PrismaChat;

export type ChatWithLatestMessage = {
  chat: PrismaChat;
  latestMessage: PrismaMessage | null;
};