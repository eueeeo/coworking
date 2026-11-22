CREATE DATABASE IF NOT EXISTS `coworking`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'coworking_app'@'localhost' 
IDENTIFIED BY '123';

CREATE USER IF NOT EXISTS 'coworking_app'@'127.0.0.1' 
IDENTIFIED BY '123';

GRANT ALL PRIVILEGES ON `coworking`.* TO 'coworking_app'@'localhost';
GRANT ALL PRIVILEGES ON `coworking`.* TO 'coworking_app'@'127.0.0.1';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'coworking_app'@'localhost';
