import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import uuid
import threading
import keyboard
import time
import io
import wave
import asyncio
import edge_tts
import re

class VoiceManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def listen(self):
        """Gravação Push-to-Talk: Grava APENAS enquanto a tecla ALT estiver premida.

        Devolve:
            None  -> nada a fazer (clique acidental, sem tentativa real de falar)
            ""    -> houve uma tentativa real de falar mas não foi possível perceber
            str   -> texto reconhecido com sucesso
        """
        print("[Microfone] A GRAVAR! (Pode falar... Solte o ALT quando terminar)")
        try:
            fs = 44100
            # Começa a gravar no máximo 30 segundos
            myrecording = sd.rec(int(30 * fs), samplerate=fs, channels=1, dtype='int16')

            # Espera que o utilizador solte o ALT
            start_time = time.time()
            while keyboard.is_pressed('alt'):
                time.sleep(0.01) # Polling 5x mais rápido para zero lag
                if time.time() - start_time > 29:
                    break

            # Pára a gravação IMEDIATAMENTE no exato milissegundo
            sd.stop()

            duracao_real = time.time() - start_time
            if duracao_real < 0.3:
                return None # Clique acidental, nem tentou falar

            audio_cortado = myrecording[:int(duracao_real * fs)]

            # Deteção de silêncio/volume demasiado baixo ANTES de gastar tempo com a API.
            # Isto separa "o microfone não está a captar som nenhum" de "o Google não percebeu a fala".
            pico = int(np.abs(audio_cortado).max()) if audio_cortado.size else 0
            if pico < 400:  # Escala int16 vai até 32767; abaixo disto é praticamente silêncio/ruído de fundo
                print(f"[Microfone] Áudio captado é praticamente silêncio (pico={pico}). Verifica o dispositivo/volume de entrada.")
                return ""

            # ========================================================
            # OTIMIZAÇÃO: 100% Memória RAM (sem gravações no disco rígido)
            # Isto acelera absurdamente a resposta do microfone
            # ========================================================
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(fs)
                wf.writeframes(audio_cortado.tobytes())
            wav_io.seek(0)

            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)

            print("[Microfone] A processar (RAM)...")
            # pt-PT reconhece melhor sotaque de Portugal, pt-BR para Brasil
            try:
                texto = self.recognizer.recognize_google(audio_data, language="pt-PT")
                print(f"[Ouvido] {texto}")
                return texto
            except sr.UnknownValueError:
                print("[Microfone] O Google não conseguiu perceber a fala (áudio percetível mas incompreensível).")
                return ""
            except sr.RequestError as e:
                print(f"[Microfone] Falha a contactar o serviço de reconhecimento (rede/API): {e}")
                return ""
        except Exception as e:
            print(f"Erro no microfone PTT: {type(e).__name__}: {e}")
            return ""

    def listen_continuous(self, duration=5):
        """Escuta contínua para o Modo Professora (em RAM)."""
        print(f"[Professora] A escutar ({duration}s)...")
        try:
            fs = 16000
            myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            
            # OTIMIZAÇÃO: RAM
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(myrecording.tobytes())
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)
                
            texto = self.recognizer.recognize_google(audio_data, language="pt-PT")
            print(f"[Aluno disse] {texto}")
            return texto
        except Exception as e:
            return ""

    def speak(self, text, callback=None, force_language=None):
        """Fala com latência hiper-reduzida usando streaming direto para a RAM."""
        if not text: 
            if callback: callback()
            return
            
        # Remover asteriscos e markdown
        text = text.replace('*', '').replace('#', '')
        
        vozes = {
            "pt": "pt-BR-ThalitaMultilingualNeural", # Mantida a voz hiper-profissional
            "en": "en-US-AriaNeural",        
            "ja": "ja-JP-NanamiNeural",      
            "de": "de-DE-KatjaNeural",       
            "ko": "ko-KR-SunHiNeural",       
            "es": "es-ES-ElviraNeural",      
            "fr": "fr-FR-DeniseNeural",      
            "it": "it-IT-ElsaNeural",        
            "zh": "zh-CN-XiaoxiaoNeural"
        }
        
        base_lang = "pt"
        if force_language:
            lang_map = {
                "inglês": "en", "ingles": "en", 
                "japonês": "ja", "japones": "ja", 
                "alemão": "de", "alemao": "de", 
                "coreano": "ko", "espanhol": "es", 
                "francês": "fr", "frances": "fr", 
                "italiano": "it", "mandarim": "zh"
            }
            base_lang = lang_map.get(force_language.lower(), "pt")
        else:
            try:
                from langdetect import detect
                detected = detect(text)
                if detected in vozes:
                    base_lang = detected
            except:
                pass

        chunks = [(base_lang, text)]
            
        # ========================================================
        # OTIMIZAÇÃO: Streaming do Áudio diretamente para Bytes (RAM)
        # Corta completamente o tempo de guardar MP3 no disco
        # ========================================================
        async def generate_chunk(lang, text_chunk):
            voz = vozes.get(lang, vozes["pt"])
            try:
                communicate = edge_tts.Communicate(text_chunk, voz)
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                return audio_bytes
            except Exception as e:
                print(f"Erro Edge-TTS streaming: {e}")
                return None

        async def generate_all():
            tasks = [generate_chunk(lang, text_chunk) for lang, text_chunk in chunks]
            return await asyncio.gather(*tasks)
            
        try: loop = asyncio.get_running_loop()
        except RuntimeError: loop = None

        if loop and loop.is_running():
            output_bytes_list = asyncio.run_coroutine_threadsafe(generate_all(), loop).result()
        else:
            output_bytes_list = asyncio.run(generate_all())
            
        output_bytes_list = [b for b in output_bytes_list if b]
        
        if not output_bytes_list:
            if callback: callback()
            return
        
        try:
            audio_data_list = []
            fs = None
            for b in output_bytes_list:
                try:
                    # Tenta ler o MP3 diretamente da RAM
                    data, fs_f = sf.read(io.BytesIO(b))
                    fs = fs_f
                    audio_data_list.append(data)
                except Exception:
                    # Fallback de segurança se o sistema não suportar stream decoding
                    temp_f = f"temp_fallback_{uuid.uuid4().hex}.mp3"
                    with open(temp_f, "wb") as f: f.write(b)
                    data, fs_f = sf.read(temp_f)
                    fs = fs_f
                    audio_data_list.append(data)
                    os.remove(temp_f)
                    
            if audio_data_list:
                combined_data = np.concatenate(audio_data_list)
                sd.play(combined_data, fs)
                sd.wait()
        except Exception as e:
            print(f"Erro reprodutor de RAM: {e}")
                
        if callback: 
            callback()
