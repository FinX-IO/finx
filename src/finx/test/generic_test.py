#! python
"""
author: dick mule
purpose: generic unit test
"""
import unittest


class MyTestCase(unittest.TestCase):
    """Simple Test Cashe"""

    def test_something(self):
        """
        Test something

        :return: None Type Object
        :rtype: None
        """
        something = True
        something_else = something
        self.assertEqual(something, something_else)  # add assertion here


if __name__ == "__main__":
    unittest.main()
