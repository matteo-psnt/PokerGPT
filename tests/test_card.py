import pytest
from game.card import Card, Rank, Suit

class TestCard:
    def test_card_creation(self):
        card = Card(Rank.ACE, Suit.SPADES)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES

    def test_card_comparison(self):
        ace_spades = Card(Rank.ACE, Suit.SPADES)
        king_hearts = Card(Rank.KING, Suit.HEARTS)
        
        # Test equality
        assert ace_spades == ace_spades
        assert ace_spades != king_hearts
        
        # Test greater than
        assert ace_spades > king_hearts
        assert not king_hearts > ace_spades
        
        # Test less than
        assert king_hearts < ace_spades
        assert not ace_spades < king_hearts
        
        # Test comparison with Rank
        assert ace_spades == Rank.ACE
        assert ace_spades != Rank.KING

        # Test comparison with int
        assert ace_spades == 0  # ACE is 0 in enum
        
    def test_card_add(self):
        ace_spades = Card(Rank.ACE, Suit.SPADES)
        
        # Test adding int
        assert ace_spades + 1 == Rank.TWO
        assert ace_spades + 12 == Rank.KING
        
        # Test overflow
        assert ace_spades + 13 == Rank.ACE
        
    def test_card_string_representation(self):
        ace_spades = Card(Rank.ACE, Suit.SPADES)
        ten_hearts = Card(Rank.TEN, Suit.HEARTS)
        
        assert str(ace_spades) == "AS"
        assert str(ten_hearts) == "10H"
        
        assert ace_spades.long_str() == "Ace of Spades"
        assert ten_hearts.long_str() == "10 of Hearts"

    def test_invalid_comparison(self):
        card = Card(Rank.ACE, Suit.SPADES)
        with pytest.raises(TypeError):
            card == "AS"