from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from settings import API_KEY
from poker import HeadsUpPoker
import json


def extract_action(json_string, min_raise, max_raise):
    try:
        json_data = json.loads(json_string)
        action = json_data['action'].capitalize()
        if action == "Raise":
            raise_amount = json_data['raise_amount']
            action = [action, raise_amount]
        
        if isinstance(action, list):
            assert action[0] == "Raise"
            assert isinstance(action[1], int)
            if action[1] < min_raise:
                print("Raise amount too small, raising to minimum")
                action[1] = min_raise
            
            elif action[1] > max_raise:
                print("Raise amount too large, raising all-in")
                action = "All-in"
        return action
    except:
        print("Invalid response from GPT-3")
        print(json_string)
        return "Fold"

chat = ChatOpenAI(model_name="gpt-3.5-turbo") # type: ignore

template = "You are a proffesional poker bot who is playing a game of heads up Texas Hold'em aginst a human player. You play optimally and will occasionally bluff. You will raise when you have a strong hand. You will only go All-in if you have a very strong hand. You will fold if you think your opponent has a better hand. And will call and check where appropriate. "
system_message_prompt = SystemMessagePromptTemplate.from_template(template)

def pre_flop_small_blind(pokerGame: HeadsUpPoker):
    # return Call, Raise, Fold or All-in
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
    Your hand is {hand}. The pot is {pot} chips. 
    You are small blind and the action is on you.
    It costs {amount_to_call} chips to call.
    Based on this information, what action would you like to take? (Call, Raise, All-in, or Fold), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''

    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack, opponents_stack=pokerGame.players[0].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot, amount_to_call=pokerGame.big_blind - pokerGame.small_blind)
    
    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)


def pre_flop_big_blind(pokerGame: HeadsUpPoker):
    # return Check, Raise, or All-in
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
    Your hand is {hand}. The pot is {pot} chips. 
    You are big blind and the action checks to you.
    Based on this information, what action would you like to take? (Check, Raise, or All-in), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''

    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack, opponents_stack=pokerGame.players[0].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot)

    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)


def first_to_act(pokerGame: HeadsUpPoker):
    # return Check, Raise, or All-in
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
    Your hand is {hand}. The pot is {pot} chips. 
    It is the {round} round and the first action is on you. The community cards are {community_cards}.
    Based on this information, what action would you like to take? (Check, Raise, or All-in), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack, opponents_stack=pokerGame.players[0].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot, round=pokerGame.round, community_cards=pokerGame.return_community_cards())
    
    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)


def player_check(pokerGame: HeadsUpPoker):
    # return Check, Raise, or All-in
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
    Your hand is {hand}. The pot is {pot} chips. 
    It is the {round} round and the action checks to you. The community cards are {community_cards}.
    Based on this information, what action would you like to take? (Check, Raise, or All-in), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack, opponents_stack=pokerGame.players[0].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot, round=pokerGame.round, community_cards=pokerGame.return_community_cards())
    
    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)


def player_raise(pokerGame: HeadsUpPoker):
    # return Call, Raise, All-in, or Fold
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
    Your hand is {hand}. The pot is {pot} chips.
    It is the {round} round. The community cards are {community_cards}.
    The opponent raises to {opponent_raise} chips.
    It costs {amount_to_call} chips to call.
    Based on this information, what action would you like to take? (Call, Raise, All-in, or Fold), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack, opponents_stack=pokerGame.players[0].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot, round=pokerGame.round, community_cards=pokerGame.return_community_cards(),
                         opponent_raise=pokerGame.current_bet, amount_to_call=pokerGame.current_bet - pokerGame.players[1].round_pot_commitment)
    
    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)


def player_all_in(pokerGame: HeadsUpPoker):
    # return Call, or Fold
    human_template = '''
    The small blind is {small_blind} chips and the big blind is {big_blind} chips.
    You have {stack} chips in your stack.
    Your hand is {hand}. The pot is {pot} chips.
    It is the {round} round. The community cards are {community_cards}.
    The opponent goes all in for {opponent_raise} chips.
    It costs {amount_to_call} chips to call.
    Based on this information, what action would you like to take? (Call, or Fold), provide no explanation for your action.
    Reply in JSON format and provide no explanation for your action. If aplicable include the amount you want to raise by.
    '''
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)

    amount_to_call = pokerGame.current_bet - pokerGame.players[1].round_pot_commitment
    if amount_to_call > pokerGame.players[1].stack:
        amount_to_call = pokerGame.players[1].stack

    response = chain.run(small_blind=pokerGame.small_blind, big_blind=pokerGame.big_blind, stack=pokerGame.players[1].stack,
                         hand=pokerGame.players[1].return_long_hand(), pot=pokerGame.current_pot, round=pokerGame.round, community_cards=pokerGame.return_community_cards(),
                         opponent_raise=pokerGame.current_bet, amount_to_call=amount_to_call)
    
    return extract_action(response, pokerGame.current_bet * 2, pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment)
