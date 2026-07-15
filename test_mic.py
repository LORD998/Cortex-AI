import soundcard as sc
import numpy as np

m = sc.default_microphone()
print('Mic:', m.name)
with m.recorder(samplerate=16000, channels=1) as mic:
    data = mic.record(numframes=16000)
    rms = np.sqrt(np.mean((data * 32767).astype(np.float32)**2))
    print('RMS:', rms)
