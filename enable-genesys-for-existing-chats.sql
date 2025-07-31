-- Enable Genesys OpenMessaging for all existing chats
-- Run this once to update existing chats after changing the default

UPDATE chats SET genesys_open_message_active = true WHERE genesys_open_message_active = false;

-- Check the results
SELECT 
    id, 
    genesys_open_message_active, 
    genesys_open_message_session_id,
    created_at
FROM chats 
ORDER BY created_at DESC 
LIMIT 10;