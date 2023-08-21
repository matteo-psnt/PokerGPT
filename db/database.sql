-- Active: 1690312626673@@127.0.0.1@3306@pokerGPTdatabase
CREATE DATABASE pokerGPTdatabase;

CREATE TABLE servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id VARCHAR(100),
    server_name VARCHAR(100),
    total_players INT DEFAULT 0,
    total_hands INT DEFAULT 0,
    total_time_played INT UNSIGNED DEFAULT 0,
    total_wins INT DEFAULT 0,
    total_losses INT DEFAULT 0,
    total_draws INT DEFAULT 0,
    net_bb_wins DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_losses DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_total DECIMAL(10, 3) DEFAULT 0.000,
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    discord_id VARCHAR(100),
    total_hands INT UNSIGNED DEFAULT 0,
    total_games INT UNSIGNED DEFAULT 0,
    total_time_played INT UNSIGNED DEFAULT 0,
    total_wins INT UNSIGNED DEFAULT 0,
    total_losses INT UNSIGNED DEFAULT 0,
    total_draws INT UNSIGNED DEFAULT 0,
    highest_win_streak INT UNSIGNED DEFAULT 0,
    current_win_streak INT UNSIGNED DEFAULT 0,
    highest_loss_streak INT UNSIGNED DEFAULT 0,
    current_loss_streak INT UNSIGNED DEFAULT 0,
    net_bb_wins DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_losses DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_total DECIMAL(10, 3) DEFAULT 0.000,
);

CREATE TABLE server_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    total_hands_on_server INT UNSIGNED DEFAULT 0,
    net_bb_wins_on_server DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_losses_on_server DECIMAL(10, 3) DEFAULT 0.000,
    net_bb_total_on_server DECIMAL(10, 3) DEFAULT 0.000,
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bot_version VARCHAR(100) DEFAULT '0.0.0',
    end_timestamp TIMESTAMP,
    total_hands INT UNSIGNED DEFAULT 0,
    small_blind INT UNSIGNED,
    big_blind INT UNSIGNED,
    starting_stack INT UNSIGNED,
    ending_stack INT UNSIGNED DEFAULT 0,
    net_bb DECIMAL(10, 3) DEFAULT 0.000,
    result ENUM('complete win', 'win', 'complete loss', 'loss', 'draw', 'in progress', 'abandoned') DEFAULT 'in progress',
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE hands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT,
    user_id INT,
    game_id INT,
    cards VARCHAR(100),
    gpt_cards VARCHAR(100),
    community_cards VARCHAR(100) DEFAULT '',
    starting_stack INT UNSIGNED,
    ending_stack INT UNSIGNED DEFAULT 0,
    net_bb DECIMAL(10, 3) DEFAULT 0.000,
    result ENUM('win', 'loss', 'split pot', 'in progress', 'abandoned') DEFAULT 'in progress',
    end_round ENUM('pre-flop', 'flop', 'turn', 'river', 'showdown', 'in progress', 'abandoned') DEFAULT 'in progress',
    FOREIGN KEY (server_id) REFERENCES servers(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
);

CREATE TABLE gpt_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    game_id INT,
    hand_id INT,
    action_type ENUM('call', 'check', 'fold', 'raise', 'all-in') NOT NULL,
    raise_amount DECIMAL(10, 2) DEFAULT NULL,
    json_data JSON,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (hand_id) REFERENCES hands(id)
)