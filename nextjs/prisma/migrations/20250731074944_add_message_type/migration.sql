-- AlterTable
ALTER TABLE "messages" ADD COLUMN     "message_type" TEXT NOT NULL DEFAULT 'user';

-- Update existing messages based on their properties
-- Messages from Genesys (have genesys_message_id and sent_to_genesys=true and is_system=true)
UPDATE "messages" 
SET "message_type" = 'genesys' 
WHERE "genesys_message_id" IS NOT NULL 
  AND "sent_to_genesys" = true 
  AND "is_system" = true;

-- System messages sent to Genesys (sent_to_genesys=true, is_system=true, but no genesys_message_id)
UPDATE "messages" 
SET "message_type" = 'system_to_genesys' 
WHERE "sent_to_genesys" = true 
  AND "is_system" = true 
  AND "genesys_message_id" IS NULL;

-- System messages to users (is_system=true, sent_to_genesys=false)
UPDATE "messages" 
SET "message_type" = 'system' 
WHERE "is_system" = true 
  AND "sent_to_genesys" = false;

-- User messages (is_system=false) - should already be 'user' from default, but being explicit
UPDATE "messages" 
SET "message_type" = 'user' 
WHERE "is_system" = false;