import requests
import json

URL = 'http://127.0.0.1:6543'

user = {'password': 'test',
        'email': 'dupa@dupa.com',
        'user_name':'fdggsdsdg'}

result = requests.get(URL + '/api/0.1/users')

print(result.status_code)
# print(result.text)

result = requests.get(URL + '/api/0.1/users/1')

print(result.status_code)
print(result.text)

result = requests.post(URL + '/api/0.1/users',
                       headers={"Content-Type": "application/json", },
                       data=json.dumps(user))

print(result.status_code)
print(result.text)

result = requests.patch(URL + '/api/0.1/users/14',
                       headers={"Content-Type": "application/json", },
                       data=json.dumps(user))

print(result.status_code)
print(result.text)
