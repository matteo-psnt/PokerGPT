import pytest
from game.deck import Deck
from game.card import Card, Rank, Suit

def test_deck_creation():
    deck = Deck()
    # A standard deck has 52 cards
    assert len(deck.cards) == 52
    
    # Check that all cards are unique
    card_strs = [str(card) for card in deck.cards]
    assert len(card_strs) == len(set(card_strs))
    
    # Verify all ranks and suits exist in the deck
    ranks_in_deck = {card.rank for card in deck.cards}
    suits_in_deck = {card.suit for card in deck.cards}
    
    assert len(ranks_in_deck) == len(Rank)
    assert len(suits_in_deck) == len(Suit)
    
    for rank in Rank:
        assert rank in ranks_in_deck
        
    for suit in Suit:
        assert suit in suits_in_deck

def test_deck_shuffle():
    deck1 = Deck()
    # Make a copy of the original card order
    original_order = deck1.cards.copy()
    
    # Shuffle the deck
    deck1.shuffle()
    
    # The deck should still have 52 cards
    assert len(deck1.cards) == 52
    
    # The order should be different (this could theoretically fail if the shuffle
    # returns the same order, but it's extremely unlikely)
    assert deck1.cards != original_order
    
    # Verify we have the same cards, just in different order
    assert sorted(str(c) for c in deck1.cards) == sorted(str(c) for c in original_order)

def test_deal_card():
    deck = Deck()
    original_count = len(deck.cards)
    
    # Deal a card
    card = deck.deal_card()
    
    # Verify card is a Card object
    assert isinstance(card, Card)
    
    # Deck should have one less card
    assert len(deck.cards) == original_count - 1
    
    # The dealt card should not be in the deck anymore
    assert card not in deck.cards