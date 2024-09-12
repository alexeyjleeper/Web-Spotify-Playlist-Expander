function addTrackListeners(player, id, token) {
    recsContainer = document.getElementById('recsContainer');
    playlist_id = recsContainer.getAttribute('data-playlist-id');

    // build list of all uris
    const allUris = []

    // add event listeners for each rec item
    document.querySelectorAll('.rec').forEach(element => {
        const uri = element.getAttribute('data-uri');
        const add = element.querySelector('.add');
        attachEventListener('click', add, handleAddClick, playlist_id, uri, token);
        allUris.push(uri);
    });
    
    // add event listeners for the all recs item
    const playAll = document.getElementById('playAll');
    const addAll = document.getElementById('addAll');
    const skip = document.getElementById('skip');
    attachEventListener('click', playAll, handlePlayClick, id, allUris, token, player);
    attachEventListener('click', addAll, handleAddClick, playlist_id, allUris, token);
    attachEventListener('click', skip, handleSkip, player)
}

function handleSkip(element, player) {
    player.getCurrentState()
        .then(state => {
            if (!state) {
                return
            } else if (state.paused) {
                const playAll = document.getElementById('playAll');
                playAll.textContent = '❚❚';
            }
        })
        .catch(err => {
            console.error('Error retrieving state from playback: ', err);
        });
        player.nextTrack().catch(err => {
            console.log('Error skipping to next track: ', err);
        });
}

function handlePlayClick(element, id, uri, token, player) {
    parent = element.parentNode.parentNode;
    selected_song = parent.getAttribute('data-uri');
    player.getCurrentState()
        .then(state => {

            // player has not been started, 
            if (!state){
                playTrack(id, uri, token);
                element.style.color='#1DB954';
                element.textContent = '❚❚';
            
            // logic for pause and resume on the currenty playing song
            } else if (state.paused) {
                player.resume()
                .then(() => {
                    element.textContent = '❚❚';
                })
                .catch(err => {
                    console.error('Error resuming Spotify playback: ', err);
                });
            } else {
                player.pause()
                .then(() => {
                    element.textContent = '▶';
                })
                .catch(err => {
                    console.error('Error pausing Spotify playback: ', err);
                });
            }
        });
}

function handleAddClick(element, playlist_id, uri, token) {
    addToPlaylist(playlist_id, uri, token);
    element.style.color='#1DB954';
}

function playTrack(id, uri, token) {

    // handle for single uri or all uris
    const formatUri = typeof uri === 'string' ? [uri] : uri;

    fetch(`https://api.spotify.com/v1/me/player/play?device_id=${id}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            uris: formatUri
        })})
        .then(response => {
            if (!response.ok) {
                console.log('new track playing');
            } else {
                console.log('Error playing track: ', response.statusText);
            }
        })
        .catch(error => {
            console.log('Error sending play request to Spotify API: ', error);
        });
}


function addToPlaylist(playlist_id, uri, token) {

    // handle for single uri or all uris
    const formatUri = typeof uri === 'string' ? [uri] : uri;

    fetch(`https://api.spotify.com/v1/playlists/${playlist_id}/tracks`, {
        method: 'POST',
        headers : {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'uris' : formatUri
        })})
        .then(response => {
            if (response.ok) {
                console.log('track added');
            } else {
                console.log('Error adding track: ', response.statusText);
            }
        })
        .catch(err => {
            console.log('Error sending add request to Spotify API: ', err)
        });
}


// handle event listeners storage and removal
const eventListeners = {
    click: []
};

function attachEventListener(type, element, callback, ...args) {
    if (element) {
        const handler = (event) => callback(element, ...args);
        element.addEventListener(type, handler);
        eventListeners[type].push({ element, handler });
    }
}

function removeEventListeners() {
    for (const type in eventListeners) {
        eventListeners[type].forEach(({ element, handler }) => {
            element.removeEventListener(type, handler);
        });
    }
}

window.onSpotifyWebPlaybackSDKReady = () => {
    fetch('../token')
        .then(response => response.json())
        .then(data => {
            const token = data.token.access_token;
            const player = new Spotify.Player({
                name: 'Playback Client',

                //sdk provides cb method
                getOAuthToken: cb => {cb(token)}
            });

            // Error handling
            player.addListener('initialization_error', ({ message }) => console.error(message));
            player.addListener('authentication_error', ({ message }) => console.error(message));
            player.addListener('account_error', ({ message }) => console.error(message));
            player.addListener('playback_error', ({ message }) => console.log(message));

            player.addListener('ready', ({ device_id }) => {
                addTrackListeners(player, device_id, token);
            });
            
            try {
                player.connect();
                console.log('Spotify Playback initialized');
            } catch(err) {
                console.error('Error connecting playback device to Spotify: ', err);
            }
            
            // listener to color the path of the playAll feature
            player.addListener('player_state_changed', ({
                    track_window: { current_track }
                }) => {
                    document.querySelectorAll('.rec').forEach(element => {
                        const uri = element.getAttribute('data-uri');
                        if (uri === current_track.uri) {
                            element.querySelectorAll('p').forEach(p => {
                                p.style.color='#1DB954';
                            })

                        }
                    });
                });
        })
        .catch(err => {
            console.log('Error initializing playback object: ', err)
        });
}

// handle for alive event listeners when user exits
window.addEventListener('beforeunload', () => {
    removeEventListeners();
});