import boto3, hmac, hashlib, base64, pyotp

client_id = '6j5r08a7qts9202kt8u289j3u5'
client_secret = 'br67387o77vldrl8ndca7g3obl3u6gngehiif8tg3o9mcptmasc'
username = 'chcproai@gmail.com'
password = input('Enter password: ')
totp_secret = 'FWJTMQIIYYGA7HNDK6UFVJ4IMP7WZZ44'

message = username + client_id
secret_hash = base64.b64encode(hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()).decode()

client = boto3.client('cognito-idp', region_name='us-east-1')
response = client.initiate_auth(
    ClientId=client_id,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': username, 'PASSWORD': password, 'SECRET_HASH': secret_hash}
)
session = response.get('Session')
print('Got session, challenge:', response.get('ChallengeName'))

totp = pyotp.TOTP(totp_secret)
code = totp.now()
print('Using code:', code)

resp2 = client.respond_to_auth_challenge(
    ClientId=client_id,
    ChallengeName='SOFTWARE_TOKEN_MFA',
    Session=session,
    ChallengeResponses={
        'USERNAME': username,
        'SOFTWARE_TOKEN_MFA_CODE': code,
        'SECRET_HASH': secret_hash
    }
)
print('SUCCESS! Token:', resp2['AuthenticationResult']['AccessToken'][:30])
