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

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home'))

@app.route('/home')
def home():
    # login stuff
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('/')

    # for using spotipy functions
    sp = spotipy.Spotify(auth = token_info['access_token'])

    # retrieve user playlist data and store in var
    current_playlists = sp.current_user_playlists()['items']

    # initialize data array to be passed to html
    playlist_data = []

    for i in range(len(current_playlists)):
        data = []
        name = current_playlists[i].get('name')
        id = current_playlists[i].get('id')
        data.append(id)
        data.append(name)
        playlist_data.append(data)
    print(len(playlist_data))

    return render_template('selection.html', html_playlist_data=playlist_data)

@app.route('/token')
def retrieve_token():
    token = get_token()
    return jsonify({'token': token})

@app.route('/customize', methods=['POST', 'GET'])
def customize():
    playlist_id = request.form.get('id')
    playlist_name = request.form.get('name')
    settings_array = request.form.getlist('custom[]')
    token = get_token()

    if not (playlist_id and playlist_name):
        return redirect('/')
       
    new_recs = []
    if settings_array:
        # sp varibale code from selection function until I sent data via post request or more secure method
        try:
            token_info = get_token()
        except:
            print('User not logged in')
            return redirect('/')
        sp = spotipy.Spotify(auth=token_info['access_token'])


        # retrieve data and assign to variables
        pl_id = request.form.get('id')
        pl_name = request.form.get('name')

        # checkpoint to see if all data passed is integers
        idx = list(range(len(settings_array)))
        for i in idx:

            # error handling to see if data was inputted correctly
            try:
                settings_array[i] = float(settings_array[i])
                settings_array[i] = settings_array[i]/10
            except:
                return redirect(url_for('home'))
            
            # to convert from website range to actual needed number for spotipy function

            # tempo and size should be used as entered but other params need to be a float between 0 and 1

            # keeping tempo max + min and size unchanged
            if i < 4 or i == 10:
                settings_array[i] = int(settings_array[i]*10)

            # turn into strings so params can be passed
            # settings_array[i] = str(settings_array[i])


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
            songs_list = sp.playlist_tracks(pl_id)['items']
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        # initialize list of the song ids
        id_list = []
        for song in range(len(songs_list)):
            if (song < 5):
                id = songs_list[song].get('track').get('id')
                id_list.append(id)

        try:
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
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        for i in range(len(rec_data)):
            uri = rec_data[i]['uri']
            name = rec_data[i]['name']
            artists = ""
            for artist in rec_data[i]['artists']:
                artists += artist['name'] + ', '
            artists = artists[:len(artists) - 2]
            new_recs.append([uri, name, artists])
    
    return render_template('customize.html', 
                           pl_data=[playlist_id, 
                           playlist_name], 
                           token=token, 
                           new_recs=new_recs)

@app.route('/expand', methods=['POST', 'GET'])
def expand():
    if request.method == 'POST':
        # sp varibale code from selection function until I sent data via post request or more secure method
        try:
            token_info = get_token()
        except:
            print('User not logged in')
            return redirect('/')
        sp = spotipy.Spotify(auth=token_info['access_token'])


        # retrieve data and assign to variables
        pl_id = request.form.get('id')
        pl_name = request.form.get('name')
        settings_array = request.form.getlist('custom[]')

        # convert numbers to proper type for spotify api
        for i in range(len(settings_array)):

            # error handling for input data type
            try:
                settings_array[i] = float(settings_array[i])
            except:
                return redirect(url_for('home'))

            if 10 > i > 3:
                settings_array[i] = settings_array[i]/10


        # control for out-of-range values
        # and convert some values from 0-10 to 0-1 range
        tmin = settings_array[0] if 200 >= settings_array[0] >= 0 else 0.0
        tmax = settings_array[1] if 200 >= settings_array[1] >= 0 else 200.0
        pmin = settings_array[2] if 100 >= settings_array[2] >= 0 else 0.0
        pmax = settings_array[3] if 100 >= settings_array[2] >= 0 else 100.0
        imin = settings_array[4]/10 if 10 >= settings_array[4] >= 0 else 0.0
        imax = settings_array[5]/10 if 10 >= settings_array[5] >= 0 else 1.0
        dmin = settings_array[6]/10 if 10 >= settings_array[6] >= 0 else 0.0
        dmax = settings_array[7]/10 if 10 >= settings_array[7] >= 0 else 1.0
        vmin = settings_array[8]/10 if 10 >= settings_array[8] >= 0 else 0.0
        vmax = settings_array[9]/10 if 10 >= settings_array[9] >= 0 else 1.0
        size = settings_array[10] if settings_array[10] in range(101) else 20

        #handle for max < min
        if tmin > tmax:
            tmin, tmax = tmax, tmin
        if pmin > pmax:
            pmin, pmax = pmax, pmin
        if imin > imax:
            imin, imax = imax, imin
        if dmin > dmax:
            dmin, dmax = dmax, dmin
        if vmin > vmax:
            vmin, vmax = vmax, vmin

        try:
            songs_list = sp.playlist_tracks(pl_id)['items']
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        # initialize list of the song ids
        id_list = []
        for song in range(len(songs_list)):
            if (song < 5):
                id = songs_list[song].get('track').get('id')
                id_list.append(id)
        # initiliaze recommendations list
        rec_uri_list = []

        try:
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
        except Exception as e:
            print('Error contacting spotify API: ', e)
            return redirect(url_for('home'))
        
        for i in range(len(rec_data)):
            rec = rec_data[i].get('uri')
            rec_uri_list.append(rec)


        new_name = pl_name + '_expand'


        # code to make the program not spit out the same name multiple times - very messy
        current_playlists = sp.current_user_playlists()['items']
        idx = list(range(len(current_playlists)))
        
        # indexing created playlists and getting rid of matching names
        counter =  1
        match = False
        condition = True
        while condition == True:
            match = False
            counter = str(counter)
            loop_name = new_name + counter
            for i in idx:
                name = str(current_playlists[i].get('name'))
                if name == loop_name:
                    counter = int(counter)
                    match = True
            if match == True:
                counter += 1
            else:
                new_name = loop_name
                condition = False


        user_id = sp.current_user()['id']
        sp.user_playlist_create(user=user_id, name=new_name)

        current_playlists = sp.current_user_playlists()['items']
        idx = list(range(len(current_playlists)))
        for playlist in idx:
            name = current_playlists[playlist].get('name')
            if name == new_name:
                expand_uri = current_playlists[playlist].get('uri')
        sp.playlist_add_items(playlist_id = expand_uri,items=rec_uri_list)

        return redirect(url_for('home', msg='success'))
    else:
        return redirect('/')




# oauth

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external = True))
        
    now = int(time.time())
    
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

# oauth

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

app.run(debug=True)