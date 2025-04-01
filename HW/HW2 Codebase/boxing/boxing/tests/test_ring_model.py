import unittest
from unittest.mock import patch
from boxing.models.ring_model import RingModel
from boxing.models.boxers_model import Boxer

class TestRingModel(unittest.TestCase):
    """Unit tests for the RingModel class."""
    def setUp(self):
        """Set up a fresh ring and two sample boxers for each test."""
        self.ring = RingModel()
        #Two sample boxers we’ll reuse
        self.boxer1 = Boxer(id=1, name="nicole", weight=140, height=164, reach=68.0, age=20)
        self.boxer2 = Boxer(id=2, name="Ivy", weight=130, height=158, reach=70.0, age=21)

    def test_enter_ring(self):
        """Test: allow adding a single boxer to the ring."""
        self.ring.enter_ring(self.boxer1)
        self.assertEqual(len(self.ring.get_boxers()), 1)

    def test_enter_ring_error(self):
        """Test: raise TypeError if non-Boxer object is added."""
        with self.assertRaises(TypeError):
            self.ring.enter_ring("not a boxer")

    def test_enter_ring_overflow(self):
        """Test: raise ValueError if trying to add more than 2 boxers."""
        self.ring.enter_ring(self.boxer1)
        self.ring.enter_ring(self.boxer2)
        with self.assertRaises(ValueError):
            self.ring.enter_ring(self.boxer1)

    def test_clear_ring(self):
        """Test: clear all boxers from the ring."""
        self.ring.enter_ring(self.boxer1)
        self.ring.clear_ring()
        self.assertEqual(len(self.ring.get_boxers()), 0)

    def test_with_not_enough_boxers(self):
        """Test: raise error if a fight is started with less than 2 boxers."""
        self.ring.enter_ring(self.boxer1)
        with self.assertRaises(ValueError):
            self.ring.fight()

    @patch('boxing.models.ring_model.get_random', return_value=0.1)
    @patch('boxing.models.ring_model.update_boxer_stats')
    def test_fight_return_winner_and_clears_ring(self, mock_update_stats, mock_rand):
        """Test: run a fight, return the winner, and clear the ring."""
        self.ring.enter_ring(self.boxer1)
        self.ring.enter_ring(self.boxer2)

        winner_name=self.ring.fight()
        # Check that a winner was returned by name
        self.assertIn(winner_name, [self.boxer1.name, self.boxer2.name])
         # Ring should now be empty
        self.assertEqual(len(self.ring.get_boxers()), 0)
        # One win + one loss = 2 calls to update_boxer_stats
        self.assertEqual(mock_update_stats.call_count, 2)  # one win, one loss

    def test_skill_float(self):
        """Test: return a float when calculating fighting skill."""
        skill = self.ring.get_fighting_skill(self.boxer1)
        self.assertIsInstance(skill, float)


if __name__ == '__main__':
    unittest.main()