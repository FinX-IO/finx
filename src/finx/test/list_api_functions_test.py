import unittest

from ..client import FinXClient


class ListAPIFunctionsTest(unittest.TestCase):
    def test_list_api_functions(self):
        finx_client = FinXClient('socket', ssl=True)
        function_list = finx_client.list_api_functions()
        self.assertTrue(len(function_list) > 10)  # add assertion here


if __name__ == '__main__':
    unittest.main()
