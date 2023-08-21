from game.card import *

# replace with your own custom emojis
red_card_rank_tops = {
    Rank.ACE : "<:red_A_top:1128175151402471515>",
    Rank.TWO : "<:red_2_top:1128175103251857439>",
    Rank.THREE : "<:red_3_top:1128175104891834389>",
    Rank.FOUR : "<:red_4_top:1128175105743274046>",
    Rank.FIVE : "<:red_5_top:1128175106590527488>",
    Rank.SIX : "<:red_6_top:1128175107504865340>",
    Rank.SEVEN : "<:red_7_top:1128175109287444571>",
    Rank.EIGHT : "<:red_8_top:1128175110407344200>",
    Rank.NINE : "<:red_9_top:1128175111455911936>",
    Rank.TEN : "<:red_10_top:1128180390507585536>",
    Rank.JACK : "<:red_J_top:1128175150559412244>",
    Rank.QUEEN : "<:red_Q_top:1128175148206403634>",
    Rank.KING : "<:red_K_top:1128175149691183156>"
}
black_card_rank_tops = {
    Rank.ACE : "<:black_A_top:1128174953712324668>",
    Rank.TWO : "<:black_2_top:1128174889904394330>",
    Rank.THREE : "<:black_3_top:1128174891854737518>",
    Rank.FOUR : "<:black_4_top:1128174892722946189>",
    Rank.FIVE : "<:black_5_top:1128174893742161971>",
    Rank.SIX : "<:black_6_top:1128174894706851921>",
    Rank.SEVEN : "<:black_7_top:1128174895776403559>",
    Rank.EIGHT : "<:black_8_top:1128174896707547238>",
    Rank.NINE : "<:black_9_top:1128174897571573760>",
    Rank.TEN : "<:black_10_top:1128180389152833576>",
    Rank.JACK : "<:black_J_top:1128174955243253840>",
    Rank.QUEEN : "<:black_Q_top:1128174957415911495>",
    Rank.KING : "<:black_K_top:1128174956266672158>"
}
suit_bottoms = {
    Suit.SPADES: "<:spade_bottom:1128173093022613585>",
    Suit.HEARTS: "<:heart_bottom:1128172979973529640>",
    Suit.DIAMONDS: "<:diamond_bottom:1128172980833361921>",
    Suit.CLUBS: "<:club_bottom:1128172982469148703>"
}

'''
To view the unique identifiers of the custom cards in Discord, 
you can use the following commands in the server chat:

Red Card Bottoms:

\:red_A_top:
\:red_2_top:
\:red_3_top:
\:red_4_top:
\:red_5_top:
\:red_6_top:
\:red_7_top:
\:red_8_top:
\:red_9_top:
\:red_10_top:
\:red_J_top:
\:red_Q_top:
\:red_K_top:


Black  Card Bottoms:

\:black_A_top:
\:black_2_top:
\:black_3_top:
\:black_4_top:
\:black_5_top:
\:black_6_top:
\:black_7_top:
\:black_8_top:
\:black_9_top:
\:black_10_top:
\:black_J_top:
\:black_Q_top:
\:black_K_top:

Suit Card Tops:

\:spade_bottom:
\:heart_bottom:
\:diamond_bottom:
\:club_bottom:

By copying and pasting these commands into the Discord chat, 
the respective custom cards will be displayed, 
and their unique identifiers will be shown in the message input field.
'''

def get_cards(input_list: list[Card], small_cards: bool = False):   
    top_row = []
    bottom_row = []
    for card in input_list:
        if card.suit == Suit.SPADES or card.suit == Suit.CLUBS:
            top_row.append(black_card_rank_tops[card.rank])
        else:
            top_row.append(red_card_rank_tops[card.rank])
        bottom_row.append(suit_bottoms[card.suit])
    
    if small_cards:
        top_row = ["__"] + top_row + ["__"]
        bottom_row = ["__"] + bottom_row + ["__"]

    
    #join rows together with a new line
    return "\n".join(["".join(top_row), "".join(bottom_row)])
