from game.card import Card, Rank, Suit

def test_card_creation():
    card = Card(Rank.ACE, Suit.SPADES)
    assert card.rank == Rank.ACE
    assert card.suit == Suit.SPADES

def test_card_equality():
    ace_spades = Card(Rank.ACE, Suit.SPADES)

    assert ace_spades == Card(Rank.ACE, Suit.SPADES)
    assert ace_spades != Card(Rank.ACE, Suit.HEARTS)
    assert ace_spades != Card(Rank.KING, Suit.SPADES)
    assert ace_spades != "AS"

def test_cards_are_hashable():
    assert len({Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES)}) == 2

def test_rank_ordering():
    # Ace is high
    assert Rank.ACE > Rank.KING > Rank.QUEEN > Rank.JACK > Rank.TEN > Rank.TWO
    assert sorted(Rank) == list(Rank)

def test_card_string_representation():
    ace_spades = Card(Rank.ACE, Suit.SPADES)
    ten_hearts = Card(Rank.TEN, Suit.HEARTS)
    two_clubs = Card(Rank.TWO, Suit.CLUBS)
    queen_diamonds = Card(Rank.QUEEN, Suit.DIAMONDS)

    assert str(ace_spades) == "AS"
    assert str(ten_hearts) == "10H"
    assert str(two_clubs) == "2C"
    assert str(queen_diamonds) == "QD"

    assert ace_spades.long_str() == "Ace of Spades"
    assert ten_hearts.long_str() == "10 of Hearts"
    assert queen_diamonds.long_str() == "Queen of Diamonds"
