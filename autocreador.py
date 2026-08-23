# autocreador.py
import os
import torch
import numpy as np
import soundfile as sf
import urllib.request
from config_pizzeria import FRASES_RELLENO, RUTA_VOZ_LOCAL, NOMBRE_PIZZERIA

# URL oficial de Hugging Face para el archivo real de voces
URL_DORA_HF = "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/ef_dora.pt?download=true"

def verificar_y_reparar_entorno(tts_pipeline=None):
    """Comprueba el disco duro. Descarga y genera lo que falte automáticamente"""
    print("🔍 [SISTEMA] Verificando dependencias de hardware locales...")

    # 1. Comprobar si falta el archivo de voz .pt
    if not os.path.exists(RUTA_VOZ_LOCAL):
        print(f"📥 Archivo '{RUTA_VOZ_LOCAL}' no encontrado.")
        print("⏳ Descargando los pesos de voz de Dora desde Hugging Face (28 MB)...")
        try:
            urllib.request.urlretrieve(URL_DORA_HF, RUTA_VOZ_LOCAL)
            print("✅ Voz descargada con éxito.")
        except Exception as e:
            print(f"❌ Error crítico al descargar la voz: {e}")
            exit(1)

    # 2. Si no se pasa la tubería de Kokoro (primer chequeo), salimos
    if tts_pipeline is None:
        return

    # 3. Comprobar si falta la carpeta o los audios .wav de relleno
    os.makedirs("audios_fijos", exist_ok=True)
    archivos_relleno_faltan = not all(os.path.exists(f"audios_fijos/relleno_{i}.wav") for i in range(len(FRASES_RELLENO)))
    saludo_falta = not os.path.exists("audios_fijos/saludo_inicial.wav")

    if archivos_relleno_faltan or saludo_falta:
        print("🎙️ Detectados audios fijos faltantes. Generando caché de audio local...")
        pack = torch.load(RUTA_VOZ_LOCAL, map_location='cpu')
        silencio_hardware = np.zeros(9600, dtype=np.float32)
        
        # Grabar saludo inicial
        if saludo_falta:
            print(" -> Grabando saludo inicial...")
            saludo_texto = f"Hola, buenas tardes. Bienvenido a {NOMBRE_PIZZERIA}. ¿Con quién tengo el gusto de hablar?"
            gen = tts_pipeline(saludo_texto, voice=pack, speed=1.1)
            _, _, audio = next(gen)
            sf.write("audios_fijos/saludo_inicial.wav", np.concatenate([silencio_hardware, audio]), 24000)
            
        # Grabar lista de frases de relleno
        for i, frase in enumerate(FRASES_RELLENO):
            ruta_w = f"audios_fijos/relleno_{i}.wav"
            if not os.path.exists(ruta_w):
                print(f" -> Grabando frase de relleno {i}: '{frase}'")
                gen = tts_pipeline(frase, voice=pack, speed=1.1)
                _, _, audio = next(gen)
                sf.write(ruta_w, np.concatenate([silencio_hardware, audio]), 24000)
                
        print("✅ Todos los audios fijos se han cocinado en 'audios_fijos/'.")
