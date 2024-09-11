# -*- coding: utf-8 -*-
"""
Created on Sun Jul  9 16:17:09 2023

@author: alexe
"""
from dotenv import load_dotenv
from socket import INADDR_MAX_LOCAL_GROUP
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template, jsonify
import os

app = Flask(__name__, template_folder = './template', static_folder = './static')
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
# random characters - doesnt matter
app.secret_key = 'jdybmhf5h*&@#$hjf^&8744ihefohoiwehf'
TOKEN_INFO = 'token_info'
load_dotenv()

@app.route('/')
def frontpage():
    return render_template('frontpage.html')

@app.route('/login')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

"""
Description: Stores access token info in cookie
"""
@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home'))

"""
Description: Handle cases with retrieving access token
Output: Object: Spotify OAuth Token data
"""
def get_token():
    token_info = session.get(TOKEN_INFO, None)

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
        redirect_uri = 'http://127.0.0.1:5000/redirect',
        scope = ['playlist-read-private',
                 'playlist-read-collaborative',
                 'playlist-modify-private',
                 'playlist-modify-public',
                 'user-library-read',
                 'user-modify-playback-state',
                 'streaming']
        )

"""
Description: Retrieves all of the user's playlists and passes them to the html
Outputs: html_playlist_data: List[List[str]] - id and name for all of user's playlists
"""
@app.route('/home')
def home():
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('/')
    print(token_info)
    sp = spotipy.Spotify(auth = token_info['access_token'])

    # retrieve user playlist data and store in var
    current_playlists = sp.current_user_playlists()['items']

    # playlist names and ids to be passed to html
    playlist_data = []
    for i in range(len(current_playlists)):
        data = []
        name = current_playlists[i].get('name')
        id = current_playlists[i].get('id')
        data.append(id)
        data.append(name)
        playlist_data.append(data)

    return render_template('selection.html', html_playlist_data=playlist_data)

# endpoint to serve the token for the customize page javascript
@app.route('/token')
def retrieve_token():
    token = get_token()
    return jsonify({'token': token})

"""
Description: Retrieves input data from user's settings, then collects a list of
             new recommendations to pass to the html
Inputs: playlist_id: str
        playlist_name: str
        settings_array: Optional[list] - min and max values for tempo, popularity, instrumentalness,
                                         danceability, valence, and single value for size, all to
                                         be passed to a recommendations request to spotipy
Outputs: pl_data: List[str] - id and name of currently expanding playlist
         token: Object - OAuth token to be sent to javascript
         new_recs: List[Optional[List[str]]] - list of uri, name, and artists for each new recommendation
"""
@app.route('/customize', methods=['POST', 'GET'])
def customize():
    playlist_id = request.form.get('id')
    playlist_name = request.form.get('name')
    settings_array = request.form.getlist('custom[]')
    if not (playlist_id and playlist_name):
        return redirect('/')
    
    try:
        token_info = get_token()
        print(token_info)
    except:
        print('User not logged in')
        return redirect('/')
       
    new_recs = []

    if settings_array:
    
        sp = spotipy.Spotify(auth = token_info['access_token'])

        # convert numbers to proper type for spotify api
        idx = list(range(len(settings_array)))
        for i in idx:

            # error handling to see if data was inputted correctly
            # also conver to proper data type for api
            try:
                settings_array[i] = float(settings_array[i])
                settings_array[i] = settings_array[i]/10
            except:
                return redirect(url_for('home'))

            if i < 4 or i == 10:
                settings_array[i] = int(settings_array[i]*10)

        # unpack customization array
        # order: tempo, popularity, instrumentalness, danceability, and valence

        tmin = settings_array[0]
        tmax = settings_array[1]
        pmin = settings_array[2]
        pmax = settings_array[3]
        imin = settings_array[4]
        imax = settings_array[5]
        dmin = settings_array[6]
        dmax = settings_array[7]
        vmin = settings_array[8]
        vmax = settings_array[9]
        size = settings_array[10]

        try:
            songs_list = sp.playlist_tracks(playlist_id)['items']
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        # initialize list of the input song ids
        id_list = []
        for song in range(len(songs_list)):
            if (song < 5):
                id = songs_list[song].get('track').get('id')
                id_list.append(id)

        try:
            print('start')
            rec_data = sp.recommendations(seed_tracks=id_list, 
                                          limit=size, 
                                          min_valence=vmin, 
                                          min_tempo=tmin, 
                                          min_popularity=pmin, 
                                          min_instrumentalness=imin, 
                                          min_danceability=dmin, 
                                          max_danceability=dmax, 
                                          max_instrumentalness=imax, 
                                          max_popularity=pmax, 
                                          max_tempo=tmax, 
                                          max_valence=vmax)['tracks']
            print('end')
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        # build recs data
        for i in range(len(rec_data)):
            uri = rec_data[i]['uri']
            name = rec_data[i]['name']
            artists = ""
            for artist in rec_data[i]['artists']:
                artists += artist['name'] + ', '
            artists = artists[:len(artists) - 2]
            new_recs.append([uri, name, artists])
        print(new_recs)
    
    return render_template('customize.html', 
                           pl_data=[playlist_id, 
                           playlist_name], 
                           token=token_info, 
                           new_recs=new_recs)

app.run(debug=True)