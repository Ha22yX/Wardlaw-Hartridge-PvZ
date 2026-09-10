"""Short, original cartoon mumble syllables synchronized to Dave's typewriter."""
from array import array
import math
import pygame as pg


class DaveVoice:
    _banks = {}

    def __init__(self):
        self.channel = None
        self.last = -1000
        self.variant = 0
        settings = pg.mixer.get_init()
        if not settings or settings[1] != -16:
            self.sounds = []
            return
        pg.mixer.set_num_channels(max(8, pg.mixer.get_num_channels()))
        pg.mixer.set_reserved(5)  # 0–3 impacts; 4 dialogue, never steal effects.
        self.channel = pg.mixer.Channel(4)
        self.channel.stop()
        if settings not in self._banks:
            rate, _, channels = settings
            bank = []
            for variant in range(5):
                samples = array('h')
                duration = .16 + variant * .012
                formants = ((550, 1250), (420, 1750), (700, 1100),
                            (340, 900), (600, 1500))[variant]
                for i in range(round(rate * duration)):
                    t = i / rate
                    pitch = 105 + variant * 17
                    phase = math.tau * (pitch * t + 30 * t * t)
                    value = 0
                    for harmonic in range(1, 15):
                        hz = harmonic * pitch
                        gain = .08 / harmonic + sum(math.exp(-((hz - f) / 220) ** 2) for f in formants) * .15
                        value += gain * math.sin(phase * harmonic)
                    envelope = min(1, t / .012) * max(0, 1 - t / duration) ** .7
                    sample = round(14000 * envelope * value)
                    samples.extend([max(-32767, min(32767, sample))] * channels)
                bank.append(pg.mixer.Sound(buffer=samples.tobytes()))
            self._banks[settings] = bank
        self.sounds = self._banks[settings]

    def update(self, now, speaking, volume):
        if not self.channel:
            return
        if not speaking or volume <= 0:
            self.stop()
            return
        self.channel.set_volume(.48 * max(0, min(1, volume)))
        if now - self.last >= 210 and not self.channel.get_busy():
            self.channel.play(self.sounds[self.variant % len(self.sounds)])
            self.channel.set_volume(.48 * max(0, min(1, volume)))
            self.variant += 1
            self.last = now

    def stop(self):
        if self.channel:
            self.channel.stop()
