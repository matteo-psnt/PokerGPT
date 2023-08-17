import mysql.connector
from config.config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE, DATABASE_EXISTS

class DatabaseManager:
    def __init__(self, discord_id, username, host_id, server_name):
        self.discord_id = discord_id
        self.username = username
        self.host_id = host_id
        self.server_name = server_name
        if DATABASE_EXISTS:
            self.cnx = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE
            )
            self.cursor = self.cnx.cursor()
            self._check_for_user()
            self._check_for_server()
            self._check_for_server_user()
    
    def _check_for_user(self):
        check_user_stmt = (
            "SELECT discord_id, username FROM users "
            "WHERE discord_id = %s"
        )
        self.cursor.execute(check_user_stmt, (self.discord_id,))
        result = self.cursor.fetchone()
        if result is None:
            add_user_stmt = (
                "INSERT INTO users (discord_id, username) "
                "VALUES (%s, %s)"
            )
            data = (self.discord_id, self.username)
            self.cursor.execute(add_user_stmt, data)
            self.cnx.commit()
        else:
            if self.username != result[1]:
                self._update_nickname()

    def _check_for_server(self):
        check_server_stmt = (
            "SELECT host_id, server_name FROM servers "
            "WHERE host_id = %s"
        )
        self.cursor.execute(check_server_stmt, (self.host_id,))
        result = self.cursor.fetchone()
        if result is None:
            add_server_stmt = (
                "INSERT INTO servers (host_id, server_name) "
                "VALUES (%s, %s)"
            )
            data = (self.host_id, self.server_name)
            self.cursor.execute(add_server_stmt, data)
            self.cnx.commit()
        else:
            if self.server_name != result[1]:
                self._update_server_name()
    
    def _check_for_server_user(self):
        get_server_id_stmt = (
            "SELECT id FROM servers "
            "WHERE host_id = %s"
        )
        self.cursor.execute(get_server_id_stmt, (self.host_id,))
        self.server_id = self.cursor.fetchone()[0]

        get_user_id_stmt = (
            "SELECT id FROM users "
            "WHERE discord_id = %s"
        )
        self.cursor.execute(get_user_id_stmt, (self.discord_id,))
        self.user_id = self.cursor.fetchone()[0]

        check_server_user_stmt = (
            "SELECT server_id, user_id FROM server_users "
            "WHERE server_id = %s AND user_id = %s"
        )
        data = (self.server_id, self.user_id)
        self.cursor.execute(check_server_user_stmt, data)
        result = self.cursor.fetchone()

        if result is None:
            add_user_server_stmt = (
                "INSERT INTO server_users (server_id, user_id) "
                "VALUES (%s, %s)"
            )
            data = (self.server_id, self.user_id)
            self.cursor.execute(add_user_server_stmt, data)
            self.cnx.commit()
    
    def _update_nickname(self):
        update_stmt = (
            "UPDATE users SET username = %s "
            "WHERE id = %s"
        )
        data = (self.username, self.user_id)
        self.cursor.execute(update_stmt, data)
        self.cnx.commit()
    
    def _update_server_name(self):
        update_server_name_stmt = (
            "UPDATE servers SET server_name = %s "
            "WHERE id = %s"
        )
        data = (self.server_name, self.server_id)
        self.cursor.execute(update_server_name_stmt, data)
        self.cnx.commit()
    
    def initialize_game(self, small_blind, big_blind, starting_stack):
        if not DATABASE_EXISTS:
            return
        self.big_blind = big_blind
        self.game_starting_stack = starting_stack
        add_game_stmt = (
            "INSERT INTO games (server_id, user_id, small_blind, big_blind, starting_stack) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        data = (self.server_id, self.user_id, small_blind, big_blind, starting_stack)
        self.cursor.execute(add_game_stmt, data)
        self.game_id = self.cursor.lastrowid
        self.cnx.commit()

    def initialize_hand(self, cards, gpt_cards, starting_stack):
        if not DATABASE_EXISTS:
            return
        self.hand_starting_stack = starting_stack
        # Inserting the new hand
        add_hand_stmt = (
            "INSERT INTO hands (server_id, user_id, game_id, cards, gpt_cards, starting_stack) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        data = (self.server_id, self.user_id, self.game_id, cards, gpt_cards, starting_stack)
        self.cursor.execute(add_hand_stmt, data)
        self.hand_id = self.cursor.lastrowid

        # Updating the total_hands count for the game
        update_total_hands_stmt = (
            "UPDATE games SET total_hands = total_hands + 1 "
            "WHERE id = %s"
        )
        self.cursor.execute(update_total_hands_stmt, (self.game_id,))
        self.cnx.commit()

    def end_hand(self, ending_stack, end_round):
        if not DATABASE_EXISTS:
            return
        net_bb = (ending_stack - self.hand_starting_stack) / self.big_blind
        net_bb = round(net_bb, 2)
        if net_bb > 0:
            result = "win"
            self._update_wins(net_bb)
        elif net_bb < 0:
            result = "loss"
            self._update_losses(abs(net_bb))
        else:
            result = 'split pot'
            self._update_draws()
        
        update_hand_stmt = (
            "UPDATE hands SET ending_stack = %s, net_bb = %s, result = %s, end_round = %s "
            "WHERE id = %s"
        )
        data = (ending_stack, net_bb, result, end_round, self.hand_id)
        self.cursor.execute(update_hand_stmt, data)
        self.cnx.commit()
    
    def end_game(self, ending_stack):
        if not DATABASE_EXISTS:
            return
        net_bb = (ending_stack - self.game_starting_stack) / self.big_blind
        net_bb = round(net_bb, 2)
        if net_bb == 100:
            result = 'complete win'
        elif net_bb > 0:
            result = 'win'
        elif net_bb == -100:
            result = 'complete loss'
        elif net_bb < 0:
            result = 'loss'
        elif net_bb == 0:
            result = 'draw'
        
        update_game_stmt = (
            "UPDATE games SET end_timestamp = NOW(), ending_stack = %s, net_bb = %s, result = %s "
            "WHERE id = %s"
        )
        data = (ending_stack, net_bb, result, self.game_id)
        self.cursor.execute(update_game_stmt, data)
        self.cnx.commit()
    
    def _update_wins(self, net_bb_wins):
        # Update servers table for win
        server_update_query = (
            "UPDATE servers SET total_hands = total_hands + 1, total_wins = total_wins + 1, "
            "net_bb_wins = net_bb_wins + %s, net_bb_total = net_bb_total + %s WHERE id = %s"
        )
        self.cursor.execute(server_update_query, (net_bb_wins, net_bb_wins, self.server_id))

        # Update users table for win
        user_update_query = (
            "UPDATE users SET total_hands = total_hands + 1, total_wins = total_wins + 1, "
            "current_win_streak = current_win_streak + 1, "
            "highest_win_streak = GREATEST(highest_win_streak, current_win_streak + 1), "
            "current_loss_streak = 0, "
            "net_bb_wins = net_bb_wins + %s, net_bb_total = net_bb_total + %s WHERE id = %s"
        )
        self.cursor.execute(user_update_query, (net_bb_wins, net_bb_wins, self.user_id))

        # Update server_users table for win
        server_user_update_query = (
            "UPDATE server_users SET total_hands_on_server = total_hands_on_server + 1, "
            "net_bb_wins_on_server = net_bb_wins_on_server + %s, "
            "net_bb_total_on_server = net_bb_total_on_server + %s "
            "WHERE server_id = %s AND user_id = %s"
        )
        self.cursor.execute(server_user_update_query, (net_bb_wins, net_bb_wins, self.server_id, self.user_id))

        self.cnx.commit()

    def _update_losses(self, net_bb_losses):
        # Update servers table for loss
        server_update_query = (
            "UPDATE servers SET total_hands = total_hands + 1, total_losses = total_losses + 1, "
            "net_bb_losses = net_bb_losses + %s, net_bb_total = net_bb_total - %s WHERE id = %s"
        )
        self.cursor.execute(server_update_query, (net_bb_losses, net_bb_losses, self.server_id))

        # Update users table for loss
        user_update_query = (
            "UPDATE users SET total_hands = total_hands + 1, total_losses = total_losses + 1, "
            "current_loss_streak = current_loss_streak + 1, "
            "highest_loss_streak = GREATEST(highest_loss_streak, current_loss_streak + 1), "
            "current_win_streak = 0, "
            "net_bb_losses = net_bb_losses + %s, net_bb_total = net_bb_total - %s WHERE id = %s"
        )
        self.cursor.execute(user_update_query, (net_bb_losses, net_bb_losses, self.user_id))

        # Update server_users table for loss
        server_user_update_query = (
            "UPDATE server_users SET total_hands_on_server = total_hands_on_server + 1, "
            "net_bb_losses_on_server = net_bb_losses_on_server + %s, "
            "net_bb_total_on_server = net_bb_total_on_server - %s "
            "WHERE server_id = %s AND user_id = %s"
        )
        self.cursor.execute(server_user_update_query, (net_bb_losses, net_bb_losses, self.server_id, self.user_id))

        self.cnx.commit()
  
    def _update_draws(self):
        # Update servers table for draw
        server_update_query = (
            "UPDATE servers SET total_hands = total_hands + 1, total_draws = total_draws + 1 "
            "WHERE id = %s"
        )
        self.cursor.execute(server_update_query, (self.server_id,))

        # Reset both current_win_streak and current_loss_streak to 0 for user
        user_update_query = (
            "UPDATE users SET total_hands = total_hands + 1, total_draws = total_draws + 1, "
            "current_win_streak = 0, current_loss_streak = 0 WHERE id = %s"
        )
        self.cursor.execute(user_update_query, (self.user_id,))

        # Update server_users table for draw
        server_user_update_query = (
            "UPDATE server_users SET total_hands_on_server = total_hands_on_server + 1 "
            "WHERE server_id = %s AND user_id = %s"
        )
        self.cursor.execute(server_user_update_query, (self.server_id, self.user_id))

        self.cnx.commit()

    def update_community_cards(self, community_cards):
        if not DATABASE_EXISTS:
            return
        update_community_cards_stmt = (
            "UPDATE hands SET community_cards = %s "
            "WHERE id = %s"
        )
        data = (community_cards, self.hand_id)
        self.cursor.execute(update_community_cards_stmt, data)
        self.cnx.commit()
    
    def record_gpt_action(self, action_type, raise_amount, json_data):
        if not DATABASE_EXISTS:
            return
        
        action_type = action_type.lower()
        if action_type not in ['call', 'check', 'fold', 'raise', 'all-in']:
            raise ValueError("Invalid action type")
        
        if raise_amount == 0:
            raise_amount = None
            
        insert_stmt = (
            "INSERT INTO gpt_actions (user_id, game_id, hand_id, action_type, raise_amount, json_data) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        data = (self.user_id, self.game_id, self.hand_id, action_type, raise_amount, json_data)
        self.cursor.execute(insert_stmt, data)
        self.cnx.commit()
 
    def close(self, exc_type, exc_value, traceback):
        if DATABASE_EXISTS:
            self.cursor.close()
            self.cnx.close()