CREATE VIEW server_list AS
SELECT
    id AS server_id,
    host_id,
    server_name,
    total_hands,
    total_wins,
    total_losses,
    total_draws,
    net_bb_wins,
    net_bb_losses,
    net_bb_total
FROM servers;

CREATE VIEW game_details AS
SELECT
    g.id AS game_id,
    s.server_name,
    u.username AS user_name,
    g.total_hands,
    g.small_blind,
    g.big_blind,
    g.starting_stack,
    g.ending_stack,
    g.net_bb,
    g.result
FROM games g
JOIN users u ON g.user_id = u.id
JOIN servers s ON g.server_id = s.id;


CREATE VIEW hand_results AS
SELECT
    h.id AS hand_id,
    s.server_name,
    u.username AS user_name,
    g.id AS game_id,
    h.cards,
    h.gpt_cards,
    h.community_cards,
    h.starting_stack,
    h.ending_stack,
    h.net_bb,
    h.result,
    h.end_round
FROM hands h
JOIN users u ON h.user_id = u.id
JOIN games g ON h.game_id = g.id
JOIN servers s ON h.server_id = s.id;


CREATE VIEW player_hand_actions AS
SELECT
    ga.id AS action_id,
    ga.timestamp,
    u.username AS user_name,
    g.id AS game_id,
    h.id AS hand_id,
    ga.action_type,
    ga.raise_amount,
    ga.json_data
FROM gpt_actions ga
JOIN users u ON ga.user_id = u.id
JOIN games g ON ga.game_id = g.id
JOIN hands h ON ga.hand_id = h.id;
