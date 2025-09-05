'use client';

import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';

export default function ClientAuthHeader() {
  const { data: session, status } = useSession();
  const isAuthenticated = status === 'authenticated';
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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
    <>
      <header className="w-full bg-white border-b border-gray-200 py-2 px-4 flex items-center justify-between">
        {/* Mobile: Logo only, Desktop: Logo + My Chats */}
        <div className="flex items-center gap-4">
          <Link href="/" className="font-semibold text-lg whitespace-nowrap">
            Consumer Reports
          </Link>
          <Link 
            href="/chats" 
            className="hidden sm:block text-sm font-medium text-gray-700 hover:text-gray-900 hover:underline"
          >
            My Chats
          </Link>
        </div>
        
        {/* Desktop: Full user info + logout */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {session?.user?.name || session?.user?.email}
          </div>
          <button
            onClick={handleSignOut}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Log out
          </button>
        </div>

        {/* Mobile: Hamburger menu */}
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="sm:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="sm:hidden bg-white border-b border-gray-200 px-4 py-3 space-y-3">
          <div className="text-sm text-gray-600">
            {session?.user?.name || session?.user?.email}
          </div>
          <Link 
            href="/chats" 
            className="block text-sm font-medium text-gray-700 hover:text-gray-900 hover:underline py-1"
            onClick={() => setIsMenuOpen(false)}
          >
            My Chats
          </Link>
          <button
            onClick={() => {
              handleSignOut();
              setIsMenuOpen(false);
            }}
            className="block w-full text-left px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Log out
          </button>
        </div>
      )}
    </>
  );
}
