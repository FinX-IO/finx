#! python
"""
author: dick mule
purpose: test functionality
"""
import inspect

import pandas as pd

from finx.client import FinXClient, ClientTypes
from finx.utils.concurrency import hybrid, Hybrid


@hybrid
async def main():
    print('FinXClient imported')
    finx_socket = FinXClient(
        ClientTypes.socket,
        finx_api_key=None,
        finx_api_endpoint=None
    )
    await finx_socket.load_functions()
    greeks: Hybrid = finx_socket.calculate_greeks
    print(f'{greeks=} / {inspect.getfullargspec(greeks.my_func)}')
    result = await greeks(101, 100, 0.01, 0.1, 0., 0.25, 5.)
    print(f'{result=}')
    # deal_information = await finx_socket.get_deal_information(
    #     security_id='75575WAA4',
    #     as_of_date='2024-09-30'
    # )
    # print(f'{deal_information=}')
    # exchange_rates = await finx_socket.forecast_exchange_rates(
    #     ['USD', 'GBP'], '2023-09-30', 'GBP'
    # )
    # print(f'{exchange_rates=}')
    finx_socket.context.clear_cache()
    args = dict(
        security_id=['91282CCA7', 'DE0001141786'] * 10000,
        as_of_date=['2021-05-19', '2020-04-21', '2021-05-18', '2020-04-20'] * 5000
    )
    batch_result = await finx_socket.batch_get_security_reference_data(args)
    print(pd.DataFrame(batch_result).T)
    finx_socket.cleanup()
    # NOW REST
    finx_rest = FinXClient(
        ClientTypes.rest,
        finx_api_key=None,
        finx_api_endpoint=None
    )
    await finx_rest.load_functions()
    finx_rest.context.clear_cache()
    greeks2: Hybrid = finx_rest.calculate_greeks
    print(f'{greeks2=} / {inspect.getfullargspec(greeks2.my_func)}')
    result2 = await greeks2(101, 100, 0.01, 0.1, 0., 0.25, 5.)
    print(f'{result2=}')
    print('FINISHED')


if __name__ == '__main__':
    main()
