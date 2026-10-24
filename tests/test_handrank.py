from game.player import HandRank

def test_hand_rank_ordering():
    # Test ordering of hand ranks
    assert HandRank.HIGH_CARD < HandRank.PAIR
    assert HandRank.PAIR < HandRank.TWO_PAIR
    assert HandRank.TWO_PAIR < HandRank.THREE_OF_A_KIND
    assert HandRank.THREE_OF_A_KIND < HandRank.STRAIGHT
    assert HandRank.STRAIGHT < HandRank.FLUSH
    assert HandRank.FLUSH < HandRank.FULL_HOUSE
    assert HandRank.FULL_HOUSE < HandRank.FOUR_OF_A_KIND
    assert HandRank.FOUR_OF_A_KIND < HandRank.STRAIGHT_FLUSH
    assert HandRank.STRAIGHT_FLUSH < HandRank.ROYAL_FLUSH

def test_hand_rank_equality():
    # Test equality comparison
    assert HandRank.PAIR == HandRank.PAIR
    assert HandRank.STRAIGHT == HandRank.STRAIGHT
    assert HandRank.ROYAL_FLUSH == HandRank.ROYAL_FLUSH
    
    # Test inequality
    assert HandRank.PAIR != HandRank.STRAIGHT
    assert HandRank.FLUSH != HandRank.FULL_HOUSE

def test_hand_rank_string_representation():
    # Test string representation
    assert str(HandRank.HIGH_CARD) == "High Card"
    assert str(HandRank.TWO_PAIR) == "Two Pair"
    assert str(HandRank.STRAIGHT_FLUSH) == "Straight Flush"
    assert str(HandRank.ROYAL_FLUSH) == "Royal Flush"