import datetime
import json
import random
import time
from typing import List, Optional
from app.episode_downloader import EpisodeDownloader
from pygame import mixer
from config import DIRECTORY, is_on_bean_machine


if is_on_bean_machine():
    from RPLCD.i2c import CharLCD
else:
    class CharLCD:
        def __init__(self, **kwargs):
            pass

        def clear(self):
            pass

        def write_string(self, string_to_write: str):
            print('FAKE DISPLAY', string_to_write)


class Episode:
    def __init__(self, **kwargs):
        self.episode_name: str = kwargs.get('episode_name')
        self.file_name: str = kwargs.get('file_name')
        self.publish_date: datetime = kwargs.get('publish_date')
        self.duration: int = kwargs.get('duration')

    @staticmethod
    def load_from_json():
        episode_json = json.load(open(DIRECTORY + '/episodes.json'))
        return [Episode(**x) for x in episode_json]


class EpisodePlayer:

    def __init__(self, episode: Episode):
        self.episode = episode
        self.setup_mixer()

    def setup_mixer(self):
        mixer.init()
        if self.is_playing():
            self.stop()
        mixer.music.load(DIRECTORY + '/' + self.episode.file_name)

    @staticmethod
    def play():
        mixer.music.play()

    @staticmethod
    def stop():
        mixer.music.stop()
        mixer.music.unload()

    @staticmethod
    def is_playing():
        return mixer.music.get_busy()

    @staticmethod
    def get_position():
        return mixer.music.get_pos()


class BeanDisplay:

    def __init__(self):
        self.is_playing: bool = False
        self.playing_episode: Episode = Optional[None]
        self.lcd: CharLCD = CharLCD(
            i2c_expander='PCF8574',
            address=0x27,
            port=1,
            cols=20,
            rows=4,
            dotsize=8
        )
        self.lines: list = ['', '', '', '']
        self.seconds_played: int = 0
        self.setup()

    def setup(self):
        self.lcd.clear()
        self.lines[0] = '--THE BEAN MACHINE--'
        self.set_display()

    def set_playing_episode(self, episode: Optional[Episode]):
        self.playing_episode = episode
        if episode is None:
            return
        self.lines[1] = 'EPISODE: %s' % episode.episode_name
        self.set_display()

    def set_display(self):
        for i, line_text in enumerate(self.lines):
            self.lcd.cursor_pos = (i, 0)
            self.lcd.write_string(line_text)

    def set_is_playing(self, is_playing: bool):
        if self.is_playing and is_playing:
            return
        elif not self.is_playing and is_playing:
            #   Turn on light.
            return
        elif self.is_playing and not is_playing:
            #   Episode has concluded.
            #   Turn off playing light.
            self.is_playing = False
            #   Clear the episode.
            self.set_playing_episode(None)

    def tick(self, total_ticks: int):
        self.seconds_played = total_ticks
        self.lines[3] = '%s / %s' % (
            datetime.timedelta(seconds=total_ticks), datetime.timedelta(seconds=self.playing_episode.duration)
        )
        self.set_display()


class BeanMachine:

    def __init__(self):
        self.episodes:List[Episode] = []
        self.bean_display: BeanDisplay = BeanDisplay()
        self.setup()

    def setup(self):
        self.set_episodes()

    def set_episodes(self):
        self.episodes = Episode.load_from_json()

    def get_episode(self) -> Episode:
        episode_number = random.randint(0, len(self.episodes))
        return self.episodes[episode_number]

    def play_episode(self):
        #   Get the episode.
        episode_to_play = self.get_episode()

        #   Give to the display
        self.bean_display.set_playing_episode(episode_to_play)

        #   Give to the episode player.
        episode_player = EpisodePlayer(episode_to_play)
        episode_player.play()

        loop_count = 0
        while True:
            is_playing = episode_player.is_playing()
            self.bean_display.tick(total_ticks=loop_count)
            if not is_playing:
                break
            loop_count += 1
            time.sleep(1)


if __name__ == '__main__':
    BeanMachine().play_episode()