import spotipy
import os
import time
from flask import session, redirect, url_for
from spotipy.oauth2 import SpotifyOAuth

"""
Description: Handle cases with retrieving access token
Output: Object: Spotify OAuth Token data
"""
def get_token():
    token_info = session.get('token_info', None)

    # redirect to login page if user is new
    if not token_info:
        redirect(url_for('login', external = True))
        
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

"""
Description: Returns configured SpotifyOAuth Object
"""
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('ID'),
        client_secret = os.getenv('KEY'),
        redirect_uri = os.getenv('REDIRECT'),
        scope = ['playlist-read-private',
                 'playlist-read-collaborative',
                 'playlist-modify-private',
                 'playlist-modify-public',
                 'user-library-read',
                 'user-modify-playback-state',
                 'streaming']
        )