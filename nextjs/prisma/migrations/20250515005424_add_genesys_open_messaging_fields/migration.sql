-- AlterTable
ALTER TABLE "chats" ADD COLUMN     "genesys_open_message_active" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "genesys_open_message_session_id" TEXT;

-- AlterTable
ALTER TABLE "messages" ADD COLUMN     "genesys_message_id" TEXT,
ADD COLUMN     "sent_to_genesys" BOOLEAN NOT NULL DEFAULT false;
