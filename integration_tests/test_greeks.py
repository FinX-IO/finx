#! python
# run test for tick_client and client
# author: Geoff Fite
import os
import asyncio
import time
import finx
from finx.client import FinXClient, ClientTypes
import pandas as pd
import numpy as np


def main(environment: str = "dev"):
    print('main routine kicked off using api_key:', os.getenv('FINX_API_KEY'))
    finx_api_key = os.getenv('FINX_API_KEY')
    # TEST: Calculate a set of greeks on an option
    client = FinXClient(ClientTypes.socket)
    # s0, k, r, sigma, q, T, p, option_side, option_type
    greeks: dict = client.calculate_greeks(101, 100, 0.01, 0.88, 0, 5, 0.88, 'call', 'european')
    print(f'**********************\nGREEKS: {greeks}\n\n')


if __name__ == '__main__':
    print('-----> FinX Test Runner ----->')
    print('-----> Calculate Greeks Test ----->')
    # RUN ASYNC
    check_event_loop = asyncio.get_event_loop()
    # Hybrid decorated methods can be called like synchronous methods
    print(f'{check_event_loop}')
    if check_event_loop.is_running():
        asyncio.set_event_loop(check_event_loop)
        # * The only caveat is if Hybrid method is called from within a running event loop *
        check_event_loop.run_until_complete(main())
    else:
        main()

