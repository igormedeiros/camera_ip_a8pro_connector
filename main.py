import vlc
import time
import logging
import os
from dotenv import load_dotenv
import msvcrt  # Para Windows

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config():
    """Carrega configurações do .env"""
    load_dotenv()
    
    required_vars = [
        'CAMERA_IP',
        'CAMERA_USERNAME',
        'CAMERA_PASSWORD',
        'CAMERA_PORT',
        'CAMERA_PATH'
    ]
    
    # Verifica se todas as variáveis necessárias existem
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Faltando variáveis no .env: {', '.join(missing)}")
        
    # Monta URL RTSP
    rtsp_url = f"rtsp://{os.getenv('CAMERA_USERNAME')}:{os.getenv('CAMERA_PASSWORD')}@" \
               f"{os.getenv('CAMERA_IP')}:{os.getenv('CAMERA_PORT')}{os.getenv('CAMERA_PATH')}"
               
    return rtsp_url

def play_stream(url):
    """Reproduz stream RTSP"""
    try:
        # Cria instância do VLC
        instance = vlc.Instance()
        logging.info("VLC instance criada")
        
        # Cria o media player
        player = instance.media_player_new()
        logging.info("Player criado")
        
        # Cria o objeto media com a URL RTSP
        media = instance.media_new(url)
        logging.info("Media criada")
        
        # Define o media no player
        player.set_media(media)
        logging.info("Media definida no player")
        
        # Inicia a reprodução
        player.play()
        logging.info("Play iniciado")
        
        # Aguarda um pouco para o stream iniciar
        time.sleep(2)
        
        print("\nPressione 'q' para sair...")
        
        while True:
            # Mostra estado do player
            state = str(player.get_state())
            playing = player.is_playing()
            fps = player.get_fps()
            time_ms = player.get_time()
            
            # Atualiza status na mesma linha
            print(f"\rEstado: {state}, Playing: {playing}, FPS: {fps:.2f}, Time: {time_ms}ms", end='')
            
            # Verifica se 'q' foi pressionado
            if msvcrt.kbhit():
                if msvcrt.getch() == b'q':
                    print("\nEncerrando...")
                    break
            
            time.sleep(0.1)  # Pequeno delay
            
    except Exception as e:
        logging.error(f"Erro: {e}")
    finally:
        # Limpa recursos
        if 'player' in locals():
            player.stop()
        if 'instance' in locals():
            instance.release()
        logging.info("Recursos liberados")

def main():
    try:
        # Carrega configuração
        url = load_config()
        logging.info(f"URL RTSP: {url}")
        
        # Inicia stream
        play_stream(url)
        
    except Exception as e:
        logging.error(f"Erro: {e}")
        
if __name__ == "__main__":
    main()