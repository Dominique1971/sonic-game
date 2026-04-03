"""Procedural sound generation using numpy – no external audio files."""
import numpy as np
import pygame
import math

SAMPLE_RATE = 44100


def _make_tone(freq, duration, wave='sine', volume=0.4, envelope=True):
    """Generate a mono int16 numpy array for a single tone."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if wave == 'sine':
        data = np.sin(2 * math.pi * freq * t)
    elif wave == 'square':
        data = np.sign(np.sin(2 * math.pi * freq * t))
    elif wave == 'sawtooth':
        data = 2 * (t * freq - np.floor(0.5 + t * freq))
    elif wave == 'triangle':
        data = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:
        data = np.sin(2 * math.pi * freq * t)

    if envelope and n > 0:
        env = np.ones(n)
        attack = min(int(0.01 * SAMPLE_RATE), n // 4)
        release = min(int(0.05 * SAMPLE_RATE), n // 2)
        if attack > 0:
            env[:attack] = np.linspace(0, 1, attack)
        if release > 0:
            env[-release:] = np.linspace(1, 0, release)
        data = data * env

    data = (data * volume * 32767).astype(np.int16)
    return data


def _mix(*arrays):
    """Mix multiple mono arrays together (same length)."""
    length = max(len(a) for a in arrays)
    out = np.zeros(length, dtype=np.float64)
    for a in arrays:
        out[:len(a)] += a.astype(np.float64)
    out = np.clip(out, -32767, 32767).astype(np.int16)
    return out


def _stereo(mono):
    """Convert mono int16 array to stereo (shape N×2)."""
    return np.column_stack([mono, mono])


def _build_sound(mono_array):
    """Create a pygame.Sound from a mono int16 array."""
    stereo = _stereo(mono_array)
    return pygame.sndarray.make_sound(stereo)


# ---------------------------------------------------------------------------
# SFX generators
# ---------------------------------------------------------------------------

def _sfx_jump():
    n = int(SAMPLE_RATE * 0.25)
    t = np.linspace(0, 0.25, n, endpoint=False)
    freq = 220 + 440 * (t / 0.25)
    data = np.sin(2 * math.pi * np.cumsum(freq) / SAMPLE_RATE)
    env = np.linspace(1, 0, n) ** 0.5
    return (data * env * 0.5 * 32767).astype(np.int16)


def _sfx_shoot_normal():
    return _make_tone(880, 0.08, 'square', 0.3)


def _sfx_shoot_spread():
    a = _make_tone(660, 0.08, 'square', 0.2)
    b = _make_tone(880, 0.08, 'square', 0.2)
    c = _make_tone(1100, 0.08, 'square', 0.2)
    return _mix(a, b, c)


def _sfx_shoot_bounce():
    return _make_tone(440, 0.1, 'triangle', 0.35)


def _sfx_shoot_homing():
    n = int(SAMPLE_RATE * 0.15)
    t = np.linspace(0, 0.15, n, endpoint=False)
    freq = 330 + 220 * np.sin(2 * math.pi * 8 * t)
    data = np.sin(2 * math.pi * np.cumsum(freq) / SAMPLE_RATE)
    env = np.linspace(1, 0, n)
    return (data * env * 0.4 * 32767).astype(np.int16)


def _sfx_shoot_laser():
    n = int(SAMPLE_RATE * 0.3)
    t = np.linspace(0, 0.3, n, endpoint=False)
    freq = 1800 - 1200 * (t / 0.3)
    data = np.sign(np.sin(2 * math.pi * np.cumsum(freq) / SAMPLE_RATE))
    env = np.exp(-t * 8)
    return (data * env * 0.4 * 32767).astype(np.int16)


def _sfx_shoot_bomb():
    return _make_tone(110, 0.2, 'sawtooth', 0.4)


def _sfx_collect_gem():
    parts = []
    for freq in [523, 659, 784, 1047]:
        parts.append(_make_tone(freq, 0.07, 'sine', 0.3))
    total = int(SAMPLE_RATE * 0.28)
    out = np.zeros(total, dtype=np.int16)
    offset = 0
    step = int(SAMPLE_RATE * 0.07)
    for p in parts:
        end = min(offset + len(p), total)
        out[offset:end] = np.clip(out[offset:end].astype(np.int32) + p[:end-offset].astype(np.int32), -32767, 32767).astype(np.int16)
        offset += step
    return out


def _sfx_enemy_die():
    n = int(SAMPLE_RATE * 0.2)
    t = np.linspace(0, 0.2, n, endpoint=False)
    freq = 400 - 300 * (t / 0.2)
    data = np.sign(np.sin(2 * math.pi * np.cumsum(freq) / SAMPLE_RATE))
    env = np.exp(-t * 12)
    return (data * env * 0.4 * 32767).astype(np.int16)


def _sfx_player_hurt():
    n = int(SAMPLE_RATE * 0.3)
    t = np.linspace(0, 0.3, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n)
    freq = 200
    tone = np.sin(2 * math.pi * freq * t)
    data = 0.5 * noise + 0.5 * tone
    env = np.exp(-t * 6)
    return (data * env * 0.5 * 32767).astype(np.int16)


def _sfx_level_up():
    notes = [523, 659, 784, 1047, 1319]
    total = int(SAMPLE_RATE * 0.6)
    out = np.zeros(total, dtype=np.int32)
    step = int(SAMPLE_RATE * 0.1)
    for i, freq in enumerate(notes):
        tone = _make_tone(freq, 0.12, 'sine', 0.35)
        start = i * step
        end = min(start + len(tone), total)
        out[start:end] += tone[:end-start].astype(np.int32)
    return np.clip(out, -32767, 32767).astype(np.int16)


def _sfx_game_over():
    notes = [392, 349, 330, 262]
    total = int(SAMPLE_RATE * 1.2)
    out = np.zeros(total, dtype=np.int32)
    step = int(SAMPLE_RATE * 0.25)
    for i, freq in enumerate(notes):
        tone = _make_tone(freq, 0.3, 'sawtooth', 0.3)
        start = i * step
        end = min(start + len(tone), total)
        out[start:end] += tone[:end-start].astype(np.int32)
    return np.clip(out, -32767, 32767).astype(np.int16)


def _sfx_explosion():
    n = int(SAMPLE_RATE * 0.5)
    t = np.linspace(0, 0.5, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n)
    low = np.sin(2 * math.pi * 60 * t)
    data = 0.7 * noise + 0.3 * low
    env = np.exp(-t * 5)
    return (data * env * 0.6 * 32767).astype(np.int16)


# ---------------------------------------------------------------------------
# Music generators – short chiptune loops per theme
# ---------------------------------------------------------------------------

# Note frequencies (A4=440)
_NOTES = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'R':  0.0,
}

_THEME_MELODIES = {
    'meadow':     ['E5','E5','G5','E5','D5','C5','R','C5','D5','E5','G5','A5','G5','E5','R','R'],
    'forest':     ['A4','C5','E5','C5','A4','G4','F4','G4','A4','C5','E5','D5','C5','R','R','R'],
    'desert':     ['E4','G4','A4','G4','E4','D4','E4','R','G4','A4','B4','A4','G4','E4','D4','R'],
    'twilight':   ['D5','C5','B4','A4','G4','F4','G4','A4','B4','C5','D5','C5','B4','A4','R','R'],
    'ice':        ['C5','E5','G5','E5','C5','B4','C5','R','E5','G5','A5','G5','E5','D5','C5','R'],
    'underwater': ['F4','A4','C5','A4','F4','E4','F4','R','A4','C5','D5','C5','A4','G4','F4','R'],
    'volcano':    ['E4','E4','G4','E4','D4','E4','R','E4','F4','E4','D4','C4','D4','E4','R','R'],
    'sky':        ['G5','E5','C5','E5','G5','A5','G5','E5','D5','E5','G5','A5','B5','A5','G5','R'],
    'cave':       ['A4','G4','F4','E4','D4','E4','F4','G4','A4','B4','C5','B4','A4','G4','F4','R'],
    'castle':     ['E4','D4','C4','D4','E4','F4','G4','A4','B4','A4','G4','F4','E4','D4','C4','R'],
}

_NOTE_DUR = 0.12  # seconds per note


def _build_music_loop(theme):
    melody = _THEME_MELODIES.get(theme, _THEME_MELODIES['meadow'])
    note_samples = int(SAMPLE_RATE * _NOTE_DUR)
    total = note_samples * len(melody)
    out = np.zeros(total, dtype=np.int32)

    for i, name in enumerate(melody):
        freq = _NOTES.get(name, 0)
        start = i * note_samples
        if freq > 0:
            t = np.linspace(0, _NOTE_DUR, note_samples, endpoint=False)
            wave = np.sign(np.sin(2 * math.pi * freq * t))  # square for chiptune feel
            # add sub-octave for richness
            wave += 0.3 * np.sin(2 * math.pi * (freq / 2) * t)
            env = np.ones(note_samples)
            env[-int(note_samples * 0.15):] = np.linspace(1, 0, int(note_samples * 0.15))
            wave = wave * env
            out[start:start + note_samples] += (wave * 0.2 * 32767).astype(np.int32)

    return np.clip(out, -32767, 32767).astype(np.int16)


# ---------------------------------------------------------------------------
# SoundManager
# ---------------------------------------------------------------------------

class SoundManager:
    def __init__(self):
        self._sfx = {}
        self._music = {}
        self._music_channel = None
        self._current_theme = None
        self._enabled = True
        self._load_all()

    def _load_all(self):
        defs = {
            'jump':          _sfx_jump,
            'shoot_normal':  _sfx_shoot_normal,
            'shoot_spread':  _sfx_shoot_spread,
            'shoot_bounce':  _sfx_shoot_bounce,
            'shoot_homing':  _sfx_shoot_homing,
            'shoot_laser':   _sfx_shoot_laser,
            'shoot_bomb':    _sfx_shoot_bomb,
            'collect_gem':   _sfx_collect_gem,
            'enemy_die':     _sfx_enemy_die,
            'player_hurt':   _sfx_player_hurt,
            'level_up':      _sfx_level_up,
            'game_over':     _sfx_game_over,
            'explosion':     _sfx_explosion,
        }
        for name, fn in defs.items():
            try:
                mono = fn()
                self._sfx[name] = _build_sound(mono)
            except Exception:
                pass

        for theme in _THEME_MELODIES:
            try:
                mono = _build_music_loop(theme)
                snd = _build_sound(mono)
                self._music[theme] = snd
            except Exception:
                pass

    def play(self, name):
        if not self._enabled:
            return
        snd = self._sfx.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_music(self, theme):
        if not self._enabled:
            return
        if theme == self._current_theme:
            return
        self._current_theme = theme
        if self._music_channel and self._music_channel.get_busy():
            self._music_channel.stop()
        snd = self._music.get(theme, self._music.get('meadow'))
        if snd:
            try:
                if self._music_channel is None:
                    self._music_channel = pygame.mixer.find_channel(True)
                if self._music_channel:
                    self._music_channel.play(snd, loops=-1)
            except Exception:
                pass

    def stop_music(self):
        if self._music_channel:
            try:
                self._music_channel.stop()
            except Exception:
                pass
        self._current_theme = None

    def toggle(self):
        self._enabled = not self._enabled
        if not self._enabled:
            self.stop_music()
