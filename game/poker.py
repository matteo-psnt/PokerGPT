from db.enums import Round
from game.deck import Deck
from game.hand_evaluator import best_hand
from game.player import HandRank, Player

# Seat indexes in a heads-up game
USER, GPT = 0, 1


class Dealer:
    def __init__(self, num_players: int, buy_in: int = 1000):
        self.players = [Player(f"Player {i + 1}", buy_in) for i in range(num_players)]
        self.new_deal()

    # shuffles a new deck, deals every player a hand and clears the board
    def new_deal(self):
        self.deck = Deck()
        for player in self.players:
            player.deal_hand(self.deck)
        self.board = []

    # deals the board up to num_cards
    def deal_board(self, num_cards: int = 5):
        while len(self.board) < num_cards:
            self.board.append(self.deck.deal_card())

    def board_str(self) -> str:
        return ", ".join(map(str, self.board))

    # returns the hand rank and the cards played for a player
    def get_hand_rank(self, player: Player):
        return best_hand(self.board + player.hand)

    def evaluate_hands(self):
        for player in self.players:
            player.hand_rank, player.hand_played = self.get_hand_rank(player)

    # returns every player holding the best hand; more than one means a split pot
    def determine_winners(self) -> list[Player]:
        def strength(player: Player):
            return (player.hand_rank, [card.rank for card in player.hand_played])

        best = max(map(strength, self.players))
        return [player for player in self.players if strength(player) == best]


class PokerGameManager(Dealer):
    def __init__(self, buy_in: int = 1000, small_blind: int = 5, big_blind: int = 10):
        super().__init__(2, buy_in)
        self.starting_stack = buy_in
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.button = 0
        self.current_action = 0
        self.round = Round.PRE_FLOP
        self.current_pot = 0
        self.current_bet = 0

    def raise_limits(self, player: int) -> tuple[int, int]:
        # Same rules the user's raise modal enforces: at least double the bet and at least the big blind
        min_raise = max(self.current_bet * 2, self.big_blind)
        return min_raise, self.players[player].total_chips

    def new_round(self):
        self.new_deal()
        self.current_pot = 0
        self.current_bet = 0
        self.button = (self.button + 1) % len(self.players)
        self.current_action = self.button
        self.round = Round.PRE_FLOP

    def reset_betting(self):
        self.current_bet = 0
        for player in self.players:
            player.round_pot_commitment = 0

    # chips the player still needs to put in to match the current bet
    def amount_to_call(self, player: int) -> int:
        return self.current_bet - self.players[player].round_pot_commitment

    # puts chips from player stack into the pot
    def player_bet(self, player: int, amount: int):
        self.current_pot += amount
        self.players[player].bet(amount)

    # calls the current bet, all-in for less if the player can't cover it
    def player_call(self, player: int):
        caller = self.players[player]
        if caller.total_chips < self.current_bet:
            # Hand the bettor back the part of their bet the caller can't match
            bettor = self.players[(player + 1) % 2]
            uncovered = self.current_bet - caller.total_chips
            bettor.stack += uncovered
            bettor.round_pot_commitment -= uncovered
            self.current_pot -= uncovered
            self.current_bet = caller.total_chips
        self.player_bet(player, self.amount_to_call(player))

    # raises the current bet to the amount
    def player_raise(self, player: int, amount: int):
        self.current_bet = amount
        self.player_bet(player, self.amount_to_call(player))

    def player_all_in(self, player: int):
        self.player_raise(player, self.players[player].total_chips)

    # splits the pot evenly between the winners
    def award_pot(self, *winners: Player):
        for winner in winners:
            winner.stack += self.current_pot // len(winners)
