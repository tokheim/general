import json
import numpy
from general import gameengine as ge

class TableBase(object):
    def __init__(self, eq_engine, win_at=4):
        self.table = {}
        self.win_condition = ge.WinCondition(win_at)
        self.norm_win_condition = ge.WinCondition(0)
        self.eq_engine = eq_engine

    def put(self, state, prob):
        self.table[state] = prob

    def state_prob_pairs(self):
        return self.table.items()

    def lookup(self, state):
        return self._lookup_norm(self.win_condition.normalize(state))

    def _lookup_win_norm(self, state):
        won = self.norm_win_condition.winner(state)
        if won:
            return won.value
        norm = state.normalize()
        val = self.table[norm]
        if norm == state:
            return val
        return 1-val

    def _dist_win_chance(self, move_space, home_dist, away_dist):
        ms = move_space[:home_dist.size, :away_dist.size]
        return numpy.round(home_dist.dot(ms).dot(away_dist.transpose()), 3)

    def calc_move_space(self, state, win_normalized=False):
        if not win_normalized:
            state = self.win_condition.normalize(state)
        space = numpy.zeros((state.home_pieces+1, state.away_pieces+1),dtype="float32")
        for i in range(0, state.home_pieces+1):
            all_won = True
            for j in range(0, state.away_pieces+1):
                if i == 0 and j == 0:
                    space[0,0]=state.score_leader.value
                    all_won = False
                    continue
                space[i,j] = self._lookup_win_norm(state.move(i, j))
                if space[i,j] < 1:
                    all_won = False
            if all_won:
                return space[0:i+1,:]
        return space

    def calc_winchance(self, state, win_normalized=False):
        if not win_normalized:
            state = self.win_condition.normalize(state)
        move_space = self.calc_move_space(state, win_normalized=True)
        home_dist, away_dist = self.eq_engine.move_distribution(move_space)
        return self._dist_win_chance(move_space, home_dist, away_dist)

    def debug_state(self, state):
        move_space = self.calc_move_space(state)
        home_dist, away_dist = self.eq_engine.move_distribution(move_space)
        home_dist = numpy.round(home_dist, 3)
        away_dist = numpy.round(away_dist, 3)
        prob = self._dist_win_chance(move_space, home_dist, away_dist)
        print("\nSpace:\n%s\nhome_dist: %s\naway_dist: %s\nprob: %s" % (move_space, home_dist, away_dist, prob))

    def comment_moves(self, state, home_move, away_move):
        move_space = self.calc_move_space(state)
        home_dist, away_dist = self.eq_engine.move_distribution(move_space)
        prev_prob = self._percent(self._dist_win_chance(move_space, home_dist, away_dist))
        new_prob = self._percent(self.calc_winchance(state.move(home_move, away_move)))
        exp_home = self._expected_win(move_space, home_move, away_dist)
        exp_away = self._expected_win(1-move_space.transpose(), away_move, home_dist)
        print("home winchance went from %s to %s" % (prev_prob, new_prob))
        print("Home:")
        self._comment_move(home_dist, home_move, exp_home)
        print("Away:")
        self._comment_move(away_dist, away_move, exp_away)

    def _percent(self, val):
        return str(round(100*val, 1)) + "%"

    def _expected_win(self, move_space, move, col_dist):
        return move_space[move,:].dot(col_dist.transpose())

    def _comment_move(self, dist, move, expectancy):
        optimal_usage = self._percent(dist[move])
        less_usage = self._percent(numpy.sum(dist[:move]))
        more_usage = self._percent(numpy.sum(dist[move+1:]))
        print("  Move should be used %s of time, has expected winrate of %s." % (optimal_usage, self._percent(expectancy)))
        print("  Use fewer pieces %s of time, more %s" % (less_usage, more_usage))
        print("  Best moves in position:")
        for i in reversed(dist.argsort()[-5:]):
            if dist[i] > 0:
                print("    %s pieces: %s," % (i, self._percent(dist[i])))

    def suggest_move(self, state, is_home):
        move_space = self.calc_move_space(state)
        dist = self.eq_engine.move_distribution(move_space)[1-is_home]
        dist[dist<0] = 0
        return numpy.random.choice(len(dist), p=dist)

class ProgressUpdater(object):
    def __init__(self, max_work, message, digits=4):
        self.message = message
        self.max_work = float(max_work)
        self.cur_work = 0
        self.digits = digits

    def _percent_val(self, delta=0):
        return round((self.cur_work+delta)/self.max_work, 4) * 100

    def increment(self, val=1):
        should_print = self._percent_val() != self._percent_val(val)
        self.cur_work += val
        if should_print:
            print(self.message % (str(self._percent_val()) + "%", ))

class TableBuilder(object):
    def __init__(self, table):
        self.table = table

    def _gen_for_score(self, home_score, away_score, max_pieces):
        prog_msg = "%s:%s" % (home_score, away_score) + ": filled %s"
        progress = ProgressUpdater(max_pieces**2, prog_msg)
        complete_winner = False
        for i in range(0, max_pieces+1):
            away_range = range(0, max_pieces+1)
            if home_score == away_score:
                away_range = range(0, i+1)
            away_could_win = False
            for j in away_range:
                home = ge.PlayerState(i,home_score)
                away = ge.PlayerState(j,away_score)
                state = ge.State(home, away)
                prob = 1
                if home == away and not complete_winner:
                    prob = 0.5
                elif not complete_winner:
                    prob = self.table.calc_winchance(state, win_normalized=True)
                away_could_win = away_could_win or (prob < 1)
                progress.increment()
                yield state, prob
            if not away_could_win:
                complete_winner = True

    def _fill_for_score(self, home_score, away_score, max_pieces):
        for state, prob in self._gen_for_score(home_score, away_score, max_pieces):
            self.table.put(state, prob)

    def fill_instructions(self, home_score, away_score, max_pieces):
        for state, prob in self._gen_for_score(home_score, away_score, max_pieces):
            print(state, ": prob ", prob)

    def fill_to_pieces(self, max_pieces, win_depth):
        for home_score in range(-1, -win_depth-1, -1):
            for away_score in range(home_score, -win_depth-1, -1):
                self.table.eq_engine.dump_stats()
                print("Filling for %s:%s" % (home_score, away_score))
                self._fill_for_score(home_score, away_score, max_pieces)


class TableIO(object):
    def __init__(self):
        pass

    def save(self, table, filename):
        with open(filename, "w") as f:
            for state, prob in table.state_prob_pairs():
                data = [state.home_wins, state.home_pieces, state.away_wins, state.away_pieces, prob]
                f.write(json.dumps(data))
                f.write("\n")

    def load(self, table, filename):
        with open(filename, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    return
                data = json.loads(line)
                home = ge.PlayerState(data[1], data[0])
                away = ge.PlayerState(data[3], data[2])
                table.put(ge.State(home, away), data[-1])


class TablePlayer(object):
    def __init__(self, table):
        self.table = table

    def post_move(self, state, is_home):
        return self.table.suggest_move(state, is_home)
