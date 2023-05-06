import numpy
import nashpy
from nashpy.algorithms.lemke_howson_lex import lemke_howson_lex
from scipy import optimize
import time

class UniformMoveFinder(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def name(self):
        return self.__class__.__name__

    def move_distribution(self, move_space):
        if self.verbose:
            print("Suggesting really dumb uniform moves for shape\n%s" % (move_space, ))
        return self._even_dist(move_space.shape[0]), self._even_dist(move_space.shape[1])

    def _even_dist(self, num):
        return numpy.ones((num, )) / num

    def dump_stats(self):
        pass


class SequentialMoveFinder(UniformMoveFinder):
    def __init__(self, *finders):
        self.finders = finders
        self.stats = [0]*len(finders)

    def move_distribution(self, move_space):
        for i, finder in enumerate(self.finders):
            moves = finder.move_distribution(move_space)
            if moves:
                self.stats[i] += 1
                return moves

    def dump_stats(self):
        print("Finder invocations:")
        for i, finder, stat in zip(range(len(self.finders)), self.finders, self.stats):
            print("%s, %s: %s" % (i, finder.name(), stat))

class TrivialMoveFinder(UniformMoveFinder):
    def move_distribution(self, move_space):
        moves = self._check_trivial_home(move_space)
        if moves:
            return moves
        moves = self._check_trivial_home((1-move_space).transpose())
        if moves:
            return moves[1], moves[0]

    def _check_trivial_home(self, move_space):
        if move_space.shape[0] == 1:
            home_move = numpy.ones((1, ))
            away_move = numpy.zeros((move_space.shape[1], ))
            away_move[numpy.argmin(move_space)] = 1
            return home_move, away_move
        best_home_probs = numpy.min(move_space, 1)
        idx = -1
        if max(best_home_probs[1:]) >= 1:
            idx = numpy.argmax(best_home_probs[1:]) + 1
        elif best_home_probs[0] >= 1:
            idx = 0
        if idx >= 0:
            home_move = best_home_probs*0
            home_move[idx] = 1
            away_move = numpy.ones((move_space.shape[1], ))/move_space.shape[1]
            return home_move, away_move


class NoisyMoveFinder(UniformMoveFinder):
    def __init__(self, finder, noise=1e-7):
        self.finder = finder
        self._gen_noise = noise

    def name(self):
        return "NoisyMoveFinder(%s)" % (self.finder.name(), )

    def move_distribution(self, move_space):
        noise = (numpy.random.rand(*move_space.shape)*(self._gen_noise*2)) - self._gen_noise
        return self.finder.move_distribution(move_space+noise)

class ConditionalFinder(UniformMoveFinder):
    def __init__(self, finder, min_size=5, min_dim=2):
        self.finder = finder
        self.min_size = min_size
        self.min_dim = min_dim

    def name(self):
        return "ConditionalFinder(%s)" % (self.finder.name(), )

    def move_distribution(self, move_space):
        shape = move_space.shape
        if move_space.size >= self.min_size and shape[0] >= self.min_dim and shape[1] >= self.min_dim:
            return self.finder.move_distribution(move_space)

class DebugFinder(UniformMoveFinder):
    def __init__(self, finder, debug_after=20):
        self.finder = finder
        self.debug_after = debug_after

    def name(self):
        return self.finder.name()

    def move_distribution(self, move_space):
        try:
            #print(self.finder.name(), " finding for shape ", move_space.shape)
            ts = time.time()
            moves = self.finder.move_distribution(move_space)
            dur = time.time() - ts
            if dur > self.debug_after:
                print(self.finder.name(), " spent ", dur, "s finding space for state:\n", move_space)
                #import code; code.interact(local=vars())
            if moves:
                return moves
        except Exception as e:
            print(e, " was thrown finding move")
        #print(self.finder.name(), " could not generate move for state:\n", move_space)
        print(self.finder.name(), " could not generate move for state: ", move_space.shape)



class NashSupportFinder(UniformMoveFinder):
    def __init__(self):
        pass

    def _create_game(self, move_space):
        return nashpy.Game(move_space, 1-move_space)

    def move_distribution(self, move_space):
        rps = self._create_game(move_space)
        eqs = rps.support_enumeration()
        return next(eqs, None)

class NashVertexFinder(NashSupportFinder):
    def __init__(self):
        pass

    def move_distribution(self, move_space):
        rps = self._create_game(move_space)
        eqs = rps.vertex_enumeration()
        return next(eqs, None)

class NashHowsonFinder(NashSupportFinder):
    def __init__(self):
        pass

    def move_distribution(self, move_space):
        rps = self._create_game(move_space)
        for eq in rps.lemke_howson_enumeration():
            if self.is_valid(move_space, *eq):
                return eq

    def is_valid(self, ms, home_eq, away_eq):
        if ms.shape[0] != home_eq.size or ms.shape[1] != away_eq.size:
            return False
        return not (numpy.isnan(home_eq).any() or numpy.isnan(away_eq).any())

class NashHowsonLexFinder(UniformMoveFinder):
    def __init__(self):
        pass

    def move_distribution(self, move_space):
        for label in range(sum(move_space.shape)):
            try:
                eq = lemke_howson_lex(move_space, 1-move_space, initial_dropped_label=label)
                if self._is_valid(eq, move_space):
                    return lemke_howson_lex(move_space, 1-move_space)
            except Exception as e:
                print("Error in calc, ", e)

    def _is_valid(self, eq, move_space):
        if eq is None:
            return False
        if len(eq) != 2:
            return False
        if len(eq[0]) != move_space.shape[0] or len(eq[1]) != move_space.shape[1]:
            return False
        return not (numpy.isnan(eq[0]).any() or numpy.isnan(away_eq).any())

class SpaceReducer(UniformMoveFinder):
    def __init__(self, finder):
        self.finder = finder

        self._execs = 0
        self._iterations = 0
        self._cols_dropped = 0
        self._rows_dropped = 0

    def _reduce(self, move_space):
        row_active = self._bool_arr(move_space.shape[0])
        col_active = self._bool_arr(move_space.shape[1])

        reducing = True
        while reducing:
            self._iterations += 1
            self._discard_cols(move_space.transpose()[col_active,:], row_active)
            reducing = self._discard_cols(1-move_space[row_active,:], col_active)
        return row_active, col_active

    def move_distribution(self, move_space):
        row_active, col_active = self._reduce(move_space)
        self._execs += 1
        self._cols_dropped += numpy.sum(col_active == False)
        self._rows_dropped += numpy.sum(row_active == False)
        #self._debug(move_space, row_active, col_active)
        eqs = self.finder.move_distribution(move_space[row_active,:][:, col_active])
        return self._reconstruct_eqs(eqs, row_active, col_active)

    def _debug(self, move_space, row_active, col_active):
        print("move space:\n", move_space, "\nto:\n", move_space[row_active,:][:,col_active])


    def _reconstruct_eqs(self, eqs, row_active, col_active):
        if eqs is None:
            return None
        row_dist = self._reconstruct_eq(eqs[0], row_active)
        col_dist = self._reconstruct_eq(eqs[1], col_active)
        return row_dist, col_dist

    def _reconstruct_eq(self, eq, active):
        distribution = active*0.0
        distribution[active] = eq
        return distribution


    def _bool_arr(self, dim):
        return numpy.ones((dim, ),dtype=bool)

    def _discard_cols(self, move_space, col_active):
        reduced = False
        for i in range(0, move_space.shape[1]):
            if col_active[i] and self._has_superior_col(move_space, i, col_active):
                col_active[i] = False
                reduced = True
        return reduced

    def _has_superior_col(self, move_space, i, col_active):
        return numpy.sum(numpy.min(move_space[:,col_active] >= move_space[:,(i, )], 0)) > 1

    def name(self):
        return "Reducer(%s)" % (self.finder.name(), )

    def dump_stats(self):
        print("Space reducer dropped ", (self._rows_dropped, self._cols_dropped), " with runs: ", self._execs, " iterations: ", self._iterations)
        self.finder.dump_stats()

class MinimizeApproxFinder(UniformMoveFinder):
    def __init__(self, err=1e-10):
        self.err = err

    def move_distribution(self, move_space):
        if not self.is_usable(move_space):
            return
        res_row = self._calc_row(move_space)
        res_col = self._calc_row(1 - move_space.transpose())
        if res_row.success and res_col.success:
            return res_row.x, res_col.x

    def _calc_row(self, move_space):
        optcalc = OptimizationCalculator(move_space)
        return optcalc.calc(self.err)

    def is_usable(self, move_space):
        #extremes = (move_space >= 1) + (move_space <= 0)
        #return numpy.sum(extremes) / move_space.size > 0.5
        return True

class OptimizationCalculator(object):
    def __init__(self, move_space):
        self.move_space = move_space

    def _normalize(self, x):
        x_pow = numpy.power(2, x)
        return x_pow/numpy.sum(x_pow)

    def objective(self, x):
        x_norm = self._normalize(x)
        return 1 - numpy.min(x_norm.dot(self.move_space))

    def _initial_guess(self):
        return numpy.random.rand(self.move_space.shape[0])

    def calc(self, f_err):
        opts = {'fatol': f_err, 'xatol': 1e-8, 'disp': False, 'maxiter': 1e6}
        res = optimize.minimize(
                self.objective,
                self._initial_guess(),
                method='nelder-mead',
                options = opts)
        if res.success:
            res.x = self._normalize(res.x)
        else:
            print("Failed approx calc, res:\n", res, "move_space:\n", self.move_space)
        return res


def create():
    nash_sup = DebugFinder(NashSupportFinder())
    return SpaceReducer(SequentialMoveFinder(
            TrivialMoveFinder(),
            ConditionalFinder(DebugFinder(NashHowsonFinder())),
            MinimizeApproxFinder(),
            ConditionalFinder(DebugFinder(NashVertexFinder())),
            nash_sup,
            NoisyMoveFinder(nash_sup),
            UniformMoveFinder(verbose=True)))
