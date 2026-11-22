CREATE DATABASE IF NOT EXISTS `coworking`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `coworking`;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `Roles`;
CREATE TABLE `Roles` (
    `ID_role` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Users`;
CREATE TABLE `Users` (
    `ID_user` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_role` INT NOT NULL,
    `last_name` VARCHAR(100) NOT NULL,
    `first_name` VARCHAR(100) NOT NULL,
    `middle_name` VARCHAR(100) NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `is_email_confirmed` BOOLEAN NOT NULL DEFAULT FALSE,
    `email_confirmation_token_hash` VARCHAR(255) NULL,
    `email_confirmation_token_expires_at` DATETIME NULL,
    CONSTRAINT `fk_users_role` FOREIGN KEY (`ID_role`)
        REFERENCES `Roles` (`ID_role`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Floors`;
CREATE TABLE `Floors` (
    `ID_floor` INT AUTO_INCREMENT PRIMARY KEY,
    `number` INT NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Zones`;
CREATE TABLE `Zones` (
    `ID_zone` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_floor` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `description` TEXT NULL,
    CONSTRAINT `fk_zones_floor` FOREIGN KEY (`ID_floor`)
        REFERENCES `Floors` (`ID_floor`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Workspace_types`;
CREATE TABLE `Workspace_types` (
    `ID_type` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `price_per_hour` DECIMAL(10, 2) NOT NULL,
    CONSTRAINT `chk_workspace_types_price` CHECK (`price_per_hour` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Workspaces`;
CREATE TABLE `Workspaces` (
    `ID_workspace` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_zone` INT NOT NULL,
    `ID_type` INT NOT NULL,
    `number` VARCHAR(50) NOT NULL,
    `description` TEXT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT `fk_workspaces_zone` FOREIGN KEY (`ID_zone`)
        REFERENCES `Zones` (`ID_zone`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_workspaces_type` FOREIGN KEY (`ID_type`)
        REFERENCES `Workspace_types` (`ID_type`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `uq_workspaces_zone_number` UNIQUE (`ID_zone`, `number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Amenity_categories`;
CREATE TABLE `Amenity_categories` (
    `ID_category` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Amenities`;
CREATE TABLE `Amenities` (
    `ID_amenity` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_category` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    CONSTRAINT `fk_amenities_category` FOREIGN KEY (`ID_category`)
        REFERENCES `Amenity_categories` (`ID_category`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `uq_amenities_category_name` UNIQUE (`ID_category`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Workspace_amenities`;
CREATE TABLE `Workspace_amenities` (
    `ID_workspace_amenity` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_workspace` INT NOT NULL,
    `ID_amenity` INT NOT NULL,
    CONSTRAINT `fk_workspace_amenities_workspace` FOREIGN KEY (`ID_workspace`)
        REFERENCES `Workspaces` (`ID_workspace`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_workspace_amenities_amenity` FOREIGN KEY (`ID_amenity`)
        REFERENCES `Amenities` (`ID_amenity`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `uq_workspace_amenity` UNIQUE (`ID_workspace`, `ID_amenity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Booking_statuses`;
CREATE TABLE `Booking_statuses` (
    `ID_status` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Bookings`;
CREATE TABLE `Bookings` (
    `ID_booking` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_user` INT NOT NULL,
    `ID_workspace` INT NOT NULL,
    `ID_status` INT NOT NULL,
    `starts_at` DATETIME NOT NULL,
    `ends_at` DATETIME NOT NULL,
    `total_cost` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_bookings_user` FOREIGN KEY (`ID_user`)
        REFERENCES `Users` (`ID_user`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_bookings_workspace` FOREIGN KEY (`ID_workspace`)
        REFERENCES `Workspaces` (`ID_workspace`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_bookings_status` FOREIGN KEY (`ID_status`)
        REFERENCES `Booking_statuses` (`ID_status`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_bookings_time` CHECK (`ends_at` > `starts_at`),
    CONSTRAINT `chk_bookings_total_cost` CHECK (`total_cost` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `Booking_status_history`;
CREATE TABLE `Booking_status_history` (
    `ID_history` INT AUTO_INCREMENT PRIMARY KEY,
    `ID_booking` INT NOT NULL,
    `ID_new_status` INT NOT NULL,
    `ID_user` INT NOT NULL,
    `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `comment` TEXT NULL,
    CONSTRAINT `fk_history_booking` FOREIGN KEY (`ID_booking`)
        REFERENCES `Bookings` (`ID_booking`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_history_status` FOREIGN KEY (`ID_new_status`)
        REFERENCES `Booking_statuses` (`ID_status`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_history_user` FOREIGN KEY (`ID_user`)
        REFERENCES `Users` (`ID_user`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

CREATE INDEX `idx_bookings_workspace_time` ON `Bookings` (`ID_workspace`, `starts_at`, `ends_at`);
CREATE INDEX `idx_bookings_user` ON `Bookings` (`ID_user`);
CREATE INDEX `idx_workspaces_zone_type` ON `Workspaces` (`ID_zone`, `ID_type`);
CREATE INDEX `idx_history_booking` ON `Booking_status_history` (`ID_booking`);

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_bookings_after_insert`$$
CREATE TRIGGER `trg_bookings_after_insert`
AFTER INSERT ON `Bookings`
FOR EACH ROW
BEGIN
    INSERT INTO `Booking_status_history` (`ID_booking`, `ID_new_status`, `ID_user`, `changed_at`, `comment`)
    VALUES (NEW.`ID_booking`, NEW.`ID_status`, NEW.`ID_user`, NEW.`created_at`, 'Создание бронирования');
END$$

DROP TRIGGER IF EXISTS `trg_bookings_check_overlap_insert`$$
CREATE TRIGGER `trg_bookings_check_overlap_insert`
BEFORE INSERT ON `Bookings`
FOR EACH ROW
BEGIN
    DECLARE v_overlap_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO v_overlap_count
    FROM `Bookings` b
    JOIN `Booking_statuses` s ON b.`ID_status` = s.`ID_status`
    WHERE b.`ID_workspace` = NEW.`ID_workspace`
      AND s.`name` <> 'Отменено'
      AND b.`starts_at` < NEW.`ends_at`
      AND b.`ends_at` > NEW.`starts_at`;

    IF v_overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ошибка: Рабочее место уже забронировано на указанный интервал времени.';
    END IF;
END$$

DROP TRIGGER IF EXISTS `trg_bookings_check_overlap_update`$$
CREATE TRIGGER `trg_bookings_check_overlap_update`
BEFORE UPDATE ON `Bookings`
FOR EACH ROW
BEGIN
    DECLARE v_overlap_count INT DEFAULT 0;

    IF (NEW.`ID_workspace` <> OLD.`ID_workspace` OR 
        NEW.`starts_at` <> OLD.`starts_at` OR 
        NEW.`ends_at` <> OLD.`ends_at` OR 
        NEW.`ID_status` <> OLD.`ID_status`) THEN

        SELECT COUNT(*) INTO v_overlap_count
        FROM `Bookings` b
        JOIN `Booking_statuses` s ON b.`ID_status` = s.`ID_status`
        WHERE b.`ID_workspace` = NEW.`ID_workspace`
          AND b.`ID_booking` <> NEW.`ID_booking`
          AND s.`name` <> 'Отменено'
          AND b.`starts_at` < NEW.`ends_at`
          AND b.`ends_at` > NEW.`starts_at`;

        IF v_overlap_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Ошибка: Изменение создает пересечение с существующим бронированием.';
        END IF;
    END IF;
END$$

DELIMITER ;
