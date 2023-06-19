import unittest

from ..client import FinXClient


class GetSecurityReferenceDataTest(unittest.TestCase):
    def test_get_security_reference_data(self):
        finx_client = FinXClient('socket', ssl=True)
        results: dict = finx_client.get_security_reference_data(security_id='912796YB9', as_of_date='2021-01-01')
        self.assertTrue(results['asset_class'] == 'bond')  # add assertion here


if __name__ == '__main__':
    unittest.main()
