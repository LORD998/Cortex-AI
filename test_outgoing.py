import sounddevice as sd
import speech_recognition as sr
from deep_translator import GoogleTranslator
import numpy as np
import io
import wave
import asyncio
import edge_tts
import soundfile as sf

print("Finding mic...")
mic_idx = None
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0 and 'CABLE' not in d['name'] and 'Mistura' not in d['name'] and 'Stereo' not in d['name']:
        mic_idx = i
        break
print(f"Using Mic Idx: {mic_idx} -> {sd.query_devices()[mic_idx]['name']}")

cable_out_idx = None
for i, d in enumerate(sd.query_devices()):
    if 'CABLE Input' in d['name'] and d['max_output_channels'] > 0:
        cable_out_idx = i
        break
print(f"Cable Out Idx: {cable_out_idx}")

recognizer = sr.Recognizer()
translator = GoogleTranslator(source='pt', target='ru')

fs = 16000
chunk_duration = 3

async def generate(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

print("Listening for 3 seconds... FALE AGORA OLA!")
data = sd.rec(int(chunk_duration * fs), samplerate=fs, channels=1, dtype='int16', device=mic_idx)
sd.wait()

rms = np.sqrt(np.mean(data.astype(np.float32)**2))
print(f"RMS: {rms}")

if rms < 50:
    print("Silence detected.")
else:
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(data.tobytes())
    wav_io.seek(0)
    
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)
        
    print("Recognizing...")
    try:
        texto = recognizer.recognize_google(audio_data, language="pt-PT")
        print(f"Recognized: {texto}")
        traducao = translator.translate(texto)
        print(f"Translated: {traducao}")
        
        print("Generating TTS...")
        audio_bytes = asyncio.run(generate(traducao, "ru-RU-SvetlanaNeural"))
        print("Playing TTS...")
        data_tts, fs_tts = sf.read(io.BytesIO(audio_bytes))
        sd.play(data_tts, fs_tts, device=cable_out_idx)
        sd.wait()
        print("Done playing!")
    except Exception as e:
        print(f"Error: {e}")
