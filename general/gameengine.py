from enum import Enum
from getpass import getpass

class PlayerState(object):
    def __init__(self, pieces=10, score=0):
        self.score = score
        self.pieces = pieces

    def state_after_move(self, pieces, won):
        if pieces > self.pieces:
            raise ValueError("Tried to move more than available pieces")
        return PlayerState(self.pieces-pieces, self.score+won)

    def add_score(self, score):
        return PlayerState(self.pieces, self.score+score)

    def __eq__(self, other):
        if isinstance(other, PlayerState):
            return self.score == other.score and self.pieces == other.pieces
        return False

    def __hash__(self):
        return hash((self.score, self.pieces))

    def __lt__(self, other):
        return (self.score, self.pieces) < (other.score, other.pieces)

    def __gt__(self, other):
        return (self.score, self.pieces) > (other.score, other.pieces)

class State(object):
    def __init__(self, home_state, away_state):
        self.home_state = home_state
        self.away_state = away_state

    @property
    def pieces_in_play(self):
        return self.home_state.pieces + self.away_state.pieces

    @property
    def score_leader(self):
        if self.home_wins > self.away_wins:
            return Result.HOME
        if self.away_wins > self.home_wins:
            return Result.AWAY
        return Result.DRAW

    @property
    def home_wins(self):
        return self.home_state.score

    @property
    def away_wins(self):
        return self.away_state.score

    @property
    def home_pieces(self):
        return self.home_state.pieces

    @property
    def away_pieces(self):
        return self.away_state.pieces

    def normalize(self):
        if self.away_state > self.home_state:
            return State(self.away_state, self.home_state)
        return self

    def can_move(self, home=0, away=0):
        return self.home_pieces >= home and self.away_pieces >= away and home >= 0 and away >= 0

    @staticmethod
    def initial(pieces=100):
        return State(PlayerState(pieces), PlayerState(pieces))

    def move(self, home_pieces, away_pieces):
        new_home = self.home_state.state_after_move(home_pieces, home_pieces > away_pieces)
        new_away = self.away_state.state_after_move(away_pieces, away_pieces > home_pieces)
        return State(new_home, new_away)

    def add_score(self, home=0, away=0):
        return State(self.home_state.add_score(home), self.away_state.add_score(away))

    def __eq__(self, other):
        if isinstance(other, State):
            return self.home_state == other.home_state and self.away_state == other.away_state
        return False

    def __hash__(self):
        return hash((self.home_state, self.away_state))

    def __str__(self):
        return "State(score=%s:%s, pieces=%s:%s)" % (self.home_state.score, self.away_state.score, self.home_state.pieces, self.away_state.pieces)

class Result(Enum):
    HOME=1
    DRAW=0.5
    AWAY=0

class WinCondition(object):
    def __init__(self, first_to=4):
        self.first_to = first_to

    def winner(self, state):
        if state.home_wins >= self.first_to:
            return Result.HOME
        elif state.away_wins >= self.first_to:
            return Result.AWAY
        elif state.pieces_in_play > 0:
            return None
        elif state.home_wins > state.away_wins:
            return Result.HOME
        elif state.away_wins > state.home_wins:
            return Result.AWAY
        return Result.DRAW

    def normalize(self, state):
        return state.add_score(home=-self.first_to, away=-self.first_to)


    def __str__(self):
        return "first_to=%s" % (self.first_to, )

class Game(object):
    def __init__(self, state, win_condition):
        self.state=state
        self.win_condition = win_condition

    @staticmethod
    def create(win_at=4, pieces=100):
        return Game(State.initial(pieces), WinCondition(win_at))

    @property
    def winner(self):
        return self.win_condition.winner(self.state)

    def __str__(self):
        return "Game(%s, %s)" % (self.win_condition, self.state)

    def play_move(self, home_pieces, away_pieces):
        if self.state.can_move(home=home_pieces, away=away_pieces):
            state = self.state.move(home_pieces, away_pieces)
            return Game(state, self.win_condition)
        print("Error, one player tried to move too many pieces")
        return self


class HumanPlayer(object):
    def __init__(self):
        pass

    def player_name(self, is_home):
        if is_home:
            return "home"
        return "away"

    def post_move(self, state, is_home):
        req = "how many pieces should %s move: " % (self.player_name(is_home))
        val = None
        while val is None:
            try:
                val = int(getpass(req))
            except ValueError:
                print("Error, illegal input!")
        return val
