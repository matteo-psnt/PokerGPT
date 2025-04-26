import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, Server, Game, Hand, ServerUser, GPTAction
from db.enums import ActionType, GameResult, HandResult, Round
from db.db_utils import DatabaseManager

@pytest.fixture
def session():
    # In-memory SQLite DB for isolated tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def db_manager(session, monkeypatch):
    # Monkeypatch DATABASE_EXISTS
    monkeypatch.setattr("db.db_utils.DATABASE_EXISTS", True)
    return DatabaseManager(
        session=session,
        discord_id="test_discord_id",
        username="test_user",
        host_id="test_host_id",
        server_name="test_server"
    )

def test_check_or_create_user(db_manager, session):
    user = session.query(User).filter_by(discord_id="test_discord_id").first()
    assert user is not None
    assert user.username == "test_user"

def test_check_or_create_server(db_manager, session):
    server = session.query(Server).filter_by(host_id="test_host_id").first()
    assert server is not None
    assert server.server_name == "test_server"

def test_initialize_game(db_manager, session):
    db_manager.initialize_game(small_blind=5, big_blind=10, starting_stack=1000)
    game = session.query(Game).first()
    assert game is not None
    assert game.small_blind == 5
    assert game.big_blind == 10
    assert game.starting_stack == 1000

def test_initialize_hand_and_end_hand(db_manager, session):
    db_manager.initialize_game(small_blind=5, big_blind=10, starting_stack=1000)
    db_manager.initialize_hand(cards="AsKs", gpt_cards="AhQh", starting_stack=1000)
    db_manager.end_hand(ending_stack=1100, end_round=Round.PRE_FLOP)
    hand = session.query(Hand).first()
    assert hand.ending_stack == 1100
    assert hand.end_round == Round.PRE_FLOP
    assert hand.result == HandResult.WIN

def test_end_game(db_manager, session):
    db_manager.initialize_game(small_blind=5, big_blind=10, starting_stack=1000)
    db_manager.end_game(ending_stack=2000)
    game = session.query(Game).first()
    assert game.ending_stack == 2000
    assert game.result == GameResult.COMPLETE_WIN

@pytest.mark.parametrize("enum_cls,model_cls,field_name,extra_fields", [
    (GameResult, Game, 'result', {
        'server_id': 1, 'user_id': 1, 'small_blind': 5, 'big_blind': 10, 'starting_stack': 1000,
        # Add other required fields here as appropriate
    }),
    (HandResult, Hand, 'result', {
        'server_id': 1, 'user_id': 1, 'game_id': 1, 'cards': "AsKs", 'gpt_cards': "AhQh", 'starting_stack': 1000,
        # Add other required fields here as appropriate
    }),
    (Round, Hand, 'end_round', {
        'server_id': 1, 'user_id': 1, 'game_id': 1, 'cards': "AsKs", 'gpt_cards': "AhQh", 'starting_stack': 1000,
        # Add other required fields here as appropriate
    }),
    (ActionType, GPTAction, 'action_type', {
        'user_id': 1, 'game_id': 1, 'hand_id': 1,
    }),
])
def test_enum_values_stored_as_value(session, enum_cls, model_cls, field_name, extra_fields):
    for enum_member in enum_cls:
        # Insert row with enum field set to member
        model_kwargs = {**extra_fields, field_name: enum_member}
        obj = model_cls(**model_kwargs)
        session.add(obj)
        session.commit()
        # Find the row in the DB (assume just added, so order by id DESC)
        row_id = obj.id
        result = session.execute(
            text(f"SELECT {field_name} FROM {model_cls.__tablename__} WHERE id=:id"), {"id": row_id}
        ).scalar()
        # Check stored string matches the .value
        assert result == enum_member.value
        # Also confirm it's not the .name
        assert result != enum_member.name
        # Clean up for next loop
        session.delete(obj)
        session.commit()
