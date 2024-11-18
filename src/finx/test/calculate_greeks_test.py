#! python
"""
author: dick mule
purpose: Calculate Greeks Test
"""
import unittest

from finx.client import FinXClient, ClientTypes


class CalculateGreeksTest(unittest.TestCase):
    """Unittest for calculating greeks"""

    def test_list_api_functions(self):
        """
        Test List Api functions using socket client

        :return: None Type
        :rtype: None
        """
        finx_client = FinXClient(ClientTypes.socket, ssl=True)
        finx_client.load_functions()
        results: dict = finx_client.calculate_greeks(
            101, 100, 0.01, 0.1, 0.0, 0.25, 5.0
        )
        print(f"{results=}")
        self.assertTrue(results["result"]["greeks"]["vol"] > 0.0)  # add assertion here
        finx_client.cleanup()


if __name__ == "__main__":
    unittest.main()
