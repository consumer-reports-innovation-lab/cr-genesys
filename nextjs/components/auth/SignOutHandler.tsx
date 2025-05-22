"use client";

import { signOut, useSession } from "next-auth/react";
import { useCallback, useEffect } from "react";
import { useMutation, UseMutationResult } from "@tanstack/react-query";

interface SignOutHandlerProps {
  children: React.ReactNode;
}

interface DeleteSessionsResponse {
  message: string;
}

/**
 * Custom sign-out handler that deletes sessions from the database
 */
export function SignOutHandler({ children }: SignOutHandlerProps) {
  const { data: session } = useSession();

  const deleteDeviceSessionsMutation: UseMutationResult<DeleteSessionsResponse, Error, string> = useMutation({
    mutationFn: async (deviceId: string): Promise<DeleteSessionsResponse> => {
      const response = await fetch(`/api/auth/session/device?deviceId=${deviceId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to delete device sessions");
      }
      return response.json();
    },
    onError: (error: Error) => {
      console.error("Failed to delete device sessions:", error.message);
      // Optionally, you can show a notification to the user here
    },
  });

  // Memoized sign out function using NextAuth
  const handleSignOut = useCallback(async () => {
    if (session?.deviceId) {
      try {
        await deleteDeviceSessionsMutation.mutateAsync(session.deviceId);
      } catch {
        // Error is already logged by onError in useMutation
        // You might want to prevent sign out or notify user differently here
      }
    }
    await signOut({ callbackUrl: "/login?logout=success" });
  }, [session, deleteDeviceSessionsMutation]);

  // Attach the custom signOut to window for global access
  useEffect(() => {
    // @ts-expect-error - Adding custom property to window
    window.customSignOut = handleSignOut;

    return () => {
      // @ts-expect-error - Clean up
      delete window.customSignOut;
    };
  }, [handleSignOut]);

  return (
    <>
      {deleteDeviceSessionsMutation.isPending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg p-6 shadow-md flex flex-col items-center">
            <svg className="animate-spin h-8 w-8 text-gray-700 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            <span className="text-gray-800">Signing out...</span>
          </div>
        </div>
      )}
      {children}
    </>
  );
}

export default SignOutHandler;
