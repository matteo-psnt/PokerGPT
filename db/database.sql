-- Active: 1690312626673@@127.0.0.1@3306@pokerGPTdatabase
CREATE DATABASE pokerGPTdatabase;

CREATE TABLE servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id VARCHAR(100),
    server_name VARCHAR(100),
    total_hands INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    total_losses INT DEFAULT 0,
    total_draws INT DEFAULT 0,
    net_wins INT DEFAULT 0,
    net_losses INT DEFAULT 0,
    net_total INT DEFAULT 0,
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    discord_id VARCHAR(100),
    total_hands INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    total_losses INT DEFAULT 0,
    total_draws INT DEFAULT 0,
    highest_win_streak INT DEFAULT 0,
    current_win_streak INT DEFAULT 0,
    highest_loss_streak INT DEFAULT 0,
    current_loss_streak INT DEFAULT 0,
    net_wins INT DEFAULT 0,
    net_losses INT DEFAULT 0,
    net_total INT DEFAULT 0,
    net_wins_scaled INT DEFAULT 0,
    net_losses_scaled INT DEFAULT 0,
    net_total_scaled INT DEFAULT 0
);

CREATE TABLE server_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    net_wins_on_server INT DEFAULT 0,
    net_losses_on_server INT DEFAULT 0,
    net_total_on_server INT DEFAULT 0,
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE hands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_timestamp TIMESTAMP,
    result ENUM('win', 'loss', 'draw', 'in progress', 'abandoned'),
    small_blind INT UNSIGNED,
    big_blind INT UNSIGNED,
    starting_stack INT UNSIGNED,
    ending_stack INT UNSIGNED,
    net INT,
    scale_factor DECIMAL(5, 4) UNSIGNED DEFAULT 1,
    starting_stack_scaled INT UNSIGNED,
    ending_stack_scaled INT UNSIGNED,
    net_scaled INT,
    hand_status ENUM('in progress', 'completed', 'abandoned') DEFAULT 'in progress',
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE rounds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    hand_id INT,
    round_number INT,
    scale_factor DECIMAL(5, 4),
    stack_before INT UNSIGNED,
    stack_after INT UNSIGNED,
    net INT,
    net_scaled INT,
    result ENUM('win', 'loss', 'draw', 'in progress', 'abandoned'),
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (hand_id) REFERENCES hands(id)
    FOREIGN KEY (scale_factor) REFERENCES hands(scale_factor)
);
