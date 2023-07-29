-- Active: 1690312626673@@127.0.0.1@3306@pokerGPTdatabase
CREATE DATABASE pokerGPTdatabase;

CREATE TABLE servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id VARCHAR(100),
    server_name VARCHAR(100),
    total_server_games INT DEFAULT 0,
    total_server_wins INT DEFAULT 0,
    total_server_losses INT DEFAULT 0,
    total_server_draws INT DEFAULT 0,
    net_server_wins INT DEFAULT 0,
    net_server_losses INT DEFAULT 0,
    net_server_total INT DEFAULT 0,
    net_server_wins_scaled INT DEFAULT 0,
    net_server_losses_scaled INT DEFAULT 0,
    net_server_total_scaled INT DEFAULT 0
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    discord_id VARCHAR(100),
    total_games INT DEFAULT 0,
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
    net_wins_scaled_on_server INT DEFAULT 0,
    net_losses_scaled_on_server INT DEFAULT 0,
    net_total_scaled_on_server INT DEFAULT 0,
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE games (
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
    game_status ENUM('in progress', 'completed', 'abandoned') DEFAULT 'in progress',
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE rounds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    game_id INT,
    round_number INT,
    amount INT UNSIGNED,
    stack_before INT UNSIGNED,
    stack_after INT UNSIGNED,
    net INT,
    net_scaled INT,
    result ENUM('win', 'loss', 'draw', 'in progress', 'abandoned'),
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
);
