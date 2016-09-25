from flask import Flask, render_template, request, redirect
from flask import make_response, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc, and_, func
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

# Import local modules
import setup
from database_setup import Base, Playlist, Song, User, PlaylistSongs, engine

app = setup.app  # define app from setup.py

# domain is only used to be able to create the full url for social share,
# could probably find a better way to do this
domain = "http://localhost"

# Create the DBSession and then session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# client id for google + oauth connection
# This should be changed to handle the google oauth you implement
# Add a json file called client_secrets.json to the main folder (the json
# file downloaded from the credentials page)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# User functions for creating and fetching users
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=int(user_id)).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Set general variables for template files
# domain is used in _social-share.html
# login_session is used for getting current user information in templates


@app.context_processor
def user_info():
    return dict(login_session=login_session, domain=domain)


@app.route('/')
def mainPage():
    return render_template('index.html')

# User Pages


@app.route('/login')
def loginPage():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    print "testing"
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return login_session['username']

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/logout')
def logoutPage():
        # Clear the login_session
    login_session.clear()
    flash('You are now logged out')
    return redirect(url_for('mainPage'))


@app.route('/profile')
@app.route('/profile/<int:user_id>')
def profilePage(user_id=None):
    if not user_id and 'username' not in login_session:
        flash('You need to login to view your profile')
        return redirect('/login?redirect=' + url_for('profilePage'))

    if not user_id:
        user_id = login_session['user_id']

    try:
        user = session.query(User).filter_by(id=user_id).one()
    except:
        return render_template('404.html'), 404

    playlists = session.query(Playlist).filter_by(
        user_id=user_id).order_by(Playlist.id.desc())
    return render_template('profile.html', user=user, playlists=playlists)

# Song & Playlist pages


@app.route('/playlists')
def playlistsPage():
    playlists = session.query(Playlist).order_by(Playlist.id.desc())
    return render_template('playlists.html', playlists=playlists)


@app.route('/playlists/<int:playlist_id>')
def singlePlaylistPage(playlist_id):
    try:
        # Try to query the playlist
        playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    except:
        # If not found then render 404
        return render_template('404.html'), 404
    try:
        # Try to query the songs in the playlist
        playlistSongs = session.query(
            PlaylistSongs).filter_by(playlist_id=playlist_id)
    except:
        playlistSongs = None

    return render_template('playlist.html', playlist=playlist,
                           playlistSongs=playlistSongs)


@app.route('/playlists/create-playlist', methods=['GET', 'POST'])
def createPlaylistPage():
    if 'username' not in login_session:
        # if not logged in redirect to login with redirect param for this page
        return redirect('/login?redirect=' + url_for('createPlaylistPage'))
    if request.method == 'POST':
        playlistName = request.form['playlistName']
        playlistDescription = request.form['playlistDescription']
        if playlistName:
            newPlaylist = Playlist(name=playlistName,
                                   description=playlistDescription,
                                   user_id=login_session['user_id'])
            session.add(newPlaylist)
            flash('New Playlist %s created' % newPlaylist.name)
            session.commit()
            # REdirect to the newly created playlist
            return redirect(url_for('singlePlaylistPage',
                                    playlist_id=newPlaylist.id))
        else:
                # If errors notify the user that there are errors
            flash('You have to give your playlist a name')

    # If not redirected to login or the new playlist show the
    # create-playlist.html
    return render_template('create-playlist.html')


@app.route('/playlists/<int:playlist_id>/edit', methods=['GET', 'POST'])
def editPlaylistPage(playlist_id):
    try:
        # See if the playlist exist first
        playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    except:
        playlist = None

    if playlist == None:
        # If playlist doesn't exist redirect to playlistpage
        flash('No playlist found to edit')
        return redirect(url_for('playlistsPage'))
    else:
        if 'username' not in login_session:
                # Check to see if user is logged in
            flash('You need to login in order to do this')
            return redirect('/login?redirect=' +
                            url_for('editPlaylistPage',
                                    playlist_id=playlist_id))

        if login_session['user_id'] != playlist.user_id:
                # Check to see if current user is the creator of this playlist
            flash('You can only edit your own playlists')
            return redirect(url_for('singlePlaylistPage',
                                    playlist_id=playlist_id))
    if request.method == 'POST':
        playlistName = request.form['playlistName']
        playlistDescription = request.form['playlistDescription']
        if playlistName:
            playlist.name = playlistName
            playlist.description = playlistDescription
            session.add(playlist)
            flash('Playlist %s updated' % playlist.name)
            session.commit()
            return redirect(url_for('singlePlaylistPage',
                                    playlist_id=playlist.id))
        else:
            flash('You have to give your playlist a name')

    # If not redirected before show edit-playlist.html
    return render_template('edit-playlist.html', playlist=playlist)


@app.route('/playlists/<int:playlist_id>/delete', methods=['GET', 'POST'])
def deletePlaylistPage(playlist_id):
    try:
        # Check to see if playlist exist
        playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    except:
        playlist = None

    if playlist == None:
        # If playlist doesn't exist redirect to playlistpage
        flash('No playlist found to delete')
        return redirect(url_for('playlistsPage'))
    else:
        if 'username' not in login_session:
                # Check if user is logged in
            flash('You need to login in order to do this')
            return redirect('/login?redirect=' +
                            url_for('editPlaylistPage',
                                    playlist_id=playlist_id))

        if login_session['user_id'] != playlist.user_id:
                # Check if current user is the creator of the playlist
            flash('You can only delete your own playlists')
            return redirect(url_for('singlePlaylistPage',
                                    playlist_id=playlist_id))
    if request.method == 'POST':
        session.delete(playlist)
        session.query(PlaylistSongs).filter_by(
            playlist_id=playlist_id).delete()
        session.commit()
        flash("Playlist %s deleted!" % playlist.name)
        return redirect(url_for('playlistsPage'))

    # If not redirected already show delete-playlist.html
    return render_template('delete-playlist.html', playlist=playlist)


@app.route('/song/<int:song_id>')
def songPage(song_id):
    try:
        # Check to see if song exists
        song = session.query(Song).filter_by(id=song_id).one()
    except:
        # If not show 404
        return render_template('404.html'), 404
    return render_template('song.html', song=song)


@app.route('/song/create', methods=['GET', 'POST'])
def createSongPage():
    if 'username' not in login_session:
        # Chek to see if user is logged in
        flash('You need to login in order to create songs')
        return redirect('/login?redirect=' + url_for('createSongPage'))
    if request.method == 'POST':
        songTitle = request.form['songTitle']
        songArtist = request.form['songArtist']
        songSpotify = request.form['songSpotify']
        songDeezer = request.form['songDeezer']
        songAppleMusic = request.form['songAppleMusic']
        songYoutube = request.form['songYoutube']
        if songTitle and songArtist:
            newSong = Song(title=songTitle, artist=songArtist,
                           spotify_url=songSpotify, deezer_url=songDeezer,
                           apple_music_url=songAppleMusic,
                           youtube_url=songYoutube)
            session.add(newSong)
            flash('New Song %s created' % newSong.title)
            session.commit()
            return redirect(url_for('playlistsPage'))
        else:
            flash('You have to write both Title & Artist')

    # If not redirected already show create-song.html
    return render_template('create-song.html')


@app.route('/song/<int:song_id>/edit', methods=['GET', 'POST'])
def editSongPage(song_id):
    if 'username' not in login_session:
        flash('You need to login in order to edit songs')
        return redirect('/login?redirect=' + url_for('createSongPage'))

    try:
        song = session.query(Song).filter_by(id=song_id).one()
    except:
        song = None

    if song == None:
        flash('No song found to edit')
        return redirect(url_for('playlistsPage'))

    if request.method == 'POST':
        songTitle = request.form['songTitle']
        songArtist = request.form['songArtist']
        songSpotify = request.form['songSpotify']
        songDeezer = request.form['songDeezer']
        songAppleMusic = request.form['songAppleMusic']
        songYoutube = request.form['songYoutube']
        if songTitle and songArtist:
            song.name = songTitle
            song.artist = songArtist
            song.spotify_url = songSpotify
            song.deezer_url = songDeezer
            song.apple_music_url = songAppleMusic
            song.youtube_url = songYoutube
            session.add(song)
            flash('Song %s has been updated' % song.title)
            session.commit()
            return redirect(url_for('playlistsPage'))
        else:
            flash('You have to write both Title & Artist')

    return render_template('edit-song.html', song=song)


@app.route('/search/JSON')
@app.route('/search')
def searchPage():
        # Search page for playlists and songs
    keyword = request.args.get('s', '')  # fetch the keyword from url param ?s=
    # Set songs and playlists to none if no keyword is present
    songs = None
    playlists = None
    if keyword:
        # if keyword query songs and playlists

        # Song query for searching
        # To find for example "Abba Dancing Queen" you can search for:
        # 'ABBA', 'ABBA Dancing Queen', 'Dancing Queen ABBA', 'Dancing Queen'
        # || in the filter concatenates columns, and  ' ' separates them by a space.
        # In order to be able to search with either artist or title first I use
        # an or filter
        songs = session.query(Song).filter(
            "artist || ' ' || title like '%" +
            keyword +
            "%' OR title || ' ' || artist like '%" +
            keyword + "%'").all()

        playlists = session.query(Playlist).filter((Playlist.name.like(
            '%' + keyword + '%') |
            Playlist.description.like('%' + keyword + '%'))).all()

    # if JSON is in the path then output searchresult as json
    if request.path == '/search/JSON':
        # Add the playlists and songs into one json_output
        json_output = jsonify(
            Playlists=[i.serialize for i in playlists],
            Songs=[i.serialize for i in songs])
        return json_output

    return render_template('search.html', songs=songs,
                           playlists=playlists, keyword=keyword)


@app.errorhandler(404)
def page_not_found(error):
        # If a url is not found then show 404
    return render_template('404.html'), 404


# JSON Api endpoint pages

@app.route('/search/song/JSON')
def searchSongJSON():
    keyword = request.args.get('s', '')
    songs = session.query(Song).filter(
        "artist || ' ' || title like '%" +
        keyword +
        "%' OR title || ' ' || artist like '%" +
        keyword + "%'").all()
    return jsonify(Songs=[i.serialize for i in songs])


@app.route('/playlists/JSON')
def playlistsPageJSON():
    playlists = session.query(Playlist)
    return jsonify(Playlists=[i.serialize for i in playlists])


@app.route('/playlists/<int:playlist_id>/JSON')
def singlePlaylistPageJSON(playlist_id):
    try:
        playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    except:
        playlist = None

    return jsonify(Playlist=playlist.serialize)


@app.route('/playlists/<int:playlist_id>/song/<int:song_id>/add')
def addSongToPlaylistPage(playlist_id, song_id):
        # Connect song to a playlist
    output = dict()
    error = []
    # Create the unique SongToPLaylistID by putting together song_id and playlist_id
    # In order to string them together so 1+1 not equals to 2 but instead 11
    addSongToPlaylistID = str(song_id) + '' + str(playlist_id)
    addSongToPlaylistID = int(addSongToPlaylistID)
    if 'username' not in login_session:
        error.append("User not logged in")
    try:
        playlist = session.query(Playlist).filter_by(id=playlist_id).one()
        # Check if playlist exists
    except:
        # Else add error
        playlist = None
        error.append("Playlist not found")

    try:
        song = session.query(Song).filter_by(id=song_id).one()
        # check to see if song exists
    except:
        # Else add error
        song = None
        error.append("Song not found")

    if playlist and 'username' in login_session:
        # Check to see if user is logged in
        if login_session['user_id'] != playlist.user_id:
                # If user is logged in see if user is the creator of the
                # playlist
            error.append("This user can't edit this playlist")

    try:
        playListSongsQ = session.query(PlaylistSongs).filter_by(
            id=addSongToPlaylistID).one()
        checkPlaylistSong = False
        # Check if song is already connected to this playlist
    except:
        checkPlaylistSong = True

    if checkPlaylistSong != True:
        error.append("Song is already in playlist")
        # Add error if song is already in playlist

    if not error:
        # If no errors connect the song to the playlist
        addSongToPlaylist = PlaylistSongs(
            id=addSongToPlaylistID, song_id=song_id,
            playlist_id=playlist_id, user_id=login_session['user_id'])
        session.add(addSongToPlaylist)
        session.commit()
        output['success'] = "Song added to playlist"

    output['error'] = error
    # Jsonify and return the output. This is because this is handled through ajax calls
    # See /src/js/app.js and playlist.html
    return jsonify(output)


@app.route('/playlistsongs/delete/<int:playlistsong_id>')
def deleteSongToPlaylistPage(playlistsong_id):
    output = dict()
    error = []

    if 'username' not in login_session:
        # Check to see if user is logged in
        error.append("User not logged in")

    try:
        playListSongsQ = session.query(PlaylistSongs).filter_by(
            id=playlistsong_id).one()
        # Check if the playlist song connection exists
    except:
        playListSongsQ = None

    if playListSongsQ == None:
        error.append("This song is not in this playlist")
        # If not throw an error

    if playListSongsQ and 'username' in login_session:
        # Have to check if user is logged in again or else this check can throw
        # an error
        if login_session['user_id'] != playListSongsQ.user_id:
                # Check if user is the creator of this connection
            error.append("This user can't edit this playlist")

    if not error:
        # If there are no errors, good for you! Add the connection between song
        # and playlist
        session.delete(playListSongsQ)
        session.commit()
        output['success'] = "Song deleted from playlist"

    output['error'] = error
    return jsonify(output)
