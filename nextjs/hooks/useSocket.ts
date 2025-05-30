import {
  disconnectSocket,
  initSocket,
  joinRoom,
  leaveRoom,
  sendMessage,
} from "@/lib/socket";
import type { SocketType } from "@/lib/socket";
import { useCallback, useEffect, useRef } from "react";

interface UseSocketProps {
  onConnect?: () => void;
  onDisconnect?: () => void;
  events?: {
    [eventName: string]: (...args: unknown[]) => void;
  };
  url?: string;
  token?: string;
}

export const useSocket = ({
  onConnect,
  onDisconnect,
  events = {},
  url,
  token,
}: UseSocketProps = {}) => {
  const socketRef = useRef<SocketType | null>(null);

  // Initialize socket connection
  useEffect(() => {
    // Initialize socket with optional custom URL and token
    const socket = initSocket(url, token);
    socketRef.current = socket;

    if (!socket) return;

    // Set up event listeners
    if (onConnect) {
      socket.on("connect", onConnect);
    }

    if (onDisconnect) {
      socket.on("disconnect", onDisconnect);
    }

    // Set up custom event listeners
    Object.entries(events).forEach(([event, handler]) => {
      socket.on(event, handler);
    });

    // Cleanup function
    return () => {
      if (socket) {
        // Remove all event listeners
        socket.off("connect");
        socket.off("disconnect");

        // Remove custom event listeners
        Object.keys(events).forEach((event) => {
          socket.off(event);
        });

        // Disconnect if no other components are using the socket
        if (socket.connected) {
          disconnectSocket();
        }
      }
    };
  }, [onConnect, onDisconnect, events, url]);

  // Helper function to emit events
  const emit = useCallback((event: string, ...args: unknown[]) => {
    if (socketRef.current) {
      socketRef.current.emit(event, ...args);
    } else {
      console.error("Socket not connected");
    }
  }, []);

  // Helper functions that use the socket instance
  const sendMessageToServer = useCallback((chatId: string, message: string) => {
    if (socketRef.current) {
      sendMessage(chatId, message);
    } else {
      console.error("Socket not connected");
    }
  }, []);

  const joinRoomInServer = useCallback((roomName: string) => {
    if (socketRef.current) {
      joinRoom(roomName);
    } else {
      console.error("Socket not connected");
    }
  }, []);

  const leaveRoomInServer = useCallback((roomName: string) => {
    if (socketRef.current) {
      leaveRoom(roomName);
    } else {
      console.error("Socket not connected");
    }
  }, []);

  return {
    socket: socketRef.current,
    emit,
    connected: socketRef.current?.connected || false,
    sendMessage: sendMessageToServer,
    joinRoom: joinRoomInServer,
    leaveRoom: leaveRoomInServer,
  };
};
