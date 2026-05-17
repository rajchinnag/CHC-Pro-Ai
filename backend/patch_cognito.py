import sys
sys.path.insert(0, '.')

with open('app/services/cognito_service.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

new_methods = '''
    def get_totp_secret(self, email: str, password: str) -> tuple:
        """
        Initiate auth, then call associate_software_token to get Cognito's
        real TOTP secret. Returns (secret, cognito_session).
        """
        resp = self.c.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME":    email,
                "PASSWORD":    password,
                "SECRET_HASH": _secret_hash(email),
            },
            ClientId=self.cid,
        )
        challenge = resp.get("ChallengeName")
        if challenge == "MFA_SETUP":
            session = resp["Session"]
        elif "AuthenticationResult" in resp:
            # No MFA yet - use access token
            access_token = resp["AuthenticationResult"]["AccessToken"]
            assoc = self.c.associate_software_token(AccessToken=access_token)
            return assoc["SecretCode"], None
        else:
            session = resp.get("Session", "")

        assoc = self.c.associate_software_token(Session=session)
        return assoc["SecretCode"], assoc["Session"]

    def verify_totp_with_cognito(self, cognito_session: str, code: str, email: str) -> None:
        """
        Verify the TOTP code with Cognito using the session from associate_software_token.
        This activates TOTP MFA for the user in Cognito.
        """
        try:
            self.c.verify_software_token(
                Session=cognito_session,
                UserCode=code,
                FriendlyDeviceName="CHCProAI"
            )
        except Exception as e:
            err = str(e)
            if "CodeMismatchException" in err or "EnableSoftwareTokenMFAException" in err:
                raise CognitoError(
                    "That code is incorrect. Check your authenticator app and try again. "
                    "Codes refresh every 30 seconds.",
                    "CodeMismatchException"
                )
            raise CognitoError(str(e), "TOTP_VERIFY_ERROR")

        # Enable MFA for this user
        self.c.admin_set_user_mfa_preference(
            UserPoolId=self.pool,
            Username=email,
            SoftwareTokenMfaSettings={"Enabled": True, "PreferredMfa": True},
        )

'''

# Insert before 'cognito = CognitoService()'
insert_point = 'cognito = CognitoService()'
content = content.replace(insert_point, new_methods + insert_point)

with open('app/services/cognito_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! New methods added.')
