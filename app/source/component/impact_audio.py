"""Short projectile impacts with bounded polyphony and live master volume."""
from array import array
import math
import random

import pygame as pg
from .. import constants as c


class ImpactAudio:
    CHANNEL_COUNT = 4
    MIN_GAP_MS = 55
    _banks = {}

    def __init__(self):
        self.channels = []
        self.gains = []
        self.last_play = None
        self.variant = 0
        self.bank = {}
        settings = pg.mixer.get_init()
        if settings is None:
            return
        pg.mixer.set_reserved(self.CHANNEL_COUNT + 1)  # Channel 4 belongs to Dave.
        self.channels = [pg.mixer.Channel(i) for i in range(self.CHANNEL_COUNT)]
        for channel in self.channels:
            channel.stop()
        self.gains = [(0, 0)] * len(self.channels)
        if settings not in self._banks:
            # Private copies avoid multiplying the global sound volume twice.
            bank = {
                'pea': [pg.mixer.Sound(buffer=c.SOUND_BULLET_EXPLODE.get_raw())],
                'fire': [pg.mixer.Sound(buffer=c.SOUND_FIREPEA_EXPLODE.get_raw())],
            }
            rate, sample_format, channels = settings
            bank['homing'] = []
            if sample_format == -16:
                for variant in range(3):
                    rng = random.Random(831 + variant)
                    samples = array('h')
                    duration = .13
                    for i in range(round(rate * duration)):
                        t = i / rate
                        env = min(1, t / .002) * (1 - t / duration) ** 3
                        # Soft low thump + crisp transient + a faint sci-fi chirp.
                        phase = math.tau * ((190 + variant * 12) * t - 420 * t * t)
                        thump = math.sin(phase) * .56
                        snap = rng.uniform(-1, 1) * math.exp(-t * 80) * .32
                        chirp = math.sin(math.tau * (980 * t - 1800 * t * t)) * .10
                        value = round(24000 * env * (thump + snap + chirp))
                        samples.extend([value] * channels)
                    bank['homing'].append(pg.mixer.Sound(buffer=samples.tobytes()))
            else:
                bank['homing'] = bank['pea']
            self._banks[settings] = bank
        self.bank = self._banks[settings]

    def set_volume(self, volume):
        volume = max(0, min(1, volume))
        for channel, (left, right) in zip(self.channels, self.gains):
            if volume == 0:
                channel.set_volume(0)
            else:
                channel.set_volume(left * volume, right * volume)

    def play(self, kind, x, volume, now=None):
        if not self.channels or volume <= 0:
            return False
        now = pg.time.get_ticks() if now is None else now
        if self.last_play is not None and 0 <= now - self.last_play < self.MIN_GAP_MS:
            return False
        index = next((i for i, ch in enumerate(self.channels) if not ch.get_busy()), None)
        if index is None:
            return False  # Never steal an active impact, voice, music, or UI sound.
        choices = self.bank[kind]
        sound = choices[self.variant % len(choices)]
        self.variant += 1
        pan = max(0, min(1, x / c.SCREEN_WIDTH))
        gain = .72 if kind == 'homing' else .65
        self.gains[index] = (gain * (1 - .30 * pan), gain * (.70 + .30 * pan))
        self.channels[index].play(sound)
        # Channel.play resets volume; apply the mix AFTER starting playback.
        self.set_volume(volume)
        self.last_play = now
        return True
