import argparse
from general import tablebase, equilibriumfinder

parser = argparse.ArgumentParser(prog="Generals", description="fill generals tablebase")
parser.add_argument('-p', '--pieces', type=int, default=100)
parser.add_argument('-w', '--wins', type=int, default=3)
parser.add_argument('-s', '--save-file', default="states.txt")
args = parser.parse_args()

eq_finder = equilibriumfinder.create()
table = tablebase.TableBase(eq_finder, args.wins)
tablebase.TableBuilder(table).fill_to_pieces(args.pieces, args.wins)
tablebase.TableIO().save(table, "states.txt")
