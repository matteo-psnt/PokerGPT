from datetime import datetime
from sqlalchemy import Column, Integer, String, DECIMAL, Enum, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from db.enums import ActionType, Round, GameResult, HandResult

Base = declarative_base()

class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    host_id = Column(String(100))
    server_name = Column(String(100))
    total_players = Column(Integer, default=0)
    total_hands = Column(Integer, default=0)
    total_time_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_draws = Column(Integer, default=0)
    net_bb_wins = Column(DECIMAL(10, 3), default=0.000)
    net_bb_losses = Column(DECIMAL(10, 3), default=0.000)
    net_bb_total = Column(DECIMAL(10, 3), default=0.000)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    discord_id = Column(String(100))
    total_hands = Column(Integer, default=0)
    total_games = Column(Integer, default=0)
    total_time_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_draws = Column(Integer, default=0)
    highest_win_streak = Column(Integer, default=0)
    current_win_streak = Column(Integer, default=0)
    highest_loss_streak = Column(Integer, default=0)
    current_loss_streak = Column(Integer, default=0)
    net_bb_wins = Column(DECIMAL(10, 3), default=0.000)
    net_bb_losses = Column(DECIMAL(10, 3), default=0.000)
    net_bb_total = Column(DECIMAL(10, 3), default=0.000)

class ServerUser(Base):
    __tablename__ = 'server_users'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    total_hands_on_server = Column(Integer, default=0)
    net_bb_wins_on_server = Column(DECIMAL(10, 3), default=0.000)
    net_bb_losses_on_server = Column(DECIMAL(10, 3), default=0.000)
    net_bb_total_on_server = Column(DECIMAL(10, 3), default=0.000)

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(TIMESTAMP, default=datetime.now)
    end_timestamp = Column(TIMESTAMP)
    bot_version = Column(String(100), default='0.0.0')
    total_hands = Column(Integer, default=0)
    small_blind = Column(Integer)
    big_blind = Column(Integer)
    starting_stack = Column(Integer)
    ending_stack = Column(Integer, default=0)
    net_bb = Column(DECIMAL(10, 3), default=0.000)
    result = Column(Enum(GameResult, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), default=GameResult.IN_PROGRESS.value)

class Hand(Base):
    __tablename__ = 'hands'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    game_id = Column(Integer, ForeignKey('games.id'))
    cards = Column(String(100))
    gpt_cards = Column(String(100))
    community_cards = Column(String(100), default='')
    starting_stack = Column(Integer)
    ending_stack = Column(Integer, default=0)
    net_bb = Column(DECIMAL(10, 3), default=0.000)
    result = Column(Enum(HandResult, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), default=HandResult.IN_PROGRESS.value)
    end_round = Column(Enum(Round, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), default=Round.IN_PROGRESS.value)

class GPTAction(Base):
    __tablename__ = 'gpt_actions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP, default=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_id = Column(Integer, ForeignKey('games.id'))
    hand_id = Column(Integer, ForeignKey('hands.id'))
    action_type = Column(Enum(ActionType, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    raise_amount = Column(DECIMAL(10, 2))
    json_data = Column(JSON)
