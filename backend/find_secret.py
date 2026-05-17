import pyotp

# The code Google Authenticator showed
ga_code = input('Enter current Google Authenticator code: ')

# Try our stored secret
secrets_to_try = [
    'KQZXWCZWJZP5HDWZRJ4KBALEBKQTQBEK',  # old
]

# Get current stored secret
import boto3
client = boto3.client('cognito-idp', region_name='us-east-1')
response = client.admin_get_user(UserPoolId='us-east-1_QVSXqhOPK', Username='chcproai@gmail.com')
for attr in response['UserAttributes']:
    if 'totp' in attr['Name']:
        secrets_to_try.append(attr['Value'])
        print('Current stored secret:', attr['Value'])

for secret in secrets_to_try:
    try:
        totp = pyotp.TOTP(secret)
        if totp.verify(ga_code, valid_window=2):
            print(f'MATCH FOUND! Secret: {secret}')
        else:
            print(f'No match: {secret} generates {totp.now()}')
    except Exception as e:
        print(f'Error with {secret}: {e}')
