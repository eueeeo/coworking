USE `coworking`;

ALTER TABLE `Users`
ADD COLUMN `is_email_confirmed` BOOLEAN NOT NULL DEFAULT FALSE AFTER `is_active`,
ADD COLUMN `email_confirmation_token_hash` VARCHAR(255) NULL AFTER `is_email_confirmed`,
ADD COLUMN `email_confirmation_token_expires_at` DATETIME NULL AFTER `email_confirmation_token_hash`;

UPDATE `Users`
SET `is_email_confirmed` = TRUE;
