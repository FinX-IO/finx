import unittest

from ..client import FinXClient


class GetSecurityReferenceDataTest(unittest.TestCase):
    def test_get_security_reference_data(self):
        finx_client = FinXClient('socket', ssl=True)
        results: dict = finx_client.get_security_reference_data(security_id='912796YB9', as_of_date='2021-01-01')
        self.assertTrue(results['asset_class'] == 'bond')  # add assertion here
        # args = dict(
        #     security_id=['US912797FJ15', '658909E28'],
        #     as_of_date=['2023-10-05', '2024-01-01'],
        #     include_schedule=['True'] * 2
        # )
        # data = finx_client.batch_get_security_reference_data(args)
        # print(f'{data=}')
        # self.assertTrue(all(isinstance(x['security_id'], str) for x in data))



if __name__ == '__main__':
    unittest.main()
