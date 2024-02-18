# using requests implementation
from authlib.integrations.requests_client import OAuth2Session
import json

# using httpx implementation (async)
#from authlib.integrations.httpx_client import AsyncOAuth2Client

with open(r'../modules/osmAuthSecret.json', 'r') as file:
    data = json.loads(file.read())
    client_id = data['client_id']
    client_secret = data['client_secret']
    scope = data['scope']
    userAgent = 'PyNavi/0.1'
    redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

client = OAuth2Session(
    client_id,
    client_secret,
    scope=scope,
    redirect_uri=redirect_uri,
    headers={'User-Agent': userAgent})

# generate authorization URL and state (save it for later)
uri, state = client.create_authorization_url('https://www.openstreetmap.org/oauth2/authorize')

# redirect the user to the authorization URL and wait for callback
print(uri)

# ...
# ...

# after authorization, capture the full callback URL
# replace `request.url` with the actual URL you received
callback_url = str(uri)

# fetch the OAuth2 token using the state and callback URL
client.token = client.fetch_token(
    'https://www.openstreetmap.org/oauth2/token',
    state=state,
    authorization_response=callback_url,
    grant_type='authorization_code')

# make authenticated API request
r = client.get('https://api.openstreetmap.org/api/0.6/user/details.json')
r.raise_for_status()
print(r.json())
