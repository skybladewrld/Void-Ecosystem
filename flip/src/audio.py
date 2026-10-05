"""Optional procedural audio that safely degrades on silent systems."""

from __future__ import annotations

from array import array
import math


class AudioManager:
    def __init__(self, pygame_module, master=0.65, ui=0.65, game=0.7):
        self.pygame = pygame_module
        self.available = False
        self.master, self.ui, self.game = master, ui, game
        self.sounds = {}
        try:
            if not pygame_module.mixer.get_init():
                pygame_module.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
            self.sounds = {name: self._tone(frequency, duration) for name, frequency, duration in (
                ("navigate", 330, .035), ("confirm", 520, .06), ("back", 240, .05),
                ("notification", 660, .08), ("important", 880, .12), ("game", 440, .045),
            )}
            self.available = True
        except (Exception,):
            self.available = False

    def _tone(self, frequency, duration):
        sample_rate = 22050
        count = int(sample_rate * duration)
        samples = array("h", (int(5000 * math.sin(2 * math.pi * frequency * i / sample_rate) * (1 - i / count)) for i in range(count)))
        return self.pygame.mixer.Sound(buffer=samples)

    def play(self, name: str, category="ui") -> None:
        if not self.available or name not in self.sounds or self.master <= 0:
            return
        volume = self.ui if category == "ui" else self.game
        self.sounds[name].set_volume(max(0.0, min(1.0, self.master * volume)))
        self.sounds[name].play()
