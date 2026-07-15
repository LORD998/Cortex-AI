import soundcard as sc
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from deep_translator import GoogleTranslator
import threading
import numpy as np
import io
import wave
import asyncio
import edge_tts

class TranslatorManager:
    def __init__(self, ui_callback):
        self.recognizer = sr.Recognizer()
        self.translator_to_pt = GoogleTranslator(source='ru', target='pt')
        self.translator_to_ru = GoogleTranslator(source='pt', target='ru')
        self.ui_callback = ui_callback
        self.is_running = False
        self.thread_in = None
        self.thread_out = None
        self.tts_lock = threading.Lock()
        
        # Encontrar o índice do "CABLE Input"
        self.cable_out_idx = None
        for i, d in enumerate(sd.query_devices()):
            if 'CABLE Input' in d['name'] and d['max_output_channels'] > 0:
                self.cable_out_idx = i
                break

    def start_translating(self):
        if self.is_running: return
        self.is_running = True
        
        if self.cable_out_idx is not None:
            self.ui_callback("[Tradutor Duplo Ativado: Escutando você e a chamada...]")
        else:
            self.ui_callback("[Tradutor Ativado (AVISO: Cabo Virtual não encontrado!)]")
            
        self.thread_in = threading.Thread(target=self._listen_loop_incoming, daemon=True)
        self.thread_in.start()
        
    def stop_translating(self):
        self.is_running = False
        self.ui_callback("") 
        
    def _speak_to_device(self, text, voice, device_idx=None):
        async def generate():
            try:
                communicate = edge_tts.Communicate(text, voice)
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                return audio_bytes
            except Exception as e:
                print(f"EdgeTTS Error: {e}")
                return None
            
        try: loop = asyncio.get_running_loop()
        except RuntimeError: loop = None
        
        if loop and loop.is_running():
            audio_bytes = asyncio.run_coroutine_threadsafe(generate(), loop).result()
        else:
            audio_bytes = asyncio.run(generate())
            
        if audio_bytes:
            try:
                data, fs = sf.read(io.BytesIO(audio_bytes))
                with self.tts_lock:
                    self.is_playing_tts = True
                    sd.play(data, fs, device=device_idx)
                    sd.wait()
                    self.is_playing_tts = False
            except Exception as e:
                print(f"Erro ao tocar áudio no dispositivo {device_idx}: {e}")
            finally:
                self.is_playing_tts = False

    def _listen_loop_incoming(self):
        """Ouve o áudio do sistema (Loopback) de forma contínua -> Traduz p/ PT -> Atualiza UI"""
        try:
            mics = sc.all_microphones(include_loopback=True)
            default_speaker = sc.default_speaker()
            loopback_mic = next((m for m in mics if m.name == default_speaker.name), mics[0])
            
            fs = 16000
            
            with loopback_mic.recorder(samplerate=fs, channels=1) as mic:
                audio_buffer = []
                is_speaking = False
                silence_chunks = 0
                
                while self.is_running:
                    # Grava pacotes de 0.25 segundos
                    chunk = mic.record(numframes=int(fs * 0.25))
                    
                    if getattr(self, 'is_playing_tts', False):
                        is_speaking = False
                        audio_buffer = []
                        silence_chunks = 0
                        continue
                        
                    data = (chunk * 32767).astype(np.int16)
                    rms = np.sqrt(np.mean(data.astype(np.float32)**2))
                    
                    if not is_speaking:
                        if rms > 50:
                            is_speaking = True
                            audio_buffer = [data]
                            silence_chunks = 0
                    else:
                        audio_buffer.append(data)
                        if rms <= 50:
                            silence_chunks += 1
                        else:
                            silence_chunks = 0
                            
                        # Cortar o áudio super rápido: 0.5s de silêncio ou máximo de 4s
                        if silence_chunks > 2 or len(audio_buffer) > 16:
                            final_data = np.concatenate(audio_buffer, axis=0)
                            buffer_length = len(audio_buffer)
                            
                            is_speaking = False
                            audio_buffer = []
                            silence_chunks = 0
                            
                            if buffer_length > 2:
                                threading.Thread(target=self._process_incoming_audio, args=(final_data, fs), daemon=True).start()
                                
        except Exception as e:
            print(f"[Tradutor In Fatal Error] {e}")

    def _process_incoming_audio(self, data, fs):
        try:
            # Amplificar áudio para volume máximo (melhora muito o reconhecimento da Google)
            max_val = np.max(np.abs(data))
            if max_val > 0:
                data = (data.astype(np.float32) * (32767.0 / max_val)).astype(np.int16)
                
            wav_io = io.BytesIO()
            import wave
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(data.tobytes())
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)
                
            try:
                texto = self.recognizer.recognize_google(audio_data, language="ru-RU")
                if texto and "smile" not in texto.lower() and len(texto.strip()) > 2:
                    traducao = self.translator_to_pt.translate(texto)
                    if traducao and len(traducao.strip()) > 2:
                        self.ui_callback(f"🗣️: {traducao}")
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                self.ui_callback(f"⚠️ Erro de Conexão/Bloqueio (Erro 500). Desligue o som do jogo!")
                print(f"RequestError: {e}")
        except Exception as e:
            print(f"[Tradutor In Error] {e}")

    def _listen_loop_outgoing(self):
        """Ouve o seu microfone de forma contínua -> Traduz p/ Russo -> Fala no Cabo Virtual (Discord/Zoom)"""
        try:
            mic_idx = None
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0 and 'CABLE' not in d['name'] and 'Mistura' not in d['name'] and 'Stereo' not in d['name'] and 'Mapeador' not in d['name']:
                    mic_idx = i
                    break
                    
            fs = 16000
            import queue
            q = queue.Queue()
            
            def callback(indata, frames, time_info, status):
                if status:
                    print(status)
                q.put(indata.copy())
                
            with sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=mic_idx, blocksize=int(fs*0.25), callback=callback):
                audio_buffer = []
                is_speaking = False
                silence_chunks = 0
                
                while self.is_running:
                    chunk = q.get()
                    rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                    
                    if not is_speaking:
                        if rms > 150:  # Threshold aumentado para ignorar ruído de fundo/respiração
                            is_speaking = True
                            audio_buffer = [chunk]
                            silence_chunks = 0
                    else:
                        audio_buffer.append(chunk)
                        if rms <= 150:
                            silence_chunks += 1
                        else:
                            silence_chunks = 0
                            
                        # Se houver 1s de silêncio ou gravação exceder 10s
                        if silence_chunks > 4 or len(audio_buffer) > 40:
                            data = np.concatenate(audio_buffer, axis=0)
                            buffer_length = len(audio_buffer)
                            
                            # Reset VAD state
                            is_speaking = False
                            audio_buffer = []
                            silence_chunks = 0
                            
                            # Apenas processa se falou durante pelo menos 0.75 segundos (3 chunks)
                            # para evitar captar apenas "duas letras" ou ruídos
                            if buffer_length > 3:
                                threading.Thread(target=self._process_outgoing_audio, args=(data, fs), daemon=True).start()
                            
        except Exception as e:
            print(f"[Tradutor Out Fatal Error] {e}")

    def _process_outgoing_audio(self, data, fs):
        try:
            wav_io = io.BytesIO()
            import wave
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(data.tobytes())
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)
                
            texto = self.recognizer.recognize_google(audio_data, language="pt-BR")
            if texto and len(texto.strip()) > 2:
                traducao = self.translator_to_ru.translate(texto)
                if traducao and len(traducao.strip()) > 2:
                    self.ui_callback(f"👤 Eu: {traducao}")
                    self._speak_to_device(traducao, "ru-RU-SvetlanaNeural", self.cable_out_idx)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"[Tradutor Process Error] {e}")
