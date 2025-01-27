#! python
"""
author: Dick Mule
purpose: Unit test for get security reference data
"""

import unittest

from finx.client import FinXClient, ClientTypes


class GetSecurityReferenceDataTest(unittest.TestCase):
    """Unittest to get security reference data"""

    def test_get_security_reference_data(self):
        """
        Method running socket client test

        :return: None type object
        :rtype: None
        """
        finx_client = FinXClient(ClientTypes.socket)
        finx_client.load_functions()
        results: dict = finx_client.get_security_reference_data(
            security_id="912796YB9", as_of_date="2021-01-01"
        )
        self.assertTrue(results["asset_class"] == "bond")  # add assertion here
        # args = dict(
        #     security_id=['US912797FJ15', '658909E28'],
        #     as_of_date=['2023-10-05', '2024-01-01'],
        #     include_schedule=['True'] * 2
        # )
        # data = finx_client.batch_get_security_reference_data(args)
        # print(f'{data=}')
        # self.assertTrue(all(isinstance(x['security_id'], str) for x in data))
        finx_client.cleanup()


if __name__ == "__main__":
    unittest.main()
