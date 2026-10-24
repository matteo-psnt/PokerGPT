from itertools import groupby
from game.card import Card, Rank
from game.player import HandRank


def best_hand(cards: list[Card]) -> tuple[HandRank, list[Card]]:
    """Returns the rank of the best five-card hand and its cards, most significant first,
    so two hands of the same rank compare by the ranks of their cards in order."""
    cards = sorted(cards, key=lambda card: card.rank, reverse=True)

    flush = _flush_cards(cards)
    if flush:
        straight_flush = _straight(flush)
        if straight_flush:
            if straight_flush[0].rank == Rank.ACE:
                return HandRank.ROYAL_FLUSH, straight_flush
            return HandRank.STRAIGHT_FLUSH, straight_flush

    # Cards grouped by rank, biggest groups first, then highest rank first
    groups = sorted((list(group) for _, group in groupby(cards, key=lambda card: card.rank)),
                    key=lambda group: (len(group), group[0].rank), reverse=True)
    sizes = [len(group) for group in groups]

    if sizes[0] == 4:
        return HandRank.FOUR_OF_A_KIND, _with_kickers(groups[0], cards)
    if sizes[0] == 3 and len(sizes) > 1 and sizes[1] >= 2:
        return HandRank.FULL_HOUSE, groups[0] + groups[1][:2]
    if flush:
        return HandRank.FLUSH, flush[:5]
    straight = _straight(cards)
    if straight:
        return HandRank.STRAIGHT, straight
    if sizes[0] == 3:
        return HandRank.THREE_OF_A_KIND, _with_kickers(groups[0], cards)
    if sizes[0] == 2 and sizes[1] == 2:
        return HandRank.TWO_PAIR, _with_kickers(groups[0] + groups[1], cards)
    if sizes[0] == 2:
        return HandRank.PAIR, _with_kickers(groups[0], cards)
    return HandRank.HIGH_CARD, cards[:5]


def _with_kickers(made: list[Card], cards: list[Card]) -> list[Card]:
    return made + [card for card in cards if card not in made][:5 - len(made)]


def _flush_cards(cards: list[Card]) -> list[Card] | None:
    for suit in {card.suit for card in cards}:
        suited = [card for card in cards if card.suit == suit]
        if len(suited) >= 5:
            return suited
    return None


def _straight(cards: list[Card]) -> list[Card] | None:
    """Highest five cards of consecutive ranks, with the ace also playing low (5-4-3-2-A)."""
    by_rank: dict[Rank, Card] = {}
    for card in cards:
        by_rank.setdefault(card.rank, card)
    for high in range(Rank.ACE, Rank.FIVE - 1, -1):
        ranks = [Rank.ACE if rank == 1 else Rank(rank) for rank in range(high, high - 5, -1)]
        if all(rank in by_rank for rank in ranks):
            return [by_rank[rank] for rank in ranks]
    return None
