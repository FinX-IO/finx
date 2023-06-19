#! python
# author: Geoff Fite
import os
import pandas as pd
import plotly.graph_objects as go
import finx
from finx.client import FinXClient


def main():
    try:
        finx_client = FinXClient(
            "socket",
            finx_api_endpoint=os.environ['FINX_API_URL'],
            finx_api_key=os.environ['FINX_API_KEY'],
            ssl=True
        )
    except Exception as e:
        raise Exception('Error loading FinXClient')
    finx_client.get_security_reference_data(security_id='912796YB9')
    data_file_name = 'raw_vol_points'
    vol_df = pd.read_csv(data_file_name)
    vol_df['expiration'] = vol_df['expiration'].round(5)
    vol_df = vol_df.sort_values(
        by=['expiration', 'strike']
    ).drop_duplicates(
        ['expiration', 'strike']
    ).drop_duplicates(['expiration', 'price'])
    print(vol_df)
    upload_filename = finx_client.upload_batch_file(vol_df)
    print(f'{upload_filename=}')
    return_files = finx_client.calibrate_vol_surface(
        upload_filename,
        s0=19800.,
        r=0.0,
        q=0.0,
        sig0=0.2,
        return_plots=True
    )
    print(return_files)
    return_dfs = [finx_client._download_file(x) for x in return_files]
    print(return_dfs[1].interpolate())
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=return_dfs[1]['x'],
                y=return_dfs[1]['y'],
                z=return_dfs[1]['z']
            )
        ]
    )
    fig.update_layout(
        autosize=False,
        width=800,
        height=900,
        title='Vol Surface',
        scene=dict(
            xaxis_title='Expiry',
            yaxis_title='Log-Strike',
            zaxis=dict(nticks=10, range=[0, 3]),
            zaxis_title='IVol',
        )
    )
    fig.show()


if __name__ == '__main__':
    print('-----> FinX Test Runner ----->')
    print('-----> Vol Surface Test ----->')
    main()
