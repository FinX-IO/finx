#! python
"""
author: dick mule
purpose: test functionality
"""
import inspect

from finx.client import FinXClient, ClientTypes
from finx.utils.concurrency import hybrid, Hybrid


@hybrid
async def main():
    print('FinXClient imported')
    finx_socket = FinXClient(
        ClientTypes.socket,
        finx_api_key='FINX_API_KEY',
        finx_api_endpoint='FINX_API_ENDPOINT'
    )
    await finx_socket.load_functions()
    greeks: Hybrid = finx_socket.calculate_greeks
    print(f'{greeks=} / {inspect.getfullargspec(greeks.my_func)}')
    result = await greeks(101, 100, 0.01, 0.1, 0., 0.25, 5.)
    print(f'{result=}')
    finx_rest = FinXClient(
        ClientTypes.rest,
        finx_api_key='FINX_API_KEY',
        finx_api_endpoint='FINX_API_ENDPOINT'
    )
    await finx_rest.load_functions()
    greeks2: Hybrid = finx_socket.calculate_greeks
    print(f'{greeks2=} / {inspect.getfullargspec(greeks2.my_func)}')
    result2 = await greeks2(101, 100, 0.01, 0.1, 0., 0.25, 5.)
    print(f'{result2=}')
    print('FINISHED')


if __name__ == '__main__':
    main()
