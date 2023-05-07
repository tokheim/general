import argparse
from general import gameengine, tablebase, equilibriumfinder

epilog = """
2 generals simultaneously pick a number of soldiers to move onto the field.
Whoever moves the most forces onto the field wins the round.
A soldier used in one round can not be used again.
Game is over after one side wins N rounds, or all soldiers are used
"""

_CPU = "computer"
_HUMAN = "human"


parser = argparse.ArgumentParser(prog="Generals", description="play generals game", epilog=epilog)
parser.add_argument('-H', '--home', choices=(_HUMAN, _CPU), default=_HUMAN)
parser.add_argument('-a', '--away', choices=(_HUMAN, _CPU), default=_CPU)
parser.add_argument('-p', '--pieces', type=int, default=100)
parser.add_argument('-w', '--wins', type=int, default=3)
parser.add_argument('-s', '--stats', action="store_true")
args = parser.parse_args()

def play_game(game, home_player, away_player, table, stats):
    while not game.winner:
        print(str(game))
        home_pieces = home_player.post_move(game.state, True)
        away_pieces = away_player.post_move(game.state, False)
        print("home played %s, away played %s" % (home_pieces, away_pieces))
        if stats:
            table.comment_moves(game.state, home_pieces, away_pieces)
        game = game.play_move(home_pieces, away_pieces)

    print("Result %s" % (game.winner, ))
    return game.winner


game = gameengine.Game.create(win_at=args.wins, pieces=args.pieces)

eq_finder = equilibriumfinder.create()
table = tablebase.TableBase(eq_finder, 3)
tablebase.TableIO().load(table, "states.txt")

def _create_player(player_type, table):
    if player_type == _CPU:
        return tablebase.TablePlayer(table)
    return gameengine.HumanPlayer()

home = _create_player(args.home, table)
away = _create_player(args.away, table)
play_game(game, home, away, table, args.stats)

