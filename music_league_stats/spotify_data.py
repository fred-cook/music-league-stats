import requests
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

# Paste your Spotify API access token here
client_id = "YOUR ID HERE"
secret_token = 'YOUR TOKEN HERE'
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": secret_token,
}
auth_response = requests.post('https://accounts.spotify.com/api/token', data=data)
access_token = auth_response.json().get("access_token")

# Initialize Spotipy with the access token
headers = {"Authorization": f"Bearer {access_token}"}


def get_tracks(track_ids: list[str]) -> pd.DataFrame:
    p = requests.get("https://api.spotify.com/v1/tracks?ids="+
                     ','.join(track_ids), headers=headers)
    
    if p.status_code != 200:
        p.raise_for_status()

    return pd.DataFrame(
        [{
            "date": get_date(track["album"]),
            "track_name": track["name"],
            "popularity": track['popularity'],
            "duration": track["duration_ms"] / 1000,
            "genres": [genre for artist in track["artists"] for genre in artist["genres"]],
        }
        for track in p.json()["tracks"]]
    )

def get_tracks_individual(track_ids: list[str]) -> pd.DataFrame:
    tracks = []
    for track in track_ids:
        p = requests.get("https://api.spotify.com/v1/tracks/"+
                        track, headers=headers)
        
        if p.status_code != 200:
            p.raise_for_status()

        tracks.append(
            {
                "date": get_date(p.json()["album"]),
                "track_name": p.json()["name"],
                "popularity": p.json()['popularity'],
                "duration": p.json()["duration_ms"] / 1000,
                "artist_ids": [artist["id"] for artist in p.json()["artists"]],
            }
        )
    return pd.DataFrame(tracks)

def get_genres(artists: pd.Series) -> pd.Series:
    genres = []
    for artist_list in artists:
        genres_a = []
        for a in artist_list:
            p = requests.get("http://api.spotify.com/v1/artists/" + a, headers=headers)
            genres_a += p.json()["genres"]
        genres.append(genres_a)
    return pd.Series(genres)



def get_features_individual(track_ids: list[str]) -> pd.DataFrame:
    features = []
    for song_id in track_ids:
        p = requests.get("https://api.spotify.com/v1/audio-features/"
                        + song_id, headers=headers)
        if p.status_code != 200:
            json = {}
        else:
            json = p.json()

        features.append(
            {
                "danceability": json.get('danceability', float("nan")),
                "energy": json.get("energy", float("nan")),
                "loudness": json.get('loudness', float("nan")),
                "acousticness": json.get("acousticness", float("nan")),
            }
        )
    return pd.DataFrame(features)


def get_features(track_ids: list[str]) -> pd.DataFrame:
    p = requests.get("https://api.spotify.com/v1/audio-features?ids="
                     +','.join(track_ids), headers=headers)
    if p.status_code != 200:
        p.raise_for_status()

    return pd.DataFrame(
        [{
            "danceability": track['danceability'],
            "energy": track["energy"],
            "loudness": track['loudness'],
            "acousticness": track["acousticness"],
        }
        for track in p.json()["audio_features"]]
    )
        

def get_date(album: dict) -> datetime:
    """
    Extract the release date for a track from the album data
    """
    date_format = {"day": "%Y-%m-%d",
               "month": "%Y-%m",
               "year": "%Y"}
    date_string = album["release_date"]
    date_fmt  = date_format[album["release_date_precision"]]
    return datetime.strptime(date_string, date_fmt)
    

def get_spotify_data(music_league_df: pd.DataFrame) -> pd.DataFrame:
    track_data = get_tracks_individual(music_league_df.song_id)
    feature_data = get_features_individual(music_league_df.song_id)
    genres = get_genres(track_data.artist_ids)
    track_data["genres"] = genres
    return pd.concat((music_league_df.set_index(np.arange(len(music_league_df))), track_data, feature_data), axis=1)