import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        something = True
        something_else = something
        self.assertEqual(something, something_else)  # add assertion here


if __name__ == '__main__':
    unittest.main()
