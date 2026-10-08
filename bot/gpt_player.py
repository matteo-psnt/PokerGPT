from typing import ClassVar, Literal, Optional, cast
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from game.poker import PokerGameManager
from db.db_utils import DatabaseManager
from db.enums import ActionType
from config.log_config import logger


# Structured output schemas: the API guarantees replies match these, so each spot only offers its legal moves.
# Field order matters: the model reasons before labelling its hand or choosing an action
# (with your_hand first it often misreads made hands, e.g. folding a straight as "queen-high").
class Decision(BaseModel):
    # Legal move to make when no decision comes back (API error or refusal)
    fallback: ClassVar[ActionType]

    thought_process: str = Field(description="Your thought process: first work out exactly what hand you have made with the board, then decide")
    your_hand: str = Field(description="The current hand you are playing")
    opponents_hand: str = Field(description="What you think your opponent has based on how they have played")
    action: str


class RaisableDecision(Decision):
    raise_amount: Optional[int] = Field(description="Total chips to raise to; null unless the action is raise")


class FacingBetDecision(RaisableDecision):
    fallback = ActionType.FOLD
    action: Literal["call", "raise", "all-in", "fold"]


class CanCheckDecision(RaisableDecision):
    fallback = ActionType.CHECK
    action: Literal["check", "raise", "all-in"]


class FacingAllInDecision(Decision):
    fallback = ActionType.FOLD
    action: Literal["call", "fold"]


class GPTPlayer:
    def __init__(self, db: DatabaseManager, model_name="gpt-6-luna"):
        self.db = db
        llm = ChatOpenAI(model_name=model_name, reasoning_effort="none")
        template = '''
        Imagine you're a poker bot in a heads-up Texas Hold'em game. Your play is optimal,
        mixing strategic bluffs and strong hands. You raise on strength, going All-in only with the best hands.
        Folding against a superior opponent hand, you call and check when fitting. Remember, only "call" the ALL-IN if your hand is better.
        '''

        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("user", "{input}")
        ])

        self.chains: dict[type[Decision], Runnable] = {
            schema: prompt | llm.with_structured_output(schema, method="json_schema", strict=True)
            for schema in (FacingBetDecision, CanCheckDecision, FacingAllInDecision)
        }

    async def _decide(self, formatted_text: str, schema: type[Decision], pokerGame: PokerGameManager):
        try:
            decision = cast(Decision, await self.chains[schema].ainvoke({'input': formatted_text}))
        except Exception as e:
            logger.error(f"GPT request failed, defaulting to {schema.fallback.value}: {e}")
            return (schema.fallback, None)
        return self._resolve_action(decision, pokerGame)

    def _resolve_action(self, decision: Decision, pokerGame: PokerGameManager):
        min_raise, max_raise = pokerGame.return_min_max_raise(1)
        action = ActionType(decision.action)

        raise_amount = None
        if action == ActionType.RAISE and isinstance(decision, RaisableDecision):
            raise_amount = max(decision.raise_amount or 0, min_raise)
            if raise_amount >= max_raise:
                action = ActionType.ALL_IN
                raise_amount = pokerGame.return_player_stack(1)

        self.db.record_gpt_action(action, raise_amount, decision.model_dump_json())
        return (action, raise_amount)


    async def pre_flop_small_blind(self, pokerGame: PokerGameManager):
        # return Call, Raise, Fold or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'opponents_stack': pokerGame.return_player_stack(0),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'amount_to_call': pokerGame.big_blind - pokerGame.small_blind
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        You are the small blind and it's your turn.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, Raise, All-in, or Fold)
        '''

        formatted_text = human_template.format(**inputs)
        return await self._decide(formatted_text, FacingBetDecision, pokerGame)

    async def pre_flop_big_blind(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'opponents_stack': pokerGame.return_player_stack(0),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        You are the big blind and your opponent has called. It's your turn and you can check for free.
        What action would you take? (Check, Raise, or All-in)
        '''

        formatted_text = human_template.format(**inputs)
        return await self._decide(formatted_text, CanCheckDecision, pokerGame)
    
    async def first_to_act(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'opponents_stack': pokerGame.return_player_stack(0),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards()
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round and you're first to act. The community cards are {community_cards}.
        What action would you take? (Check, Raise, or All-in)
        '''

        formatted_text = human_template.format(**inputs)
        return await self._decide(formatted_text, CanCheckDecision, pokerGame)
    
    async def player_check(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'opponents_stack': pokerGame.return_player_stack(0),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards()
        }

        human_template = """
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It is the {round} round and the action checks to you. The community cards are {community_cards}.
        Based on this information, what action would you like to take? (Check, Raise, or All-in).
        """        
        
        formatted_text = human_template.format(**inputs)

        return await self._decide(formatted_text, CanCheckDecision, pokerGame)
    
    async def player_raise(self, pokerGame: PokerGameManager):
        # return Call, Raise, All-in, or Fold
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'opponents_stack': pokerGame.return_player_stack(0),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards(),
            'opponent_raise': pokerGame.current_bet,
            'amount_to_call': pokerGame.current_bet - pokerGame.players[1].round_pot_commitment
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round. The community cards are {community_cards}.
        Your opponent has raised to {opponent_raise} chips.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, Raise, All-in, or Fold)
        '''

        formatted_text = human_template.format(**inputs)

        return await self._decide(formatted_text, FacingBetDecision, pokerGame)

    async def player_all_in(self, pokerGame: PokerGameManager):
        # return Call, or Fold
        amount_to_call = pokerGame.current_bet - pokerGame.players[1].round_pot_commitment
        if amount_to_call > pokerGame.return_player_stack(1):
            amount_to_call = pokerGame.return_player_stack(1)
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.return_player_stack(1),
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards(),
            'opponent_raise': pokerGame.current_bet,
            'amount_to_call': amount_to_call
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round. The community cards are {community_cards}.
        Your opponent has gone all in for {opponent_raise} chips.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, or Fold)
        '''

        formatted_text = human_template.format(**inputs)
        
        return await self._decide(formatted_text, FacingAllInDecision, pokerGame)
