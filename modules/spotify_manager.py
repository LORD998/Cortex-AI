import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class SpotifyManager:
    def __init__(self):
        self.client_id = "90c54e89d6984ffca6e3f81fb2d2bca7"
        self.client_secret = "bd07827abdf442b4accf05ee362e9218"
        self.redirect_uri = "http://localhost:8080"
        self.scope = "user-read-playback-state user-modify-playback-state user-top-read playlist-modify-private playlist-modify-public"
        self.sp = None
        self._authenticate()

    def _authenticate(self):
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.sp.current_playback()
        except Exception as e:
            print(f"Erro na autenticação do Spotify: {e}")
            self.sp = None

    def play_track(self, track_name: str):
        if not self.sp:
            return "Erro: O Spotify não está autenticado."
        
        try:
            results = self.sp.search(q=track_name, type='track', limit=1)
            tracks = results['tracks']['items']
            if not tracks:
                return f"Não encontrei a música '{track_name}' no Spotify."
            
            track_uri = tracks[0]['uri']
            track_title = tracks[0]['name']
            artist_name = tracks[0]['artists'][0]['name']
            
            devices = self.sp.devices()
            if not devices or not devices['devices']:
                return "Não tens nenhum dispositivo ativo no Spotify. Abre a app primeiro e põe a tocar algo."
                
            active_device = None
            for d in devices['devices']:
                if d['is_active']:
                    active_device = d['id']
                    break
            
            if not active_device:
                active_device = devices['devices'][0]['id']

            self.sp.start_playback(device_id=active_device, uris=[track_uri])
            return f"A tocar '{track_title}' de {artist_name} no Spotify!"
        except spotipy.exceptions.SpotifyException as e:
            return f"Erro do Spotify: {e.msg}. Talvez precises de ter a app aberta."
        except Exception as e:
            return f"Erro ao tentar tocar a música: {str(e)}"

    def pause_playback(self):
        if not self.sp: return "Spotify não autenticado."
        try:
            self.sp.pause_playback()
            return "O Spotify foi pausado."
        except Exception as e:
            return f"Erro ao pausar: {str(e)}"
            
    def next_track(self):
        if not self.sp: return "Spotify não autenticado."
        try:
            self.sp.next_track()
            return "Passei para a próxima música no Spotify."
        except Exception as e:
            return f"Erro ao passar música: {str(e)}"

    def current_track(self):
        if not self.sp: return "Spotify não autenticado."
        try:
            playback = self.sp.current_playback()
            if playback and playback['is_playing']:
                item = playback['item']
                return f"Estás a ouvir '{item['name']}' de {item['artists'][0]['name']}."
            return "Nenhuma música está a tocar no momento."
        except Exception as e:
            return f"Erro ao ler música: {str(e)}"

    def create_top_tracks_playlist(self):
        if not self.sp: return "Spotify não autenticado."
        try:
            user_id = self.sp.current_user()['id']
            
            # Buscar as 20 músicas mais ouvidas (long term)
            top_tracks = self.sp.current_user_top_tracks(limit=20, time_range='long_term')
            if not top_tracks or not top_tracks['items']:
                return "Não consegui encontrar músicas suficientes no teu histórico para criar uma playlist."
            
            track_uris = [track['uri'] for track in top_tracks['items']]
            
            # Criar playlist nova
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name="Favoritas da Cortex 🧠",
                public=False,
                description="Playlist gerada automaticamente pela Cortex com as tuas músicas mais ouvidas."
            )
            
            # Adicionar as músicas
            self.sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
            
            return f"Sucesso! Criei a playlist '{playlist['name']}' no teu Spotify com as tuas {len(track_uris)} músicas mais ouvidas."
        except spotipy.exceptions.SpotifyException as e:
            return f"Erro do Spotify ao criar playlist: {e.msg}. Pode ser necessário refazer o login para aceitar novas permissões."
        except Exception as e:
            return f"Erro inesperado ao criar playlist: {str(e)}"
