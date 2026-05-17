import boto3, hmac, hashlib, base64, pyotp, qrcode, base64 as b64
from io import BytesIO

client_id = '6j5r08a7qts9202kt8u289j3u5'
client_secret = 'br67387o77vldrl8ndca7g3obl3u6gngehiif8tg3o9mcptmasc'
username = 'chcproai@gmail.com'
password = input('Enter password: ')

message = username + client_id
secret_hash = b64.b64encode(hmac.new(client_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()).decode()

client = boto3.client('cognito-idp', region_name='us-east-1')
response = client.initiate_auth(
    ClientId=client_id,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': username, 'PASSWORD': password, 'SECRET_HASH': secret_hash}
)
session = response.get('Session')

assoc = client.associate_software_token(Session=session)
real_secret = assoc['SecretCode']
print('Real Cognito secret:', real_secret)

uri = pyotp.TOTP(real_secret).provisioning_uri(username, issuer_name='CHCProAI')
print('OTP URI:', uri)

img = qrcode.make(uri)
img.save('new_qr.png')
print('QR code saved as new_qr.png')
