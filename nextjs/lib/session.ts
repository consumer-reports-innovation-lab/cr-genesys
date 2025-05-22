/**
 * Custom session management utilities
 */
import { PrismaClient } from "@prisma/client";

// We'll initialize Prisma client dynamically to avoid Edge runtime issues
let prisma: PrismaClient | null = null;

// Only initialize in server context
if (typeof window === "undefined") {
  try {
    prisma = new PrismaClient();
  } catch (error) {
    console.error("Failed to initialize Prisma:", error);
  }
}

/**
 * Create a new session for a user
 */
export async function createSession(
  db: PrismaClient,
  userId: string,
  sessionToken: string,
  deviceId?: string
) {
  try {
    // Set expiration to 30 days from now
    const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

    // Create the session in the database
    const session = await db.session.create({
      data: {
        sessionToken,
        userId,
        expires,
        ...(deviceId ? { deviceId } : {}),
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    });

    return session;
  } catch (error) {
    console.error("Failed to create session:", error);
    return null;
  }
}

/**
 * Get active session for a user
 */
export async function getActiveSession(userId: string) {
  if (!prisma) {
    console.error("Prisma client not initialized");
    return null;
  }

  try {
    // Find the most recent active session
    const session = await prisma.session.findFirst({
      where: {
        userId,
        expires: { gt: new Date() },
      },
      orderBy: { expires: "desc" },
    });

    return session;
  } catch (error) {
    console.error("Failed to get session:", error);
    return null;
  }
}

/**
 * Get a session by token
 */
export async function getSessionByToken(sessionToken: string) {
  try {
    // Initialize Prisma client if not already initialized
    if (!prisma) {
      prisma = new PrismaClient();
    }

    const session = await prisma.session.findUnique({
      where: { sessionToken },
      include: { user: true },
    });

    // Check if session has expired
    if (session && new Date(session.expires) < new Date()) {
      await prisma.session.delete({
        where: { id: session.id },
      });
      return null;
    }

    return session;
  } catch (error) {
    console.error("Failed to get session:", error);
    return null;
  }
}

/**
 * Delete all sessions for a user
 */
export async function deleteUserSessions(userId: string) {
  try {
    // Initialize Prisma client if not already initialized
    if (!prisma) {
      prisma = new PrismaClient();
    }

    await prisma.session.deleteMany({
      where: { userId },
    });
    return true;
  } catch (error) {
    console.error("Failed to delete sessions:", error);
    return false;
  } finally {
    // Clean up Prisma connection
    if (prisma) {
      await prisma.$disconnect();
    }
  }
}

/**
 * Delete a specific session by token
 */
export async function deleteSessionByToken(sessionToken: string) {
  if (!prisma) {
    console.error("Prisma client not initialized");
    return false;
  }

  try {
    // Delete the session with the given token
    await prisma.session.delete({
      where: { sessionToken },
    });

    return true;
  } catch (error) {
    console.error("Failed to delete session:", error);
    return false;
  }
}
