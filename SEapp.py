# -*- coding: utf-8 -*-
"""
Created on Sun Jul  9 16:17:09 2023

@author: alexe
"""

from socket import INADDR_MAX_LOCAL_GROUP
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template

app = Flask(__name__, template_folder = './template', static_folder = './static')

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# random characters - doesnt matter
app.secret_key = 'jdybmhf5h*&@#$hjf^&8744ihefohoiwehf'

TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('home', msg ='welcome'))

@app.route('/home/<msg>')
def home(msg):

    # error handling 
    if msg == 'success':
        htmlmsg = "Playlist expanded. If your playlist was shorter than expected, try broadening your customization."
    elif msg == 'error':
        htmlmsg = "Please try to re-enter your inputs as specified or broaden your customization specifications."
    else:
        htmlmsg = "Please select a playlist to expand based on the first five songs"
    

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

    # code to pass playlist ids and names to html
    # for loop set up index to correspond to playlist data items
    idx = list(range(len(current_playlists)))

    # initialize data array to be passed to html
    playlist_data = []

    for playlist in idx:
        # inialize individual playlist data list
        data = []
        # retrieve name
        name = current_playlists[playlist].get('name')
        # retrieve id
        id = current_playlists[playlist].get('id')
        # add to id and name to data
        data.append(id)
        data.append(name)
        playlist_data.append(data)

    return render_template('selection.html', html_playlist_data=playlist_data, htmlmsg=htmlmsg)

@app.route('/customize', methods=['POST', 'GET'])
def customize():
    if request.method == 'POST':
        selected_playlist_data = request.form.getlist('selection_data[]')
        return render_template('customize.html', pl_data=selected_playlist_data)
    else:
        return redirect('/')

# I need to add a try function cuz im passing the playlist id through get request
# so when the playlist is generated there is no errors passing the id at the final step

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
        pl_info = request.form.getlist('playlistdata[]')
        settings_array = request.form.getlist('custom[]')

        # assign separate parts of data to own var
        playlist_id = pl_info[0]
        playlist_name = pl_info[1]

        # checkpoint to see if all data passed is integers
        idx = list(range(len(settings_array)))
        for i in idx:

            # error handling to see if data was inputted correctly
            try:
                settings_array[i] = float(settings_array[i])
                settings_array[i] = settings_array[i]/10
            except:
                return redirect(url_for('home', msg='error'))
            
            # to convert from website range to actual needed number for spotipy function

            # tempo and size should be used as entered but other params need to be a float between 0 and 1

            # keeping tempo max + min and size unchanged
            if i < 4 or i == 10:
                settings_array[i] = int(settings_array[i]*10)

            # turn into strings so params can be passed
            # settings_array[i] = str(settings_array[i])


        # in order abbrevations: tempo, popularity, instrumentalness, danceability, and valence

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


        # error handling to see if playlist id data didnt get messed with
        try:
            songs_list = sp.playlist_tracks(playlist_id)['items']
        except:
            return redirect(url_for('home', msg='error'))
        
        idx = list(range(len(songs_list)))
    
        # initialize list of the song ids
        id_list = []
        for song in idx:
            if (song < 5):
                id = songs_list[song].get('track').get('id')
                id_list.append(id)
        # initiliaze recommendations list
        rec_uri_list = []
        try:
            rec_data = sp.recommendations(seed_tracks=id_list, limit=size, min_valence=vmin, min_tempo=tmin, min_popularity=pmin, min_instrumentalness=imin, min_danceability=dmin, max_danceability=dmax, max_instrumentalness=imax, max_popularity=pmax, max_tempo=tmax, max_valence=vmax)['tracks']
        except:
            # error occurs cuz of timeout, specifications are too strict to generate a recommendation, and error with inputting data
            return redirect(url_for('home', msg='error'))
        idx = list(range(len(rec_data)))
        for i in idx:
            rec = rec_data[i].get('uri')
            rec_uri_list.append(rec)


        new_name = playlist_name + '_expand'


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

        # go to developer.spotify.com
        # create app with http://127.0.0.1:5000/redirect redirect uri to get personal spotify api client id and key
        client_id = '[your spotify api id]',
        client_secret = '[your spotify api key]',
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-read'
        )

app.run(debug=True)