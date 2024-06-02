import datetime
import json
import os
import re
import typing
import xml.etree.ElementTree as ET
from config import DIRECTORY
import requests


class EpisodeDownloader:
    RSS_URL = 'https://podcast.global.com/show/5234547/episodes/feed'
    NAMESPACES = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}


    def __init__(self):
        self.podcast_rss: typing.Optional[ET] = None
        self.podcast_title: str = ''
        self.podcast_episode_list: list = []

    @staticmethod
    def convert_string_to_snake_cased(string_to_convert: str):
        return re.sub('[^A-Za-z0-9]+', '_', string_to_convert.lower())

    @staticmethod
    def download_file(episode_file_name: str, url: str):
        r = requests.get(url, stream=True,)
        with open(DIRECTORY + '/' + episode_file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print('Downloaded', episode_file_name)

    @staticmethod
    def has_episode_been_downloaded(episode_file_name: str) -> bool:
        return os.path.exists(DIRECTORY + '/' + episode_file_name)

    def get_filename(self, episode_title: str, episode_number: str, publish_date: datetime):
        channel_title: str = self.convert_string_to_snake_cased(self.podcast_title)
        episode_title: str = self.convert_string_to_snake_cased(episode_title)
        file_name = '_'.join([
            episode_number,
            channel_title,
            episode_title,
            publish_date.strftime('%Y%m%d')
        ]) + '.mp3'

        return file_name

    def set_podcast_rss_data(self):
        podcast_data = requests.get(self.RSS_URL)
        if podcast_data.status_code != 200:
            return
        podcast_text = podcast_data.content
        self.podcast_rss = ET.fromstring(podcast_text)

    def process_podcast_episode(self, episode: ET, episode_number: int):
        episode_title: str = episode.find('title').text
        publish_date: datetime.datetime = datetime.datetime.strptime(episode.find('pubDate').text, '%a, %d %b %Y %H:%M:%S +%f')
        mp3_url: str = episode.find('enclosure').attrib.get('url')
        full_episode_number: str = '0' * (3 - len(str(episode_number))) +  str(episode_number)
        file_name: str = self.get_filename(episode_title, full_episode_number, publish_date)
        duration: int = int(episode.find('itunes:duration', self.NAMESPACES).text)
        self.podcast_episode_list.append({
            'episode_name': episode_title,
            'publish_date': publish_date,
            'file_name': file_name,
            'duration': duration
        })
        if self.has_episode_been_downloaded(file_name):
            return
        self.download_file(file_name, mp3_url)

    def process(self):
        self.set_podcast_rss_data()
        channel: ET = self.podcast_rss.find('channel')
        self.podcast_title = channel.find('title').text
        episode_count: int = len(channel.findall('item'))
        for i, episode in enumerate(channel.findall('item')):
            self.process_podcast_episode(episode, episode_number=(episode_count - i))
        json.dump(self.podcast_episode_list, open(DIRECTORY + '/episodes.json', 'w'), default=str)


EpisodeDownloader().process()