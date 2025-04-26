from game.player import *

class Dealer:
    def __init__(self, num_players: int, buy_in: int = 1000):
        self.deck = Deck()
        self.players = [Player("Player " + str(_ + 1), buy_in) for _ in range(num_players)]
        for player in self.players:
            player.deal_hand(self.deck)
        self.board = []
    
    # sets player name
    def set_player_name(self, player: int, name: str):
        self.players[player].player_name = name
    
    # deals a new cards
    def new_deal(self):
        self.deck = Deck()
        for player in self.players:
            player.deal_hand(self.deck)
        self.board = []

    # deals the board with num_cards
    def deal_board(self, num_cards: int = 5):
        for _ in range(num_cards - len(self.board)):
            self.board.append(self.deck.deal_card())
    
    # returns the player's stack
    def return_player_stack(self, player: int):
        return self.players[player].stack
            
    # returns the player's hand as a list
    def return_player_hand(self, player: int):
        return self.players[player].return_hand()

    # returns the player's hand as a str
    def return_player_hand_str(self, player: int):
        return (", ".join(map(str, self.players[player].return_hand())))
    
    # returns the board as a string
    def return_community_cards(self):
        return(", ".join(map(str, self.board)))

    # returns the hand rank and the cards played for a player
    def get_hand_rank(self, player : Player):
        hand_rank = ""
        hand_played = []

        # Get all cards
        all_cards = self.board.copy()
        all_cards.append(player.card1)
        all_cards.append(player.card2)

        # Sort cards by rank
        all_cards.sort(reverse=True)

        # Check for straight flush
        highest_straight_rank = -1
        
        for suit in Suit:
            # Get all cards of the same suit
            suit_cards = [card for card in all_cards if card.suit == suit]
            if len(suit_cards) >= 5:
                for i in range(len(suit_cards)):
                    for j in range(i + 1, len(suit_cards)):
                        for k in range(j + 1, len(suit_cards)):
                            for l in range(k + 1, len(suit_cards)):
                                for m in range(l + 1, len(suit_cards)):
                                    # checks for straight
                                    if (suit_cards[i] == suit_cards[j] + 1 and suit_cards[i] == suit_cards[k] + 2 and suit_cards[i] == suit_cards[l] + 3 and suit_cards[i] == suit_cards[m] + 4):
                                        
                                        # Check if the current straight is higher than the previous highest straight
                                        if suit_cards[i].rank.value > highest_straight_rank:
                                            hand_rank = handRank.STRAIGHT_FLUSH
                                            highest_straight_rank = suit_cards[i].rank.value
                                            hand_played = [suit_cards[i], suit_cards[j], suit_cards[k], suit_cards[l], suit_cards[m]]
                                    
                                    # considers edge case of Royal Flush
                                    if (suit_cards[i] == Rank.ACE and suit_cards[j] == Rank.KING and suit_cards[k] == Rank.QUEEN and 
                                        suit_cards[l] == Rank.JACK and suit_cards[m] == Rank.TEN):
                                        hand_rank = handRank.ROYAL_FLUSH
                                        hand_played = [suit_cards[i], suit_cards[j], suit_cards[k], suit_cards[l], suit_cards[m]]
                                        return hand_rank, hand_played
                                    # considers edge case of ace low straight
                                    if (suit_cards[i] == Rank.ACE and suit_cards[j] == Rank.FIVE and suit_cards[k] == Rank.FOUR and 
                                        suit_cards[l] == Rank.THREE and suit_cards[m] == Rank.TWO):
                                        if Rank.FIVE.value > highest_straight_rank:
                                            highest_straight_rank = Rank.FIVE.value
                                            hand_rank = handRank.STRAIGHT_FLUSH
                                            hand_played = [suit_cards[j], suit_cards[k], suit_cards[l], suit_cards[m], suit_cards[i]]
        if highest_straight_rank != -1:
            return hand_rank, hand_played


        # Check for four of a kind and return heightest kicker
        for i in range(len(all_cards) - 3):
            if all_cards[i] == all_cards[i + 3]:
                hand_rank = handRank.FOUR_OF_A_KIND
                hand_played = all_cards[i : i + 4]
                if (all_cards[0] != all_cards[i]):
                    hand_played.append(all_cards[0])
                else:
                    hand_played.append(all_cards[4])
                return hand_rank, hand_played
        

        # Check for full house
        for i in range(len(all_cards) - 2):
            for i in range(len(all_cards) - 2):
                if all_cards[i] == all_cards[i + 2]:
                    for j in range(len(all_cards) - 1):
                        if all_cards[j] == all_cards[j + 1] and all_cards[i] != all_cards[j]:
                            hand_rank = handRank.FULL_HOUSE
                            hand_played = all_cards[i : i + 3]
                            hand_played.append(all_cards[j])
                            hand_played.append(all_cards[j + 1])
                            return hand_rank, hand_played
        

        # Check for flush
        for suit in Suit:
            suit_cards = [card for card in all_cards if card.suit == suit]
            if len(suit_cards) >= 5:
                hand_rank = handRank.FLUSH
                hand_played = suit_cards[:5]
                return hand_rank, hand_played
        

        # Check for straight
        highest_straight_rank = -1
        
        for i in range(len(all_cards)):
            for j in range(i + 1, len(all_cards)):
                for k in range(j + 1, len(all_cards)):
                    for l in range(k + 1, len(all_cards)):
                        for m in range(l + 1, len(all_cards)):
                            # checks for straight
                            if (all_cards[i] == all_cards[j] + 1 and all_cards[i] == all_cards[k] + 2 and all_cards[i] == all_cards[l] + 3 and all_cards[i] == all_cards[m] + 4):
                                
                                # Check if the current straight is higher than the previous highest straight
                                if all_cards[i].rank.value > highest_straight_rank:
                                    hand_rank = handRank.STRAIGHT
                                    highest_straight_rank = all_cards[i].rank.value
                                    hand_played = [all_cards[i], all_cards[j], all_cards[k], all_cards[l], all_cards[m]]
                            
                            # considers edge case of ace high straight
                            if (all_cards[i] == Rank.ACE and all_cards[j] == Rank.KING and all_cards[k] == Rank.QUEEN and 
                                all_cards[l] == Rank.JACK and all_cards[m] == Rank.TEN):
                                hand_rank = handRank.STRAIGHT
                                hand_played = [all_cards[i], all_cards[j], all_cards[k], all_cards[l], all_cards[m]]
                                return hand_rank, hand_played
                            
                            # considers edge case of ace low straight
                            if (all_cards[i] == Rank.ACE and all_cards[j] == Rank.FIVE and all_cards[k] == Rank.FOUR and 
                                all_cards[l] == Rank.THREE and all_cards[m] == Rank.TWO):
                                highest_straight_rank = Rank.FIVE.value
                                hand_rank = handRank.STRAIGHT
                                hand_played = [all_cards[j], all_cards[k], all_cards[l], all_cards[m], all_cards[i]]

        if highest_straight_rank != -1:
            return hand_rank, hand_played
        
            
        # Check for heightest three of a kind and return heightest kicker
        for i in range(len(all_cards) - 2):
            if all_cards[i] == all_cards[i + 2]:
                hand_rank = handRank.THREE_OF_A_KIND
                hand_played = all_cards[i : i + 3]
                if (all_cards[0] != all_cards[i] and all_cards[1] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                elif (all_cards[0] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[4])
                else:
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])

                return hand_rank, hand_played
        

        # Check for two pair and return heightest kicker
        for i in range(len(all_cards) - 1):
            if all_cards[i] == all_cards[i + 1]:
                for j in range(i + 2, len(all_cards) - 1):
                    if all_cards[j] == all_cards[j + 1]:
                        hand_rank = handRank.TWO_PAIR
                        hand_played = all_cards[i : i + 2]
                        hand_played.append(all_cards[j])
                        hand_played.append(all_cards[j + 1])
                        if (all_cards[0] != all_cards[i] and all_cards[0] != all_cards[j]):
                            hand_played.append(all_cards[0])
                        elif (all_cards[2] != all_cards[i] and all_cards[2] != all_cards[j]):
                            hand_played.append(all_cards[2])
                        else:
                            hand_played.append(all_cards[4])
                        return hand_rank, hand_played
              
        
        # Check for pair and return heightest kicker
        for i in range(len(all_cards) - 1):
            if all_cards[i] == all_cards[i + 1]:
                hand_rank = handRank.PAIR
                hand_played = all_cards[i : i + 2]
                if (all_cards[0] != all_cards[i] and all_cards[1] != all_cards[i] and all_cards[2] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                    hand_played.append(all_cards[2])
                elif (all_cards[2] != all_cards[i] and all_cards[3] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[2])
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])
                elif (all_cards[0] != all_cards[i] and all_cards[3] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])
                else:
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                    hand_played.append(all_cards[4])
                return hand_rank, hand_played
        
        # Return highest card
        hand_rank = handRank.HIGH_CARD
        hand_played = all_cards[0:5]
        return hand_rank, hand_played
    
    # evaluate the hands of all players
    def evaluate_hands(self):
        for player in self.players:
            player.hand_rank, player.hand_played = self.get_hand_rank(player)
    
    # return the winner of the hand and consider tiebreakers
    def determine_winner(self):
        winner = self.players[0]
        for player in self.players:
            if player.hand_rank > winner.hand_rank:
                winner = player
            elif player.hand_rank == winner.hand_rank:
                for i in range(len(player.hand_played)):
                    if player.hand_played[i] > winner.hand_played[i]:
                        winner = player
                        break
                    elif player.hand_played[i] < winner.hand_played[i]:
                        break
        # Check for ties
        tiedPlayers = [winner]
        for player in self.players:
            if player == winner:
                continue
            if player.hand_rank == winner.hand_rank:
                tie = True
                for i in range(len(player.hand_played)):
                    if player.hand_played[i] != winner.hand_played[i]:
                        tie = False
                        break
                if tie:
                    tiedPlayers.append(player)
        if len(tiedPlayers) > 1:
            return tiedPlayers
        return winner

class PokerGameManager(Dealer):
    def __init__(self, buy_in: int = 1000, small_blind: int = 5, big_blind: int = 10):
        super().__init__(2, buy_in)
        self.starting_stack = buy_in
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.button = 0
        self.current_action = 0
        self.round = "pre-flop"
        self.current_pot = 0
        self.current_bet = 0
    
    def return_min_max_raise(self, player: int):
        min_raise = self.current_bet * 2
        max_raise = self.players[1].stack + self.players[1].round_pot_commitment
        return (min_raise, max_raise)

    def new_round(self):
        self.new_deal()
        self.current_pot = 0
        self.current_bet = 0
        self.button = (self.button + 1) % len(self.players)
        self.current_action = self.button
    
    def reset_betting(self):
        self.current_bet = 0
        for player in self.players:
            player.round_pot_commitment = 0

    # puts chips from player stack into the pot
    def player_bet(self, player: int, amount: int):
        self.current_pot += amount
        self.players[player].bet(amount)

    # calls the current bet
    def player_call(self, player: int):
        if self.players[player].stack + self.players[player].round_pot_commitment < self.current_bet:
            self.player_all_in_call(player)
            return
        amount_to_call = self.current_bet - self.players[player].round_pot_commitment
        self.player_bet(player, amount_to_call)

    # raises the current bet to the amount
    def player_raise(self, player: int, amount: int):
        self.current_bet = amount
        amount_raised = amount - self.players[player].round_pot_commitment
        self.player_bet(player, amount_raised)

    # player goes all in as a call and matches other player's bet
    def player_all_in_call(self, player: int):
        total_chips = self.players[player].stack + self.players[player].round_pot_commitment
        other_player = (player + 1) % 2
        if total_chips < self.current_bet:
            chips_not_covered = self.current_bet - total_chips
            self.players[other_player].round_pot_commitment = total_chips
            self.players[other_player].stack += chips_not_covered
            self.current_pot -= chips_not_covered
            self.current_bet = total_chips
            self.player_bet(player, total_chips- self.players[player].round_pot_commitment)
        else:
            self.player_call(player)

    # player goes all in as a raise
    def player_all_in_raise(self, player: int):
        total_raise = self.players[player].stack + self.players[player].round_pot_commitment
        self.player_raise(player, total_raise)
    
    # gives winning player the pot
    def player_win(self, player):
        if isinstance(player, int):
            self.players[player].stack += self.current_pot
        elif isinstance(player, Player):
            player.stack += self.current_pot
        elif isinstance(player, list):
            for p in player:
                p.stack += self.current_pot // len(player)