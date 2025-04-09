
import unittest

class TestExample(unittest.TestCase):
    def test_passing(self):
        self.assertEqual(1 + 1, 2)
    
    def test_failing(self):
        # This test will fail
        self.assertEqual(1 + 1, 3)

if __name__ == "__main__":
    unittest.main()
