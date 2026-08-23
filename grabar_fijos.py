import os
import torch
import numpy as np
import soundfile as sf
from kokoro import KPipeline
from config_pizzeria import FRASES_RELLENO, RUTA_VOZ_LOCAL, NOMBRE_PIZZERIA

print("📦 Creando carpeta de audios locales...")
os.makedirs("audios_fijos", exist_ok=True)

print("🔄 Cargando Kokoro para la grabación única...")
pipeline = KPipeline(lang_code='e', repo_id=None)
pack = torch.load(RUTA_VOZ_LOCAL, map_location='cpu')
silencio_hardware = np.zeros(9600, dtype=np.float32)

# 1. Grabar el saludo inicial largo
print("🎙️ Grabando saludo inicial...")
saludo_texto = f"Hola, buenas tardes. Bienvenido a {NOMBRE_PIZZERIA}. ¿Con quién tengo el gusto de hablar?"
gen = pipeline(saludo_texto, voice=pack, speed=1.1)
_, _, audio = next(gen)
audio_listo = np.concatenate([silencio_hardware, audio])
sf.write("audios_fijos/saludo_inicial.wav", audio_listo, 24000)

# 2. Grabar las frases de relleno
for i, frase in enumerate(FRASES_RELLENO):
    print(f"🎙️ Grabando frase de relleno {i}: '{frase}'")
    gen = pipeline(frase, voice=pack, speed=1.1)
    _, _, audio = next(gen)
    audio_listo = np.concatenate([silencio_hardware, audio])
    sf.write(f"audios_fijos/relleno_{i}.wav", audio_listo, 24000)

print("\n✅ ¡Éxito! Todos los audios fijos se han guardado en la carpeta 'audios_fijos/'.")
