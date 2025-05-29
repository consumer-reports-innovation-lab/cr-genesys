// Import the socket.io-client library
import io from 'socket.io-client';

// Define the response interface for socket operations
export interface SocketResponse<T = unknown> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
}

// Define the socket type
export type SocketType = ReturnType<typeof io>;

// Create a singleton socket instance
let socket: SocketType | null = null;

/**
 * Initialize the WebSocket connection
 * @param url Optional WebSocket server URL
 * @returns The socket instance
 */
/**
 * Initialize the WebSocket connection
 * @param url Optional WebSocket server URL
 * @returns The socket instance
 */
/**
 * Initialize the WebSocket connection
 * @param url Optional WebSocket server URL
 * @returns The socket instance
 */
/**
 * Initialize the WebSocket connection
 * @param url Optional WebSocket server URL
 * @returns The socket instance
 */
/**
 * Initialize the WebSocket connection
 * @param url Optional WebSocket server URL
 * @returns The socket instance
 */
export const initSocket = (url?: string): SocketType | null => {
  if (!socket) {
    const envSocketUrl = process.env.NEXT_PUBLIC_SOCKET_URL;
    const socketUrl = url || (typeof envSocketUrl === 'string' ? envSocketUrl.replace('http', 'ws') : undefined) || 'ws://localhost:8000';
    
    try {
      socket = io(socketUrl, {
        path: '/ws/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 20000,
        autoConnect: true,
      });

      socket.on('connect', () => {
        console.log('Connected to WebSocket server with ID:', socket?.id);
      });

      socket.on('disconnect', (reason: string) => {
        console.log('Disconnected from WebSocket server:', reason);
      });

      socket.on('connect_error', (error: Error) => {
        console.error('WebSocket connection error:', error);
      });
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      throw error;
    }
  }
  
  return socket;
};

/**
 * Get the current socket instance
 * @returns The socket instance or null if not initialized
 */
export const getSocket = (): SocketType | null => {
  return socket;
};

/**
 * Disconnect the WebSocket connection
 */
export const disconnectSocket = (): void => {
  if (socket) {
    socket.disconnect();
    socket = null;
    console.log('WebSocket connection closed');
  }
};

/**
 * Send a chat message
 * @param chatId The ID of the chat
 * @param content The message content
 * @returns A promise that resolves with the server response
 */
export const sendMessage = async (
  chatId: string,
  content: string
): Promise<SocketResponse<{ message_id: string }>> => {
  const socket = getSocket();
  if (!socket) {
    return { status: 'error', message: 'Socket not initialized' };
  }

  return new Promise<SocketResponse<{ message_id: string }>>((resolve) => {
    socket.emit(
      'message',
      { chat_id: chatId, content },
      (response: SocketResponse<{ message_id: string }>) => {
        resolve(response);
      }
    );
  });
};

/**
 * Join a chat room
 * @param chatId The ID of the chat room to join
 * @returns A promise that resolves with the server response
 */
export const joinRoom = async (chatId: string): Promise<SocketResponse<{ room: string }>> => {
  const socket = getSocket();
  if (!socket) {
    return { status: 'error', message: 'Socket not initialized' };
  }

  return new Promise<SocketResponse<{ room: string }>>((resolve) => {
    socket.emit(
      'join',
      { chat_id: chatId },
      (response: SocketResponse<{ room: string }>) => {
        if (response.status === 'success') {
          console.log(`Joined chat room: ${chatId}`);
        } else {
          console.error(`Failed to join room ${chatId}:`, response.message);
        }
        resolve(response);
      }
    );
  });
};

/**
 * Leave a chat room
 * @param chatId The ID of the chat room to leave
 * @returns A promise that resolves with the server response
 */
export const leaveRoom = async (chatId: string): Promise<SocketResponse> => {
  const socket = getSocket();
  if (!socket) {
    return { status: 'error', message: 'Socket not initialized' };
  }

  return new Promise<SocketResponse>((resolve) => {
    socket.emit(
      'leave',
      { chat_id: chatId },
      (response: SocketResponse) => {
        if (response.status === 'success') {
          console.log(`Left chat room: ${chatId}`);
        } else {
          console.error(`Failed to leave room ${chatId}:`, response.message);
        }
        resolve(response);
      }
    );
  });
};

/**
 * Emit a custom event with acknowledgment
 * @param event The event name
 * @param data The data to send
 * @returns A promise that resolves with the server response
 */
export const emitWithAck = async <T = unknown>(
  event: string,
  data: unknown = {}
): Promise<SocketResponse<T>> => {
  const socket = getSocket();
  if (!socket) {
    return { status: 'error', message: 'Socket not initialized' };
  }

  return new Promise<SocketResponse<T>>((resolve) => {
    socket.emit(
      event,
      data,
      (response: SocketResponse<T>) => {
        resolve(response);
      }
    );
  });
};
