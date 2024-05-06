import os
import streamlit as st
import time
import urllib.request
import re
from pytube import YouTube
import spotipy
from spotipy import SpotifyOAuth, SpotifyOauthError
from dotenv import load_dotenv

# https://open.spotify.com/user/mastiff03?si=ce27f0222fe44fa6

def main():
# set streamlit page config
    st.set_page_config(
            page_title="Spotify playlist downloader",
            page_icon="./icon.png", 
            layout="centered",
            initial_sidebar_state="collapsed",
            )
    
# load enviromental variables from .env file
    load_dotenv('.env')
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

# set needed sessions
    if "spotipy_client" not in st.session_state:
        st.session_state.spotipy_client = 0

    if "user_authorise" not in st.session_state:
        st.session_state.user_authorise = False

    if "user_playlists" not in st.session_state:
        st.session_state.user_playlists = []

    if "playlist_tracks" not in st.session_state:
        st.session_state.playlist_tracks = []

    if "is_downloading" not in st.session_state:
        st.session_state.is_downloading = False

# streamlit UI
    col1, col2 = st.columns([1,4])
    with col1:
        st.image("icon.png", width=120)
    with col2:
        st.header('Download your favourite :green[Spotify] playlists and albums', divider='green')

    user_url = st.text_input('Paste below your profile link', placeholder ='e.g. https://open.spotify.com/user/123456789')

    if st.button("Authorize", use_container_width=True):
        if user_url:
            try:
                st.session_state.user_playlists = []
# create spotify client
                auth_menager = SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    scope="user-library-read playlist-read-private playlist-read-collaborative",
                )

                st.session_state.user_authorise = True
                st.session_state.spotipy_client = spotipy.Spotify(auth_manager=auth_menager)
    # change the name for easier accessibility
                sp = st.session_state.spotipy_client

# retrieve names and ids of playlists and albums
                user_playlist_data = sp.current_user_playlists()['items']
                user_album_data = sp.current_user_saved_albums()['items']

    # add playlists to session variable
                for item in user_playlist_data:
                    st.session_state.user_playlists.append([[item['name'], item['id']], item['type']])
                
    # add albums to session variable
                for item in user_album_data:
                    st.session_state.user_playlists.append([[item['album']['name'], item['album']['id']], item['album']['type']])

    # user_playlists array looks like [[name, id], type]
    # type means playlist or album

                progress_text = "Operation in progress. Please wait."
                progress_bar = st.progress(0, text=progress_text)

                for percent_complete in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(1)
                progress_bar.empty()

            except SpotifyOauthError as e:
                st.write(f"Spotify OAuth setup error: {e}")

    # raise it when url is empty
        else:
            st.warning('Paste your profile link', icon="⚠️")
    

    if st.session_state.user_authorise:
        download_direction = st.text_input("Set direction where playlist will be downloaded", placeholder="Default C:/")

# retrieve playlist/album name from array and forward it to selectbox
        playlists_names = []
        for i in st.session_state.user_playlists:
            playlists_names.append(i[0][0])
        selected_playlist = st.selectbox(
        'Pick playlist/album you want to download:',
        (playlists_names),
        placeholder="Select playlist...")

# start download button
        if st.button("Download", use_container_width=True):
            st.session_state.is_downloading = True
            st.session_state.playlist_tracks = []
    # change the name for easier accessibility
            sp = st.session_state.spotipy_client

# retrieve tracks from the selected playlist by name and artist
            for i in st.session_state.user_playlists:
                if i[0][0] == selected_playlist:
                    playlist_id = i[0][1]
                    playlist_type = i[1]
    # type division into playlist and album is needed because spotipy uses two different methods to retrieve the tracks

    # we have to bypass spotipy limit which is set to 100 tracks
            if playlist_type == 'playlist':
                total = sp.playlist_tracks(playlist_id=playlist_id)['total']
                if total > 100:
                    offset = 0
                    while offset <= total:
                        tracks = sp.playlist_tracks(playlist_id=playlist_id, offset=offset)['items']
                        for track in tracks:
                            st.session_state.playlist_tracks.append([track['track']['artists'][0]['name'], track['track']['name']])
                        offset += 100
                else:
                    tracks = sp.playlist_tracks(playlist_id=playlist_id)['items']
                    for track in tracks:
                        st.session_state.playlist_tracks.append([track['track']['artists'][0]['name'], track['track']['name']])
                        
            if playlist_type == 'album':
                tracks = sp.album_tracks(album_id=playlist_id)['items']
                for track in tracks:
                    st.session_state.playlist_tracks.append([track['artists'][0]['name'], track['name']])

# stop downloading button
            if st.button("Stop downloading", use_container_width=True):
                st.session_state.is_downloading = False

# specify and make the direction to download files (default is C:/)
            if download_direction == '':
                download_path = "C:/"
            else:
                download_path = download_direction
    # we need to get rid of forbidden symbols when creating a folder
            download_folder = os.path.join(download_path, re.sub('[\/:*?<>|"]','', selected_playlist))
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)

            with st.spinner("Downloading..."):
                for track in st.session_state.playlist_tracks:
                    if not st.session_state.is_downloading:
                        break
# search for tracks in Youtube
                    search_query = urllib.parse.quote(f"{track[0]} {track[1]}")
                    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={search_query}")
                    video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]
                    yt = YouTube(f"https://youtube.com/watch?v={video_id}")

# download tracks via pytube
    # we need to get rid of forbidden symbols as above
                    filename = f"{track[0]} - {track[1]}.mp4"
                    filename = re.sub('[\/:*?<>|"]','', filename)
                    yt.streams.filter(only_audio=True).first().download(output_path=download_folder, filename=filename)

                st.session_state.is_downloading = False
                st.balloons()
                st.success('Download complete', icon="✅")

if __name__ == "__main__":
    main()