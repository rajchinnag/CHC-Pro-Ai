import boto3, pyotp, qrcode

username = 'chcproai@gmail.com'
real_secret = 'FWJTMQIIYYGA7HNDK6UFVJ4IMP7WZZ44'

uri = pyotp.TOTP(real_secret).provisioning_uri(username, issuer_name='CHCProAI')
print('OTP URI:', uri)

img = qrcode.make(uri)
img.save('new_qr.png')
print('QR saved as new_qr.png - open and scan with Google Authenticator')
