import pytest
from game.player import handRank

def test_hand_rank_ordering():
    # Test ordering of hand ranks
    assert handRank.HIGH_CARD < handRank.PAIR
    assert handRank.PAIR < handRank.TWO_PAIR
    assert handRank.TWO_PAIR < handRank.THREE_OF_A_KIND
    assert handRank.THREE_OF_A_KIND < handRank.STRAIGHT
    assert handRank.STRAIGHT < handRank.FLUSH
    assert handRank.FLUSH < handRank.FULL_HOUSE
    assert handRank.FULL_HOUSE < handRank.FOUR_OF_A_KIND
    assert handRank.FOUR_OF_A_KIND < handRank.STRAIGHT_FLUSH
    assert handRank.STRAIGHT_FLUSH < handRank.ROYAL_FLUSH

def test_hand_rank_equality():
    # Test equality comparison
    assert handRank.PAIR == handRank.PAIR
    assert handRank.STRAIGHT == handRank.STRAIGHT
    assert handRank.ROYAL_FLUSH == handRank.ROYAL_FLUSH
    
    # Test inequality
    assert handRank.PAIR != handRank.STRAIGHT
    assert handRank.FLUSH != handRank.FULL_HOUSE

def test_hand_rank_string_representation():
    # Test string representation
    assert str(handRank.HIGH_CARD) == "High Card"
    assert str(handRank.TWO_PAIR) == "Two Pair"
    assert str(handRank.STRAIGHT_FLUSH) == "Straight Flush"
    assert str(handRank.ROYAL_FLUSH) == "Royal Flush"