/**
 * API utility functions for communicating with the FastAPI backend
 */

import type { Chat, Message } from "@prisma/client";
import { Session } from "next-auth";

// API Configuration
const API_ENV = process.env.NODE_ENV || "development";

// Determine if running on server or client
const IS_SERVER = typeof window === "undefined";

// Base API URL based on environment and execution context
const API_BASE_URLS = {
  development_server: process.env.INTERNAL_API_URL || "http://web:8000", // Fallback to web:8000 for Docker dev
  development_client:
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000", // Fallback for client dev
  test: process.env.INTERNAL_API_URL || "http://fastapi:8000", // For test environment, likely server-side
  production:
    process.env.NEXT_PUBLIC_API_URL || "https://api.consumerreports.org", // Production URL for client/server if not distinguished
};

let determinedApiBaseUrl: string;

if (IS_SERVER) {
  if (API_ENV === "production") {
    determinedApiBaseUrl = API_BASE_URLS.production;
  } else if (API_ENV === "test") {
    determinedApiBaseUrl = API_BASE_URLS.test;
  } else {
    // development or other server environments
    determinedApiBaseUrl = API_BASE_URLS.development_server;
  }
} else {
  // Client-side
  if (API_ENV === "production") {
    determinedApiBaseUrl = API_BASE_URLS.production;
  } else {
    // development or other client environments
    determinedApiBaseUrl = API_BASE_URLS.development_client;
  }
}

const API_BASE_URL = determinedApiBaseUrl;

// Extend Prisma types with any additional fields we need
export type ChatWithMessages = Chat & {
  messages?: Message[];
  latestMessage?: Message;
};

// Custom error types for better error handling
export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export class NetworkError extends ApiError {
  constructor(message: string = "Network error occurred") {
    super(message, 0);
    this.name = "NetworkError";
  }
}

export class AuthError extends ApiError {
  constructor(message: string = "Authentication error") {
    super(message, 401);
    this.name = "AuthError";
  }
}

/**
 * Helper to handle API errors consistently with typed errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const errorMessage =
      errorData?.detail ||
      `API Error: ${response.status} ${response.statusText}`;

    // Handle specific error types
    if (response.status === 401 || response.status === 403) {
      throw new AuthError(errorMessage);
    }

    throw new ApiError(errorMessage, response.status, errorData);
  }

  return response.json() as Promise<T>;
}

/**
 * Get the authorization header using the session
 */
function getAuthHeader(session: Session | null): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  
  if (session) {
    headers["Authorization"] = `Bearer ${session.accessToken}`;
  }

  return headers;
}

/**
 * Fetch wrapper with error handling and retry logic
 */
async function fetchWithRetry<T>(
  url: string,
  options: RequestInit,
  retries: number = 1
): Promise<T> {
  try {
    const response = await fetch(url, options);
    return await handleResponse<T>(response);
  } catch (error) {
    if (retries > 0 && error instanceof NetworkError) {
      // Wait before retrying (exponential backoff)
      await new Promise((resolve) =>
        setTimeout(resolve, 1000 * 2 ** (2 - retries))
      );
      return fetchWithRetry<T>(url, options, retries - 1);
    }
    throw error;
  }
}

/**
 * Get all chats for the current user
 */
export async function getUserChats(
  session: Session | null
): Promise<{ chat: ChatWithMessages; latestMessage: Message }[]> {
  return fetchWithRetryAndCamel<
    { chat: ChatWithMessages; latestMessage: Message }[]
  >(`${API_BASE_URL}/chats`, {
    method: "GET",
    headers: getAuthHeader(session),
  });
}

/**
 * Create a new chat
 */
// Utility to convert snake_case to camelCase
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

// Recursively convert object keys to camelCase
function convertKeysToCamelCase(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(convertKeysToCamelCase);
  } else if (obj && typeof obj === "object" && obj.constructor === Object) {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        snakeToCamel(key),
        convertKeysToCamelCase(value),
      ])
    );
  }
  return obj;
}

// Wrap fetchWithRetry to apply camelCase conversion for API_BASE_URL
async function fetchWithRetryAndCamel<T>(
  url: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetchWithRetry<T>(url, init || {});
  // Only convert if URL matches API_BASE_URL
  if (url.startsWith(API_BASE_URL) && res && typeof res === "object") {
    return convertKeysToCamelCase(res) as T;
  }
  return res;
}

export async function createChat(
  session: Session | null
): Promise<ChatWithMessages> {
  return fetchWithRetryAndCamel<ChatWithMessages>(`${API_BASE_URL}/chats`, {
    method: "POST",
    headers: getAuthHeader(session),
  });
}

interface GetChatOptions {
  includeChatHistory?: boolean;
}

/**
 * Get a specific chat by ID
 * @param chatId - The ID of the chat to retrieve
 * @param session - The current user session
 * @param options - Optional parameters
 * @param options.includeChatHistory - Whether to include chat messages in the response (default: true)
 */
export async function getChat(
  chatId: string,
  session: Session | null,
  { includeChatHistory }: GetChatOptions = {}
): Promise<{ chat: ChatWithMessages }> {
  const url = new URL(`${API_BASE_URL}/chats/${chatId}`);

  // Only append the parameter if it's explicitly set to true or false
  if (includeChatHistory !== undefined) {
    url.searchParams.append(
      "include_chat_history",
      includeChatHistory.toString()
    );
  }

  return fetchWithRetryAndCamel<{ chat: ChatWithMessages }>(url.toString(), {
    method: "GET",
    headers: getAuthHeader(session),
  });
}

/**
 * Get all messages for a specific chat
 */
export async function getChatMessages(
  chatId: string,
  session: Session | null
): Promise<Message[]> {
  return fetchWithRetryAndCamel<Message[]>(
    `${API_BASE_URL}/chats/${chatId}/messages`,
    {
      method: "GET",
      headers: getAuthHeader(session),
    }
  );
}

/**
 * Create a new message in a chat
 */
export async function createChatMessage(
  chatId: string,
  systemPrompt: string,
  question: string,
  session: Session | null
): Promise<Message> {
  const body = JSON.stringify({
    system_prompt: systemPrompt,
    question: question,
  });

  return fetchWithRetryAndCamel<Message>(
    `${API_BASE_URL}/chats/${chatId}/messages`,
    {
      method: "POST",
      headers: {
        ...getAuthHeader(session),
        "Content-Type": "application/json",
      },
      body,
    }
  );
}

/**
 * Get PureCloud permissions
 */
export async function getPureCloudPermissions(
  session: Session | null
): Promise<unknown> {
  return fetchWithRetry<unknown>(`${API_BASE_URL}/purecloud/permissions`, {
    method: "GET",
    headers: getAuthHeader(session),
  });
}
