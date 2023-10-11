# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import os
# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

import rasa_sdk
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import pylast


class ActionHelloWorld(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        key = os.getenv('API_KEY')
        secret = os.getenv('SECRET')
        username = os.getenv('username')
        password_hash = pylast.md5(text=os.getenv('password'))
        if key is None or secret is None or username is None or password_hash == pylast.md5(text=None):
            raise('some environment variable is missing')
        self.network = pylast.LastFMNetwork(
            password_hash=password_hash,
            username=username,
            api_key=key,
            api_secret=secret
        )

    def name(self) -> Text:
        return "action_best_songs"

    def __best_songs(self, band_name: str, amount=5) -> List[str]:
        raw_tracks = self.network.get_artist(artist_name=band_name).get_top_tracks(limit=amount)
        return [track.item.get_name() for track in raw_tracks]
        pass

    def __format_songs(self, songs: List[str]) -> str:
        ans = "I suggest these:\n"
        for i, song in enumerate(songs):
            ans += f"{i}: {song}\n"  # todo: more beautiful
        return ans

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        band_name = tracker.get_slot('band')
        if band_name is None:
            dispatcher.utter_message(
                text='Don\'t know the band. Please clarify, what band\'s songs I should search for')
            return []
        songs = self.__best_songs(band_name=band_name, amount=6)
        print(songs)
        msg = self.__format_songs(songs=songs)
        print(msg)
        dispatcher.utter_message(text=msg)
        return []
