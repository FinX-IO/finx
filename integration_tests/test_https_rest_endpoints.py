#! python
# author: Geoff Fite
import os
import urllib.request

base_api_url = os.environ['FINX_API_KEY']

finx_api_key = os.getenv('FINX_API_KEY')
user_email = os.getenv('FINX_USER_EMAIL')

endpoints = [
    {
        'function': 'hello_world',
        'params': {},
    },
    {
        'function': 'validate_user',
        'params': {
            'user_uuid': finx_api_key
        }
    },
    {
        'function': 'validate_user_email',
        'params': {
            'user_email': user_email
        }
    },
]


# set this up as a main function
def main():
    for endpoint in endpoints:
        url = base_api_url + '/cms2/' + endpoint['function']
        params = endpoint['params']
        url += '?' + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url) as response:
            html = response.read()
            print('**********')
            print(endpoint['function'], html)
            print(' ')


if __name__ == '__main__':
    main()
