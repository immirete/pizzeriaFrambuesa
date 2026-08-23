# formulario_pedido.py
import random
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from config_pizzeria import FRASES_RELLENO, PROMPT_TELEFONO

# Diccionario global para monitorizar el estado inmutable de la llamada
datos_cliente = {
    "nombre": "",
    "tipo_entrega": "",
    "direccion": "NO REQUERIDA (Es para recoger en local)",
    "telefono": "NO REQUERIDO"
}

def _reproducir_fijo(ruta):
    try:
        data, fs = sf.read(ruta, dtype='float32')
        sd.play(data, fs)
        sd.wait()
    except: pass

def lanzar_relleno():
    print("⚡ [RELLENO EMITIDO DESDE CARPETA AL MILISEGUNDO]")
    idx = random.randint(0, len(FRASES_RELLENO) - 1)
    hilo = threading.Thread(target=_reproducir_fijo, args=(f"audios_fijos/relleno_{idx}.wav",))
    hilo.start()
    return hilo

def escuchar_microfono(stt_model):
    frecuencia, bloque_muestras, umbral_volumen, segundos_silencio_maximo = 16000, 8000, 0.015, 1.5
    bloques_silencio_necesarios = int(segundos_silencio_maximo / 0.5)
    bloques_silenciosos_consecutivos = 0
    
    print("\n🎤 [MICROFONO ABIERTO] Escuchando...")
    grabacion_completa, hablando = [], False
    
    while True:
        bloque = sd.rec(bloque_muestras, samplerate=frecuencia, channels=1, dtype='float32')
        sd.wait()
        volumen = np.sqrt(np.mean(bloque**2))
        if volumen > umbral_volumen:
            hablando = True
            bloques_silenciosos_consecutivos = 0
            grabacion_completa.append(bloque)
        else:
            if hablando:
                bloques_silenciosos_consecutivos += 1
                grabacion_completa.append(bloque)
                if bloques_silenciosos_consecutivos >= bloques_silencio_necesarios: break
            else:
                grabacion_completa.append(bloque)
                # Ajustado a 3 segundos de espera máxima para agilizar el feedback
                if len(grabacion_completa) > 6: break

    audio_data = np.concatenate(grabacion_completa).flatten()
    if len(audio_data) == 0 or np.max(np.abs(audio_data)) < umbral_volumen:
        return ""
        
    segments, _ = stt_model.transcribe(audio_data, beam_size=1, language="es")
    texto = "".join([segment.text for segment in segments]).strip()
    print(f"👤 Cliente: {texto}")
    return texto

def ejecutar_formulario_inicial(stt_model, ollama_client, hablar_func):
    """Cuestionario secuencial blindado controlado por Python"""
    
    # 1. Nombre del cliente
    print(f"\n🤖 Dora: Hola, buenas tardes...")
    _reproducir_fijo("audios_fijos/saludo_inicial.wav")
    
    while not datos_cliente["nombre"]:
        resp = escuchar_microfono(stt_model)
        if not resp: continue
        hilo = lanzar_relleno()
        palabras = resp.replace(".", "").split()
        if palabras:
            datos_cliente["nombre"] = palabras[-1].capitalize()
            hilo.join()
            hablar_func(f"Encantada de atenderte, {datos_cliente['nombre']}. ¿Tu pedido será para recoger en el local o para enviar a domicilio?")
        else:
            hilo.join()
            hablar_func("Disculpa, no te he oído bien el nombre. ¿Me lo repites?")

    # 2. Tipo de entrega (Recoger o Domicilio)
    while not datos_cliente["tipo_entrega"]:
        resp = escuchar_microfono(stt_model)
        if not resp: continue
        hilo = lanzar_relleno()
        resp_clean = resp.lower()
        
        if any(k in resp_clean for k in ["recoger", "local", "coger", "coche"]):
            datos_cliente["tipo_entrega"] = "recoger"
            hilo.join()
            hablar_func(f"Estupendo, {datos_cliente['nombre']}. Te lo dejamos preparado en la Calle Frambuesa número 4. ¿Qué pizzas o bebidas te pongo?")
        elif any(k in resp_clean for k in ["domicilio", "enviar", "casa", "reparto"]):
            datos_cliente["tipo_entrega"] = "domicilio"
            datos_cliente["direccion"] = ""
            datos_cliente["telefono"] = ""
            hilo.join()
            
            # Formulario de Reparto paso a paso
            # A) Dirección con filtro de vía sugerido por Iván
            while not datos_cliente["direccion"]:
                hablar_func(f"Perfecto {datos_cliente['nombre']}. Por favor, dime tu dirección exacta indicando si es Calle, Avenida o Pasaje.")
                datos_casa = escuchar_microfono(stt_model)
                if not datos_casa: continue
                hilo_dom = lanzar_relleno()
                
                vias_validas = ["calle", "avenida", "pasaje", "carretera", "vía", "piso", "plaza", "ronda"]
                if not any(via in datos_casa.lower() for via in vias_validas):
                    hilo_dom.join()
                    hablar_func("Disculpa, necesito que me especifiques si es una Calle, Avenida o Pasaje para el repartidor.")
                    continue
                
                resumen_dir = ollama_client.chat(model='qwen2.5:1.5b', messages=[
                    {'role': 'system', 'content': "Devuelve solo el tipo de vía, nombre y número de forma corta."},
                    {'role': 'user', 'content': datos_casa}
                ])['message']['content']
                datos_cliente["direccion"] = resumen_dir
                print(f"[DIRECCIÓN GUARDADA]: {datos_cliente['direccion']}")
                hilo_dom.join()

            # B) Teléfono de contacto
            while not datos_cliente["telefono"]:
                hablar_func(f"Dirección anotada, {datos_cliente['nombre']}. Ahora dime un número de teléfono móvil de contacto.")
                datos_tel = escuchar_microfono(stt_model)
                if not datos_tel: continue
                hilo_dom = lanzar_relleno()
                resumen_tel = ollama_client.chat(model='qwen2.5:1.5b', messages=[
                    {'role': 'system', 'content': "Extrae el teléfono. Devuelve solo los dígitos numéricos juntos."},
                    {'role': 'user', 'content': datos_tel}
                ])['message']['content']
                datos_cliente["telefono"] = resumen_tel
                print(f"[TELÉFONO GUARDADO]: {datos_cliente['telefono']}")
                hilo_dom.join()

            hablar_func(f"Todo listo, {datos_cliente['nombre']}. Apuntado para reparto. Ahora sí, ¿qué pizzas o bebidas deseas pedir?")
        else:
            hilo.join()
            hablar_func(f"Disculpa {datos_cliente['nombre']}, ¿confirmamos si es para recoger o a domicilio?")
            
    return datos_cliente
