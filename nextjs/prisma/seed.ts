import { PrismaClient } from "@prisma/client";
import { saltAndHashPassword } from "../utils/password";

const prisma = new PrismaClient();

/**
 * Create a test user with the given email and name
 */
async function createUser(email: string, name: string) {
  return prisma.user.upsert({
    where: { email },
    update: {},
    create: {
      email,
      name,
      password: await saltAndHashPassword("password123"),
      emailVerified: new Date(),
    },
  });
}

/**
 * Create a welcome chat for a user
 */
async function createWelcomeChat(userId: string) {
  return prisma.chat.create({
    data: {
      title: "Welcome to Consumer Reports",
      userId,
      messages: {
        create: [
          {
            content: "Hello! How can I help you with Consumer Reports today?",
            isSystem: true,
            isMarkdown: false,
          },
        ],
      },
    },
    include: {
      messages: true,
    },
  });
}

/**
 * Create a subscription help chat for a user
 */
async function createSubscriptionChat(userId: string) {
  return prisma.chat.create({
    data: {
      title: "Subscription Help",
      userId,
      messages: {
        create: [
          {
            content: "Hello! How can I help you with Consumer Reports today?",
            isSystem: true,
            isMarkdown: false,
          },
        ],
      },
    },
    include: {
      messages: true,
    },
  });
}

/**
 * Create a car buying advice chat for a user
 */
async function createCarBuyingChat(userId: string) {
  return prisma.chat.create({
    data: {
      title: "Car Buying Advice",
      userId,
      messages: {
        create: [
          {
            content: "Hello! How can I help you with Consumer Reports today?",
            isSystem: true,
            isMarkdown: false,
          },
        ],
      },
    },
    include: {
      messages: true,
    },
  });
}

/**
 * Create a product safety concern chat that's closed with feedback
 */
async function createSafetyConcernChat(userId: string) {
  return prisma.chat.create({
    data: {
      title: "Product Safety Concerns",
      userId,
      status: "CLOSED",
      messages: {
        create: [
          {
            content: "Hello! How can I help you with Consumer Reports today?",
            isSystem: true,
            isMarkdown: false,
          },
          {
            content: "Your feedback has been sent.",
            isSystem: true,
            isMarkdown: false,
          },
        ],
      },
    },
    include: {
      messages: true,
    },
  });
}

/**
 * Delete all existing chats and messages for a user
 */
async function cleanupUserData(userId: string) {
  // Find all chats for this user
  const userChats = await prisma.chat.findMany({
    where: { userId },
    select: { id: true },
  });

  const chatIds = userChats.map((chat) => chat.id);

  if (chatIds.length > 0) {
    // Delete all messages in these chats
    await prisma.message.deleteMany({
      where: {
        chatId: { in: chatIds },
      },
    });

    // Delete all chats
    await prisma.chat.deleteMany({
      where: {
        id: { in: chatIds },
      },
    });

    console.log(`Deleted ${chatIds.length} existing chats for user ${userId}`);
  }
}

/**
 * Main seed function that orchestrates the database seeding
 */
async function main() {
  console.log("Starting seed script...");

  // Create test users
  const user1 = await createUser("user1@example.com", "Test User One");
  const user2 = await createUser("user2@example.com", "Test User Two");
  console.log(`Created users: ${user1.name}, ${user2.name}`);

  // Clean up existing data
  await cleanupUserData(user1.id);
  await cleanupUserData(user2.id);
  console.log("Cleaned up existing chats and messages");

  // Create chats for user1
  const user1Chat1 = await createWelcomeChat(user1.id);
  const user1Chat2 = await createSubscriptionChat(user1.id);

  // Create chats for user2
  const user2Chat1 = await createCarBuyingChat(user2.id);
  const user2Chat2 = await createSafetyConcernChat(user2.id);

  // Log results
  console.log(
    `Created ${user1.name}'s chats: ${user1Chat1.title}, ${user1Chat2.title}`
  );
  console.log(
    `Created ${user2.name}'s chats: ${user2Chat1.title}, ${user2Chat2.title}`
  );
  console.log("Seed completed successfully!");
}

main()
  .catch((e) => {
    console.error("Error in seed script:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
