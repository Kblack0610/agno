
"""Example test file to demonstrate the Code Testing Agent"""

import unittest

# A simple calculator implementation with a bug
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        # Bug: no check for division by zero
        return a / b

# Test cases for the calculator
class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
    
    def test_subtract(self):
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(1, 5), -4)
    
    def test_multiply(self):
        self.assertEqual(self.calc.multiply(2, 3), 6)
        self.assertEqual(self.calc.multiply(5, 0), 0)
    
    def test_divide(self):
        self.assertEqual(self.calc.divide(6, 3), 2)
        # This test will fail due to division by zero
        # self.assertEqual(self.calc.divide(5, 0), "Error")
        
        # Missing: test for division by zero handling

if __name__ == "__main__":
    unittest.main()
