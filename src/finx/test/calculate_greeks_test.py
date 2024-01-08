import unittest

from ..client import  FinXClient


class CalculateGreeksTest(unittest.TestCase):
    def test_list_api_functions(self):
        finx_client = FinXClient('socket', ssl=True)
        results: dict = finx_client.calculate_greeks(101, 100, 0.01, 0.1, 0., 0.25, 5.)
        print(f'{results=}')
        self.assertTrue(results['result']['greeks']['vol'] > 0.0)  # add assertion here


if __name__ == '__main__':
    unittest.main()
