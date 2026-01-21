import pygame
import numpy as np

class SoundManager:
    def __init__(self, sample_rate=44100):
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
        self.sample_rate = sample_rate
        
        # Pre-generate sounds
        self.sounds = {
            'beat': self._generate_wave(440.0, 0.1, 'sine'),
            'move': self._generate_wave(200.0, 0.05, 'square', decay=True),
            'rotate': self._generate_wave(600.0, 0.05, 'square', decay=True),
            'drop': self._generate_wave(150.0, 0.1, 'sawtooth', decay=True),
            'clear': self._generate_wave(880.0, 0.2, 'sine', decay=True), # High ping
            'game_over': self._generate_noise(0.5)
        }
        
    def _generate_wave(self, freq, duration, type='sine', decay=True):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        if type == 'sine':
            wave = np.sin(freq * t * 2 * np.pi)
        elif type == 'square':
            wave = np.sign(np.sin(freq * t * 2 * np.pi))
        elif type == 'sawtooth':
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        else:
            wave = np.sin(freq * t * 2 * np.pi)
            
        if decay:
            envelope = np.linspace(1.0, 0.0, len(t))
            wave = wave * envelope
            
        audio = (wave * 32767 * 0.5).astype(np.int16) # 0.5 volume
        return pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def _generate_noise(self, duration):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        noise = np.random.uniform(-1, 1, len(t))
        envelope = np.linspace(1.0, 0.0, len(t))
        noise = noise * envelope
        audio = (noise * 32767 * 0.5).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()