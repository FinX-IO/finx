#! python
"""
author: dick mule
purpose: unittest the list api functions method
"""
import unittest

from finx.client import FinXClient, ClientTypes


class ListAPIFunctionsTest(unittest.TestCase):

    def test_list_api_functions(self):
        finx_client = FinXClient(ClientTypes.socket)
        finx_client.load_functions()
        function_list = finx_client.list_api_functions()
        self.assertTrue(len(function_list) > 10)  # add assertion here
        finx_client.cleanup()


if __name__ == '__main__':
    unittest.main()
