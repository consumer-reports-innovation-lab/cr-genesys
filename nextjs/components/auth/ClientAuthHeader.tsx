'use client';

import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';

export default function ClientAuthHeader() {
  const { data: session, status } = useSession();
  const isAuthenticated = status === 'authenticated';

  const handleSignOut = async () => {
    // Use the custom signOut handler if available, otherwise fall back to standard signOut
    if (typeof window !== 'undefined') {
      // @ts-expect-error - Custom property added by SignOutHandler
      if (window.customSignOut) {
        // @ts-expect-error - Custom property
        await window.customSignOut();
        return;
      }
    }
    
    // Default fallback
    await signOut({ callbackUrl: "/login" });
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <header className="w-full bg-white border-b border-gray-200 py-3 px-4 flex items-center">
      <div className="w-1/3">
        <Link href="/" className="font-semibold text-lg">
          Consumer Reports
        </Link>
      </div>
      <div className="w-1/3 flex justify-center">
        <Link 
          href="/chats" 
          className="text-sm font-medium text-gray-700 hover:text-gray-900 hover:underline"
        >
          My Chats
        </Link>
      </div>
      <div className="w-1/3 flex items-center justify-end gap-4">
        <div className="text-sm">
          {session?.user?.name || session?.user?.email}
        </div>
        <button
          onClick={handleSignOut}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
