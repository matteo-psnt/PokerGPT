import json
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts.chat import ChatPromptTemplate
from game.poker import PokerGameManager
from db.db_utils import DatabaseManager
from db.enums import ActionType

class GPTPlayer:
    def __init__(self, db: DatabaseManager, model_name="gpt-4.1-nano"):
        self.db = db
        llm = ChatOpenAI(model_name=model_name)
        output_parser = StrOutputParser()
        template = '''
        Imagine you're a poker bot in a heads-up Texas Hold'em game. Your play is optimal, 
        mixing strategic bluffs and strong hands. You raise on strength, going All-in only with the best hands. 
        Folding against a superior opponent hand, you call and check when fitting. Remember, only "call" the ALL-IN if your hand is better. 
        Please reply in the following JSON format: {{your_hand": "what is the current hand you are playing",  
        "opponents_hand": "what do you think your opponent has based on how he has played", "thought_process": "what is your thought process", 
        "action": "your action", "raise_amount": your raise amount if applicable}}
        Note: If the action you chose doesn't involve a raise, please do not include the "raise_amount" key in your JSON response.
        '''
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("user", "{input}")
        ])

        self.chain = prompt | llm | output_parser
        
    def _extract_action(self, json_string, pokerGame: PokerGameManager):
        min_raise, max_raise = pokerGame.return_min_max_raise(1)
        try:
            json_data = json.loads(json_string)
            action_str = json_data['action'].lower()
            action = ActionType(action_str)
                        
            raise_amount = None
            if action == ActionType.RAISE:
                raise_amount = int(json_data['raise_amount'])
                
                if raise_amount < min_raise:
                    raise_amount = min_raise

                elif raise_amount >= max_raise:
                    action = ActionType.ALL_IN
                    raise_amount = pokerGame.return_player_stack(1)
            
            self.db.record_gpt_action(action, raise_amount, json_string)
            return (action, raise_amount)
        except Exception as erro:
            return ("Default", 0)


    def pre_flop_small_blind(self, pokerGame: PokerGameManager):
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
        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)

    def pre_flop_big_blind(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
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
        What action would you take? (Check, Raise, or All-in)
        '''

        formatted_text = human_template.format(**inputs)
        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)
    
    def first_to_act(self, pokerGame: PokerGameManager):
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
        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)
    
    def player_check(self, pokerGame: PokerGameManager):
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

        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)
    
    def player_raise(self, pokerGame: PokerGameManager):
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

        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)  

    def player_all_in(self, pokerGame: PokerGameManager):
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
        
        response = self.chain.invoke({'input': formatted_text})
        return self._extract_action(response, pokerGame)
