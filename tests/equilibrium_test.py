import unittest
import numpy
from general import equilibriumfinder as ef


class EquilibriumTest(unittest.TestCase):
    def setUp(self):
        self.nh_finder = ef.NashHowsonFinder()
        self.ns_finder = ef.NashSupportFinder()
        self.nhl_finder = ef.NashHowsonLexFinder()
        self.trivial_finder = ef.TrivialMoveFinder()
        self.reducer = ef.SpaceReducer(self.nh_finder)

    def test_reduction_howson(self):
        move_space = numpy.array(
          [[1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1.  ,1.  ,1.  ,1.  ,1.  ,1. ],
           [1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1.  ,1.  ,1.  ,1.  ,1. ],
           [1.  ,1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1.  ,1.  ,1.  ,1. ],
           [1.  ,1.  ,1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1.  ,1.  ,1. ],
           [1.  ,1.  ,1.  ,1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1.  ,1. ],
           [1.  ,1.  ,1.  ,1.  ,1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5 ,1. ],
           [1.  ,1.  ,1.  ,1.  ,1.  ,1.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.  ,0.5]])
        eq = self.reducer.move_distribution(move_space)
        self.assertIsNotNone(eq, "howson w/ reduction should produce solution")
        self._dump(eq)
        self.assertAlmostEqual(self._prob(eq, move_space), 0.3333, 4, "payoff found with sup vector")
        print("Payoff: ", self._prob(eq, move_space))

    def test_reduction_trivial(self):
        move_space = numpy.array(
                [[0.5, 0.,  0. ],
                 [1.,  0.5, 0. ],
                 [1.,  1.,  0.5]])
        eq = ef.SpaceReducer(self.trivial_finder).move_distribution(move_space)
        self.assertIsNotNone(eq, "reduction should provide trival solution")
        self._dump(eq)
        self.assertAlmostEqual(self._prob(eq, move_space), 0.5, 4, "strat is all [2,2]")

    def test_row_reduction(self):
        move_space = numpy.array(
                [[0.,    0.5,   1.,    1.,    1.,    1.,    1.   ],
                 [0.,    0.,    0.5,   1.,    1.,    1.,    1.   ],
                 [0.,    0.,    0.,    0.5,   1.,    1.,    1.   ],
                 [0.,    0.,    0.,    0.,    0.5,   1.,    1.   ],
                 [0.5,   0.,    0.,    0.,    0.,    0.5,   1.   ],
                 [1.,    0.333, 0.,    0.,    0.,    0.,    0.5  ],
                 [1.,    1.,    0.,    0.,    0.,    0.,    0.   ],
                 [1.,    1.,    1.,    0.,    0.,    0.,    0.   ],
                 [1.,    1.,    1.,    1.,    0.,    0.,    0.   ],
                 [1.,    1.,    1.,    1.,    1.,    0.,    0.   ],
                 [1.,    1.,    1.,    1.,    1.,    1.,    0.   ]])
        eq = self.reducer.move_distribution(move_space)
        self.assertIsNotNone(eq, "howson sould find solution")
        self._dump(eq)
        self.assertAlmostEqual(self._prob(eq, move_space), 0.57891414, 4, "payoff found with sup vector")

    def test_approx_stuff(self):
        move_space = numpy.array(
                [[0.    ,0.5   ,1.    ,1.    ,1.    ,1.    ,1.    ,1.    ,1.   ],
                 [0.711 ,0.    ,0.    ,0.5   ,1.    ,1.    ,1.    ,1.    ,1.   ],
                 [1.    ,0.672 ,0.    ,0.    ,0.5   ,1.    ,1.    ,1.    ,1.   ],
                 [1.    ,1.    ,0.667 ,0.    ,0.    ,0.5   ,1.    ,1.    ,1.   ],
                 [1.    ,1.    ,1.    ,0.579 ,0.    ,0.    ,0.5   ,1.    ,1.   ],
                 [1.    ,1.    ,1.    ,1.    ,0.5   ,0.    ,0.    ,0.5   ,1.   ],
                 [1.    ,1.    ,1.    ,1.    ,1.    ,0.5   ,0.    ,0.    ,1.   ],
                 [1.    ,1.    ,1.    ,1.    ,1.    ,1.    ,0.333 ,0.    ,0.5  ],
                 [1.    ,1.    ,1.    ,1.    ,1.    ,1.    ,1.    ,1.    ,0.   ]])


        eq = ef.MinimizeApproxFinder().move_distribution(move_space)
        #eq = self.nhl_finder.move_distribution(numpy.asarray(move_space))
        self.assertIsNotNone(eq, "approx finder should provide solution")
        self._dump(eq, digits=4)
        print("approx prob: ", self._prob(eq, move_space))

        #eq_real = self.ns_finder.move_distribution(move_space)
        eq_real = (
                numpy.array([0.2005, 0.141, 0., 0.1433, 0.0653, 0., 0.2086, 0., 0.2413]),
                numpy.array([0.2064, 0.0698, 0., 0.2236, 0., 0.0353, 0.2236, 0., 0.2413]))
        self._dump(eq_real, digits=4)
        real_prob = self._prob(eq_real, move_space)
        print("real prob: ", real_prob)
        self.assertAlmostEqual(self._prob(eq, move_space), real_prob, msg="approximation should provide similar strat", delta=0.02)
        self.assertAlmostEqual(self._prob([eq[0], eq_real[1]], move_space), real_prob, msg="not exploitable strat for away", delta=0.05)
        self.assertAlmostEqual(self._prob([eq_real[0], eq[1]], move_space), real_prob, msg="not exploitable strat for home", delta=0.05)

        print("best home prob: ", self._prob([eq_real[0], eq[1]], move_space))
        print("best away prob: ", self._prob([eq[0], eq_real[1]], move_space))



    def _dump(self, eq, digits=2):
        print(numpy.round(eq[0], digits), numpy.round(eq[1], digits))

    def _prob(self, eq, ms):
        return float(eq[0].dot(ms).dot(eq[1].transpose()))
