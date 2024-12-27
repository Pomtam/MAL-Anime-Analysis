import json
import requests
import os
import secrets
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('MAL_CLIENT_ID')
CLIENT_SECRET = os.getenv('MAL_CLIENT_SECRET')
TOKEN_FILE = 'token.json'

# 1. Generate a new Code Verifier / Code Challenge.
def get_new_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]

# 2. Print the URL needed to authorise your application.
def print_new_authorisation_url(code_challenge: str):
    url = f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&code_challenge={code_challenge}'
    print(f'Authorise your application by clicking here: {url}\n')

# 3. Generate a new token.
def generate_new_token(authorisation_code: str, code_verifier: str) -> dict:
    url = 'https://myanimelist.net/v1/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': authorisation_code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code'
    }

    response = requests.post(url, data)
    response.raise_for_status()  # Check whether the request contains errors

    token = response.json()
    token['expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=token['expires_in'])).isoformat()
    
    save_token(token)
    print('Token generated successfully and saved to token.json!')

    return token

# 4. Refresh the token.
def refresh_token(refresh_token: str) -> dict:
    url = 'https://myanimelist.net/v1/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(url, data)
    response.raise_for_status()  # Check whether the request contains errors

    token = response.json()
    token['expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=token['expires_in'])).isoformat()
    
    save_token(token)
    print('Token refreshed successfully and saved to token.json!')

    return token

# 5. Save the token to a file.
def save_token(token: dict):
    with open(TOKEN_FILE, 'w') as file:
        json.dump(token, file, indent=4)

# 6. Load the token from a file.
def load_token() -> dict:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, 'r') as file:
        return json.load(file)

# 7. Check if the token is valid or needs refreshing.
def get_valid_token() -> str:
    token = load_token()

    if not token:
        raise ValueError('No token found. Please generate a new one.')

    expires_at = datetime.fromisoformat(token['expires_at'])
    if datetime.now(timezone.utc) >= expires_at:
        print('Token expired. Refreshing...')
        token = refresh_token(token['refresh_token'])

    return token['access_token']

# 8. Test the API by requesting your profile information.
def print_user_info():
    access_token = get_valid_token()
    url = 'https://api.myanimelist.net/v2/users/@me'
    response = requests.get(url, headers={
        'Authorization': f'Bearer {access_token}'
    })

    response.raise_for_status()
    user = response.json()
    print(f"\n>>> Greetings {user['name']}! <<<")

if __name__ == '__main__':
    if not os.path.exists(TOKEN_FILE):
        code_verifier = code_challenge = get_new_code_verifier()
        print_new_authorisation_url(code_challenge)

        authorisation_code = input('Copy-paste the Authorisation Code: ').strip()
        generate_new_token(authorisation_code, code_verifier)

    print_user_info()
