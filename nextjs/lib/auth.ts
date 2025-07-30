import { saltAndHashPassword } from "@/utils/password";
import { PrismaClient } from "@prisma/client";
import type { Session, User } from "next-auth";
import type { AuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import CredentialsProvider from "next-auth/providers/credentials";
import { createSession } from "./session";

// Extend NextAuth Session type to include deviceId
declare module "next-auth" {
  interface Session {
    deviceId?: string;
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
    accessToken?: string;
  }
}

// Simple UUID generator function
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Create auth options for NextAuth v4
export const authOptions: AuthOptions = {
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt", // Always use JWT for simplicity
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // Ensure credentials is not undefined
        if (!credentials || !credentials.email || !credentials.password) {
          return null;
        }

        // TypeScript type assertion to ensure credentials is properly typed
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          const pwHash = await saltAndHashPassword(
            credentials.password as string
          );
          const db = new PrismaClient();
          try {
            const user = await db.user.findFirst({
              where: { email: credentials.email },
            });
            if (!user) {
              await db.$disconnect();
              return null;
            }
            if (user.password !== pwHash) {
              await db.$disconnect();
              return null;
            }
            await db.$disconnect();
            return {
              id: user.id,
              email: user.email || "",
              name: user.name || "",
            };
          } catch (error) {
            console.error("Database error:", error);
            await db.$disconnect();
            return null;
          }
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }: { token: JWT; user?: User }) {
      try {
        if (user) {
          token.id = user.id;
          token.email = user.email;
          token.name = user.name;
          token.deviceId = `web-${generateUUID()}`;

          if (token.id) {
            // Use token.jti as sessionToken if available, otherwise generate one
            const sessionToken = generateUUID();
            const db = new PrismaClient();
            await createSession(
              db,
              token.id as string,
              sessionToken,
              token.deviceId as string
            );
            await db.$disconnect();
            token.sessionToken = sessionToken;
          }
        }
      } catch (error) {
        console.error("JWT callback error:", error);
      }
      return token;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (session.user && token) {
        session.user.id = token.id as string;
        session.deviceId = token.deviceId as string;
        session.accessToken = token.accessToken as string;
      }
      session.accessToken = token.sessionToken as string;

      return session;
    },
  },
  debug: process.env.NODE_ENV === "development",
};
