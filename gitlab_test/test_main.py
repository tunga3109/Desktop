# test_main.py
import unittest
from main import add_numbers

class TestAddNumbers(unittest.TestCase):

    def test_add_positive_numbers(self):
        result = add_numbers(3, 5)
        self.assertEqual(result, 8)

if __name__ == "__main__":
    unittest.main()
