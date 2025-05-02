from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, ROUND_HALF_UP
from db.models import ActionType, User, Server, Game, Hand, GPTAction, ServerUser
from db.enums import GameResult, HandResult, Round
from config.config import DATABASE_EXISTS


class DatabaseManager:
    def __init__(
        self,
        session: Session,
        discord_id: str,
        username: str,
        host_id: str,
        server_name: str,
    ):
        self.session = session
        self.discord_id = discord_id
        self.username = username
        self.host_id = host_id
        self.server_name = server_name

        if DATABASE_EXISTS:
            self._check_or_create_user()
            self._check_or_create_server()
            self._check_or_create_server_user()

    def _safe_commit(self):
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def _check_or_create_user(self):
        self.user = (
            self.session.query(User)
            .filter_by(discord_id=self.discord_id)
            .first()
        )
        if not self.user:
            self.user = User(discord_id=self.discord_id, username=self.username)
            self.session.add(self.user)
            self._safe_commit()
        elif self.user.username != self.username:
            self.user.username = self.username
            self._safe_commit()

    def _check_or_create_server(self):
        self.server = (
            self.session.query(Server)
            .filter_by(host_id=self.host_id)
            .first()
        )
        if not self.server:
            self.server = Server(host_id=self.host_id, server_name=self.server_name)
            self.session.add(self.server)
            self._safe_commit()
        elif self.server.server_name != self.server_name:
            self.server.server_name = self.server_name
            self._safe_commit()

    def _check_or_create_server_user(self):
        self.server_user = (
            self.session.query(ServerUser)
            .filter_by(server_id=self.server.id, user_id=self.user.id)
            .first()
        )
        if not self.server_user:
            self.server_user = ServerUser(
                server_id=self.server.id, user_id=self.user.id
            )
            self.session.add(self.server_user)
            self.server.total_players += 1
            self._safe_commit()

    def initialize_game(self, small_blind: int, big_blind: int, starting_stack: int):
        if not DATABASE_EXISTS:
            return
        self.big_blind = Decimal(big_blind)
        self.game_starting_stack = Decimal(starting_stack)
        self.game = Game(
            server_id=self.server.id,
            user_id=self.user.id,
            small_blind=small_blind,
            big_blind=big_blind,
            starting_stack=starting_stack,
            bot_version="v2.0.0",
        )
        self.session.add(self.game)
        self._safe_commit()

    def initialize_hand(self, cards: str, gpt_cards: str, starting_stack: int):
        if not DATABASE_EXISTS:
            return
        self.hand_starting_stack = Decimal(starting_stack)
        self.hand = Hand(
            server_id=self.server.id,
            user_id=self.user.id,
            game_id=self.game.id,
            cards=cards,
            gpt_cards=gpt_cards,
            starting_stack=starting_stack,
        )
        self.session.add(self.hand)
        self.game.total_hands += 1
        self._safe_commit()

    def end_hand(self, ending_stack: int, end_round: Round):
        if not DATABASE_EXISTS:
            return

        delta = Decimal(ending_stack) - self.hand_starting_stack
        net_bb = (delta / self.big_blind).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if net_bb > 0:
            result = HandResult.WIN
            self._update_wins(net_bb)
        elif net_bb < 0:
            result = HandResult.LOSS
            self._update_losses(abs(net_bb))
        else:
            result = HandResult.SPLIT_POT
            self._update_draws()

        self.hand.ending_stack = ending_stack
        self.hand.net_bb = net_bb
        self.hand.result = result
        self.hand.end_round = end_round
        self._safe_commit()

    def end_game(self, ending_stack: int):
        if not DATABASE_EXISTS:
            return
        delta = Decimal(ending_stack) - self.game_starting_stack
        net_bb = (delta / self.big_blind).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if net_bb == Decimal(100):
            result = GameResult.COMPLETE_WIN
        elif net_bb > 0:
            result = GameResult.WIN
        elif net_bb == Decimal(-100):
            result = GameResult.COMPLETE_LOSS
        elif net_bb < 0:
            result = GameResult.LOSS
        else:
            result = GameResult.DRAW

        self.game.end_timestamp = datetime.now()
        self.game.ending_stack = ending_stack
        self.game.net_bb = net_bb
        self.game.result = result
        self._safe_commit()

        duration = (self.game.end_timestamp - self.game.timestamp).total_seconds()
        duration = Decimal(duration).quantize(Decimal("0.01"))

        self.user.total_time_played += duration
        self.user.total_games += 1
        self.server.total_time_played += duration
        
        self._safe_commit()
        self.close()

    def _update_wins(self, net_bb: Decimal):
        self.server.total_hands += 1
        self.server.total_wins += 1
        self.server.net_bb_wins += net_bb
        self.server.net_bb_total += net_bb

        self.user.total_hands += 1
        self.user.total_wins += 1
        self.user.current_win_streak += 1
        self.user.highest_win_streak = max(
            self.user.highest_win_streak, self.user.current_win_streak
        )
        self.user.current_loss_streak = 0
        self.user.net_bb_wins += net_bb
        self.user.net_bb_total += net_bb

        self.server_user.total_hands_on_server += 1
        self.server_user.net_bb_wins_on_server += net_bb
        self.server_user.net_bb_total_on_server += net_bb

        self._safe_commit()

    def _update_losses(self, net_bb: Decimal):
        self.server.total_hands += 1
        self.server.total_losses += 1
        self.server.net_bb_losses = Decimal(self.server.net_bb_losses) + net_bb
        self.server.net_bb_total = Decimal(self.server.net_bb_total) - net_bb

        self.user.total_hands += 1
        self.user.total_losses += 1
        self.user.current_loss_streak += 1
        self.user.highest_loss_streak = max(
            self.user.highest_loss_streak, self.user.current_loss_streak
        )
        self.user.current_win_streak = 0
        self.user.net_bb_losses = Decimal(self.user.net_bb_losses) + net_bb
        self.user.net_bb_total = Decimal(self.user.net_bb_total) - net_bb

        self.server_user.total_hands_on_server += 1
        self.server_user.net_bb_losses_on_server = Decimal(self.server_user.net_bb_losses_on_server) + net_bb
        self.server_user.net_bb_total_on_server = Decimal(self.server_user.net_bb_total_on_server) - net_bb

        self._safe_commit()

    def _update_draws(self):
        self.server.total_hands += 1
        self.server.total_draws += 1

        self.user.total_hands += 1
        self.user.total_draws += 1
        self.user.current_win_streak = 0
        self.user.current_loss_streak = 0

        self.server_user.total_hands_on_server += 1

        self._safe_commit()

    def update_community_cards(self, community_cards: str):
        if not DATABASE_EXISTS:
            return
        self.hand.community_cards = community_cards
        self._safe_commit()

    def record_gpt_action(self, action_type: ActionType, raise_amount: int | None, json_data: str):
        if not DATABASE_EXISTS:
            return
        
        action = GPTAction(
            user_id=self.user.id,
            game_id=self.game.id,
            hand_id=self.hand.id,
            action_type=action_type,
            raise_amount=raise_amount,
            json_data=json_data,
        )
        self.session.add(action)
        self._safe_commit()

    def get_top_players(self, limit=10):
        return self.session.query(User.username, User.net_bb_total).order_by(User.net_bb_total.desc()).limit(limit).all()

    def get_user_stats_of_player(self):
        return self.session.query(
            User.total_hands, User.total_games, User.total_time_played,
            User.net_bb_total, User.net_bb_wins, User.net_bb_losses,
            User.total_wins, User.total_losses, User.total_draws,
            User.highest_win_streak, User.highest_loss_streak
        ).filter_by(discord_id=self.discord_id).first()

    def get_user_place(self):
        subquery = self.session.query(User.net_bb_total).filter_by(discord_id=self.discord_id).scalar_subquery()
        return self.session.query(func.count(User.id)).filter(User.net_bb_total > subquery).scalar() + 1

    def get_user_stats_by_username(self, username):
        return self.session.query(
            User.total_hands, User.total_games, User.total_time_played,
            User.net_bb_total, User.net_bb_wins, User.net_bb_losses,
            User.total_wins, User.total_losses, User.total_draws,
            User.highest_win_streak, User.highest_loss_streak
        ).filter_by(username=username).first()

    def get_top_servers(self, limit=10):
        return self.session.query(Server.server_name, Server.net_bb_wins).order_by(Server.net_bb_wins.desc()).limit(limit).all()

    def get_server_stats(self):
        return self.session.query(
            Server.total_players, Server.total_hands, Server.total_time_played,
            Server.net_bb_total, Server.net_bb_wins, Server.net_bb_losses,
            Server.total_wins, Server.total_losses, Server.total_draws
        ).filter_by(host_id=self.host_id).first()

    def get_server_place(self):
        subquery = self.session.query(Server.net_bb_wins).filter_by(host_id=self.host_id).scalar_subquery()
        return self.session.query(func.count(Server.id)).filter(Server.net_bb_wins > subquery).scalar() + 1

    def get_server_stats_by_name(self, server_name):
        return self.session.query(
            Server.total_players, Server.total_hands, Server.total_time_played,
            Server.net_bb_total, Server.net_bb_wins, Server.net_bb_losses,
            Server.total_wins, Server.total_losses, Server.total_draws
        ).filter_by(server_name=server_name).first()

    def close(self):
        self.session.close()
