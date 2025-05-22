import { Socket } from "socket.io-client";
import io from "socket.io-client";

// Define the SocketClient type for export
export type SocketClient = typeof Socket;

// Create a singleton socket instance
let socket: ReturnType<typeof io> | null = null;

// Initialize the socket connection
export const initSocket = (
  url: string = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3000"
) => {
  if (!socket) {
    socket = io(url, {
      transports: ["websocket", "polling"], // Support both transport methods
      reconnection: true,                   // Enable reconnection
      reconnectionAttempts: 5,              // Number of reconnection attempts
      reconnectionDelay: 1000,              // Initial delay before reconnection (ms)
      timeout: 20000,                       // Connection timeout (ms)
      autoConnect: true,                    // Auto connect on initialization
    });

    // Connection event handlers
    socket.on("connect", () => {
      console.log("Connected to server with ID:", socket?.id);
    });

    socket.on("disconnect", (reason: string) => {
      console.log("Disconnected from server:", reason);
    });

    socket.on("connect_error", (error: Error) => {
      console.error("Connection error:", error.message);
    });

    // Default event handlers for common events
    socket.on("message", (data: Record<string, unknown>) => {
      console.log("Received message:", data);
    });

    socket.on("notification", (data: Record<string, unknown>) => {
      console.log("Notification received:", data);
    });
  }
  return socket;
};

// Get the socket instance
export const getSocket = (): ReturnType<typeof io> | null => {
  return socket;
};

// Disconnect the socket
export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

// Helper functions for common socket operations

// Send a message to the server
export const sendMessage = (message: string) => {
  if (socket) {
    socket.emit("sendMessage", { text: message, timestamp: new Date() });
  } else {
    console.error("Socket not connected");
  }
};

// Join a room
export const joinRoom = (roomName: string) => {
  if (socket) {
    socket.emit("joinRoom", { room: roomName });
  } else {
    console.error("Socket not connected");
  }
};

// Leave a room
export const leaveRoom = (roomName: string) => {
  if (socket) {
    socket.emit("leaveRoom", { room: roomName });
  } else {
    console.error("Socket not connected");
  }
};
