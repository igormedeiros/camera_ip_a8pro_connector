import cv2
import subprocess
import numpy as np
from ultralytics import YOLO
import os
from dotenv import load_dotenv
import time

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Carrega o modelo YOLO v8 nano - modelo mais leve e rápido da família YOLO
model = YOLO('yolov8n.pt')

# Configurações de vídeo
# Resolução SD (Standard Definition) - melhor performance vs qualidade
width, height = 720, 480  # Padrão NTSC (National Television System Committee)
transport = 'udp'  # UDP é mais rápido que TCP, melhor para streaming
fps = 10  # FPS (Frames por Segundo) - 10 é suficiente para detecção de objetos
frame_delay = 1/fps  # Calcula delay entre frames

# Carrega credenciais da câmera do arquivo .env
# Isso é uma boa prática de segurança para não expor senhas no código
user = os.getenv('CAMERA_USERNAME')
password = os.getenv('CAMERA_PASSWORD')
camera_ip = os.getenv('CAMERA_IP')
camera_port = os.getenv('CAMERA_PORT')
camera_path = os.getenv('CAMERA_PATH')

# Configuração do FFmpeg para captura do stream RTSP
# FFmpeg é usado por ser mais estável que OpenCV direto para RTSP
command = [
    'ffmpeg', '-rtsp_transport', f'{transport}',  # Protocolo de transporte 
    '-i', f'rtsp://{user}:{password}@{camera_ip}:{camera_port}/{camera_path}',  # URL da câmera
    '-vf', f'scale={width}:{height}',  # Redimensiona para SD
    '-vcodec', 'rawvideo',  # Formato de vídeo bruto
    '-pix_fmt', 'bgr24',    # Formato de pixel compatível com OpenCV
    '-f', 'rawvideo',       # Força saída em formato raw
    'pipe:1'                # Envia para pipe ao invés de arquivo
]

# Inicia o processo do FFmpeg em background
process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

# Controle de FPS
last_frame_time = time.time()

def check_human_detection(results):
    """Verifica se há humanos detectados nos resultados do YOLO"""
    for r in results:
        for c in r.boxes.cls:
            # Classe 0 no YOLO geralmente representa pessoas
            if int(c) == 0:  
                return True
    return False

def execute():
    """Função executada quando um humano é detectado"""
    print("🚨 Humano detectado! Executando ação...")
    # Adicione aqui as ações que deseja executar
    # Por exemplo: notificações, gravação, alarme, etc.

# Loop principal de processamento de frames
while True:
    current_time = time.time()
    elapsed = current_time - last_frame_time
    
    # Pula frame se não passou tempo suficiente
    if elapsed < frame_delay:
        continue

    # Lê um frame do pipe do FFmpeg
    raw_frame = process.stdout.read(width * height * 3)  # 3 canais (BGR)
    if len(raw_frame) != width * height * 3:
        break  # Sai se não conseguir ler o frame completo

    # Converte os bytes brutos para uma matriz numpy que o OpenCV entende
    frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))

    # Executa a detecção de objetos com YOLO
    results = model(frame)
    
    # Verifica se há humanos e executa ação
    if check_human_detection(results):
        execute()
        # Adiciona texto de alerta no frame
        cv2.putText(frame, "HUMANO DETECTADO!", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Desenha as caixas delimitadoras e labels no frame
    annotated_frame = results[0].plot()
    
    # Adiciona informação de FPS no frame
    real_fps = 1/elapsed
    cv2.putText(annotated_frame, f'FPS: {real_fps:.1f}', (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Mostra o frame com as detecções
    cv2.imshow("Detecção YOLO", annotated_frame)
    last_frame_time = current_time

    # Verifica se a tecla 'q' foi pressionada para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Limpa os recursos ao finalizar
process.stdout.close()
process.wait()
cv2.destroyAllWindows()