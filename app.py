import os
import streamlit as st
import spotipy
import time
from spotipy import SpotifyOAuth, SpotifyOauthError
from dotenv import load_dotenv

# https://open.spotify.com/user/mastiff03?si=ce27f0222fe44fa6
# https://open.spotify.com/user/21olcekn5v4tdmnhtiqsjpicq?si=66cabee344064d3d

def main():
# set streamlit page config
    st.set_page_config(
            page_title="Spotify playlist downloader",
            page_icon="./favicon.png", 
            layout="centered",
            initial_sidebar_state="collapsed",
            )
    
# load enviromental variables from .env file
    load_dotenv('.env')
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    # redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

# set needed sessions
    if "spotipy_client" not in st.session_state:
        st.session_state.spotipy_client = 0

    if "user_authorise" not in st.session_state:
        st.session_state.user_authorise = False

    if "user_playlists" not in st.session_state:
        st.session_state.user_playlists = {}

    if "playlist_tracks" not in st.session_state:
        st.session_state.playlist_tracks = {}
    
    st.header('🎶Download your favourite :green[Spotify] playlists', divider='green')
    
    user_url = st.text_input('Paste below your profile link', placeholder ='e.g. https://open.spotify.com/user/123456789')


    if st.button("Authorize", use_container_width=True) and user_url:
        try:
            st.session_state.user_playlists = {}
# create spotify client
            auth_menager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope="user-library-read playlist-read-private playlist-read-collaborative",
            )

            st.session_state.user_authorise = True
            st.session_state.spotipy_client = spotipy.Spotify(auth_manager=auth_menager)
            sp = st.session_state.spotipy_client

# retrieve names and ids of playlists
            user_playlist_data = sp.current_user_playlists()['items']
            for item in user_playlist_data:
                st.session_state.user_playlists[item['name']] = item['id']

            progress_text = "Operation in progress. Please wait."
            progress_bar = st.progress(0, text=progress_text)

            for percent_complete in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent_complete + 1, text=progress_text)
            time.sleep(1)
            progress_bar.empty()

        except SpotifyOauthError as e:
            print(f"Spotify OAuth setup error: {e}")

    if st.session_state.user_authorise:
        selected_playlist = st.selectbox(
        'Pick playlist you want to download:',
        (st.session_state.user_playlists.keys()),
        placeholder="Select playlist...")

        if st.button("Download", use_container_width=True):
            st.session_state.playlist_tracks = {}
            sp = st.session_state.spotipy_client

# retrive selected playlist tracks by name and artist
            playlist_id = st.session_state.user_playlists[selected_playlist]
            # we have to bypass spotipy limit which is set to 100 tracks
            total = sp.playlist_tracks(playlist_id=playlist_id)['total']
            if total > 100:
                offset = 0
                while offset <= total:
                    tracks = sp.playlist_tracks(playlist_id=playlist_id, offset=offset)['items']
                    for track in tracks:
                        st.session_state.playlist_tracks[track['track']['name']] = track['track']['artists'][0]['name']
                    offset += 100
            else:
                tracks = sp.playlist_tracks(playlist_id=playlist_id)['items']
                for track in tracks:
                    st.session_state.playlist_tracks[track['track']['name']] = track['track']['artists'][0]['name']

            st.write(st.session_state.playlist_tracks)


if __name__ == "__main__":
    main()