# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import os
# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List, Tuple, Optional

import rasa_sdk
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import pycountry
import difflib
import pylast


def correct_if_misspelled(country: str) -> Optional[str]:
    common = common_uses.keys()
    match = difflib.get_close_matches(country.lower(), common)  # try to find in common uses
    if len(match) != 0:
        return common_uses[match[0]]
    country_names = [country.name.lower() for country in pycountry.countries]
    match = difflib.get_close_matches(country.lower(), country_names)
    if len(match) == 0:
        return None
    else:
        return match[0]


common_uses = {
    'russia': 'russian federation',
    'rf': 'russian federation',
    'usa': 'united states',
    'us': 'united states',
    'uk': 'united kingdom',
    'england': 'united kingdom',
    'gb': 'united kingdom',
    'britain': 'united kingdom'
}


class MissingEnvironmentVariable(Exception):
    pass


key = os.getenv('API_KEY')
secret = os.getenv('SECRET')
username = os.getenv('username')
password_hash = pylast.md5(text=os.getenv('password'))
if key is None or secret is None or username is None or password_hash == pylast.md5(text=None):
    raise MissingEnvironmentVariable('one of 4 is missing')
net = pylast.LastFMNetwork(
    password_hash=password_hash,
    username=username,
    api_key=key,
    api_secret=secret
)


class ActionBestSongs(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def __best_songs(self, band_name: str, amount=5) -> List[str]:
        raw_tracks = self.network.get_artist(artist_name=band_name).get_top_tracks(limit=amount)
        return [track.item.get_name() for track in raw_tracks]
        pass

    def __format_songs(self, songs: List[str]) -> str:  # todo: more beautiful
        ans = "I suggest these songs:\n"
        for i, song in enumerate(songs):
            ans += f"{i}: {song}\n"
        return ans

    def name(self) -> Text:
        return "action_best_songs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        band_name = tracker.get_slot('band')
        if band_name is None:
            dispatcher.utter_message(
                text='Don\'t know the band. Please clarify, what band\'s songs I should search for')
            return []
        songs = self.__best_songs(band_name=band_name, amount=6)
        msg = self.__format_songs(songs=songs)
        dispatcher.utter_message(text=msg)
        return []


class ActionSimilarArtists(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def name(self) -> Text:
        return "action_similar_bands"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        band_name = tracker.get_slot('band')
        if band_name is None:
            dispatcher.utter_message(
                text='Don\'t know the band. Please clarify, what band\'s songs I should search for')
            return []
        similar = self.__similar_bands(band_name=band_name, amount=6)
        msg = self.__format_bands(main_band=band_name, similar_bands=similar)
        dispatcher.utter_message(text=msg)
        return []

    def __similar_bands(self, band_name: str, amount: int) -> List[str]:
        return [artist.item.get_name() for artist in
                self.network.get_artist(artist_name=band_name).get_similar(limit=amount)]

    def __format_bands(self, main_band: str, similar_bands: List[str]) -> str:
        formatted = f"I think these ones are similar to {main_band}:\n"
        for i, similar_band in enumerate(similar_bands):
            formatted += f"{i}: {similar_band}\n"
        return formatted


class ActionArtistsTags(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def name(self) -> Text:
        return "action_bands_tags"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        band_name = tracker.get_slot('band')
        if band_name is None:
            dispatcher.utter_message(
                text='Don\'t know the band. Please clarify, what band\'s songs I should search for')
            return []
        tags = self.__tags(band_name=band_name, amount=6)
        msg = self.__format_tags(main_band=band_name, tags=tags)
        dispatcher.utter_message(text=msg)
        return []

    def __tags(self, band_name: str, amount: int) -> List[str]:
        return [tag.item.get_name() for tag in
                self.network.get_artist(artist_name=band_name).get_top_tags(limit=amount)]

    def __format_tags(self, main_band: str, tags: List[str]) -> str:
        formatted = f"The {main_band}\'s tags are:\n"
        for i, tag in enumerate(tags):
            formatted += f"{i}: {tag}\n"
        return formatted


class ActionBestAlbum(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def __best_album(self, band_name: str) -> List[str]:
        raw_album = self.network.get_artist(artist_name=band_name).get_top_albums(limit=1)
        return [album.item.get_name() for album in raw_album]
        pass

    def __format_album(self, album: str) -> str:  # todo: more beautiful
        ans = "I suggest this album:\n"
        ans += f"{album}\n"
        return ans

    def name(self) -> Text:
        return "action_best_album"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        band_name = tracker.get_slot('band')
        if band_name is None:
            dispatcher.utter_message(
                text='Don\'t know the band. Please clarify, what band\'s songs I should search for')
            return []
        album = self.__best_album(band_name=band_name)
        msg = self.__format_album(album=album[0])
        dispatcher.utter_message(text=msg)
        return []


class ActionCountryBestTracks(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def __best_songs(self, region: str) -> List[Tuple[str, str]]:
        print(f"region: {region}")
        raw_album = self.network.get_geo_top_tracks(country=region, limit=6)
        return [(album.item.get_name(), album.item.get_artist()) for album in raw_album]
        pass

    def __format_songs(self, country: str, songs: List[Tuple[str, str]]) -> str:  # todo: more beautiful
        ans = f"According to your country({country}), I suggest these tracks:\n"
        for i, (song, artist) in enumerate(songs):
            ans += f"{i}: \"{song}\" by {artist} \n"
        return ans

    def name(self) -> Text:
        return "action_country_best_songs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = tracker.get_slot('country')
        if country is None:
            dispatcher.utter_message(
                text='Couldnt find country in your speech. Try speaking clearly')
            return []
        verified_country = correct_if_misspelled(country=country)
        if country is None:
            dispatcher.utter_message(
                text=f'Non existent country provided: {country}')
            return []
        country = verified_country
        songs = self.__best_songs(region=country)
        msg = self.__format_songs(country=country, songs=songs)
        dispatcher.utter_message(text=msg)
        return []


class ActionCountryBestArtists(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def name(self) -> Text:
        return "action_country_best_band"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        country = tracker.get_slot('country')
        if country is None:
            dispatcher.utter_message(
                text='Couldnt find country in your speech. Try speaking clearly')
            return []
        verified_country = correct_if_misspelled(country=country)
        if country is None:
            dispatcher.utter_message(
                text=f'Non existent country provided: {country}')
            return []
        country = verified_country
        best = self.__best_band(country=country)
        msg = self.__format_band(country=country, best_band=best)
        dispatcher.utter_message(text=msg)
        return []

    def __best_band(self, country: str) -> str:
        print(f"country: {country}")
        return [artist.item.get_name() for artist in
                self.network.get_geo_top_artists(country=country, limit=1)][0]

    def __format_band(self, country: str, best_band: str) -> str:
        formatted = f"This band is the most popular in {country}: {best_band}\n"
        return formatted


class ActionTagBestAlbums(Action):
    network: pylast.LastFMNetwork

    def __init__(self):
        self.network = net

    def name(self) -> Text:
        return "action_tag_best_albums"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        tag = tracker.get_slot('tag')
        if tag is None:
            dispatcher.utter_message(
                text='Couldnt find tag in your speech. Try speaking clearly')
            return []
        best = self.__best_albums(tag=tag)
        msg = self.__format_albums(tag=tag, albums=best)
        dispatcher.utter_message(text=msg)
        return []

    def __best_albums(self, tag: str) -> List[Tuple[str, str]]:
        print(f"country: {tag}")
        return [(album.item.get_name(), album.item.get_artist()) for album in
                self.network.get_tag(name=tag).get_top_albums(limit=6)]

    def __format_albums(self, tag: str, albums: List[Tuple[str, str]]) -> str:
        formatted = f"This band is the most popular in {tag}:\n"
        for i, (album, artist) in enumerate(albums):
            formatted += f"{i}: \"{album}\" by {artist}\n"
        return formatted
