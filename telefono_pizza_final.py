# telefono_pizza_final.py
import os
import torch
import random
import numpy as np
import sounddevice as sd
import soundfile as sf
import ollama
from kokoro import KPipeline
from faster_whisper import WhisperModel
from config_pizzeria import PROMPT_TELEFONO, RUTA_VOZ_LOCAL, PRECIOS, FRASES_RELLENO
import formulario_pedido as form
# IMPORTAMOS EL ESCUDO AUTOMÁTICO DE ENTORNO
import autocreador as auto

# Fase 0: Escudo de autocuración antes de cargar librerías pesadas
auto.verificar_y_reparar_entorno(tts_pipeline=None)

print("🔄 1. Inicializando Inteligencia Artificial (Whisper Base y Kokoro)...")
stt_model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=1, num_workers=1)
tts_pipeline = KPipeline(lang_code='e', repo_id=None)

# Fase 0.5: Cocinar audios locales si faltasen en la carpeta
auto.verificar_y_reparar_entorno(tts_pipeline)

pack = torch.load(RUTA_VOZ_LOCAL, map_location='cpu')
silencio_hardware = np.zeros(9600, dtype=np.float32)
carrito_interno = {"Pizzas": [], "Bebidas": []}

def lanzar_relleno_inmediato_sin_esperar():
    print("⚡ [RELLENO EMITIDO DESDE CARPETA AL MILISEGUNDO]")
    idx = random.randint(0, len(FRASES_RELLENO) - 1)
    try:
        data, fs = sf.read(f"audios_fijos/relleno_{idx}.wav", dtype='float32')
        sd.play(data, fs)
    except: pass

def hablar_texto_dinamico(texto):
    print(f"\n🤖 Dora: {texto}")
    generator = tts_pipeline(texto, voice=pack, speed=1.1)
    for _, _, audio in generator:
        sd.play(np.concatenate([silencio_hardware, audio]), 24000)
        sd.wait()

def escanear_frase_y_actualizar_carrito(texto_cliente):
    txt = texto_cliente.lower()
    sabor_detectado = None
    for s in ["barbacoa", "barbaco", "robacoa", "carbonara", "carbonada", "margarita", "pepperoni", "peperoni", "vegetariana"]:
        if s in txt:
            sabor_detectado = "Barbacoa" if s in ["barbaco", "robacoa"] else ("Pepperoni" if "peperoni" in s else ("Carbonara" if "carbonada" in s else s.capitalize()))
            break
    tamanio_detectado = "Mediana"
    for t in ["individual", "mediana", "familiar", "familia"]:
        if t in txt:
            tamanio_detectado = "Familiar" if "familia" in t else t.capitalize()
            break
    if sabor_detectado:
        clave = f"Pizza {sabor_detectado} {tamanio_detectado}"
        precio = PRECIOS.get(clave, 11.90)
        carrito_interno["Pizzas"].append({"sabor": sabor_detectado, "tamanio": tamanio_detectado, "precio": precio})
        print(f"🛒 [PYTHON]: Añadida Pizza {sabor_detectado} {tamanio_detectado} ({precio:.2f}€)")
        return f"Anotada tu pizza {sabor_detectado} de tamaño {tamanio_detectado}."

    bebida_detectada = None
    if "coca" in txt or "cola" in txt: bebida_detectada = "Coca-Cola grande" if "grande" in txt else "Coca-Cola de lata"
    elif "fanta" in txt or "naranja" in txt or "limón" in txt: bebida_detectada = "Fanta grande" if "grande" in txt else "Fanta de lata"
    elif "cerveza" in txt or "birra" in txt: bebida_detectada = "Cerveza de lata"
    elif "agua" in txt: bebida_detectada = "Agua"
    if bebida_detectada:
        precio = PRECIOS.get(bebida_detectada, 2.00)
        carrito_interno["Bebidas"].append({"nombre": bebida_detectada, "precio": precio})
        print(f"🛒 [PYTHON]: Añadida Bebida {bebida_detectada} ({precio:.2f}€)")
        return f"Apuntada la {bebida_detectada} para la cuenta."
    return None

def generar_ticket_y_despedida(nombre, json_p):
    total, linhas = 0.0, []
    for p in carrito_interno["Pizzas"]:
        total += p["precio"]
        linhas.append(f" - 1x Pizza {p['sabor']} ({p['tamanio']}) -> {p['precio']:.2f}€")
    for b in carrito_interno["Bebidas"]:
        total += b["precio"]
        linhas.append(f" - 1x {b['nombre']} -> {b['precio']:.2f}€")
    if total == 0.0:
        hablar_texto_dinamico(f"Perfecto {nombre}. No hemos anotado platos. ¡Hasta la próxima!")
        return
    hablar_texto_dinamico(f"Perfecto {nombre}. El total de tu comanda son exactamente {total:.2f} euros.")
    hablar_texto_dinamico("En unos veinte minutos puedes pasar a recogerla por el local." if json_p["tipo_entrega"] == "recoger" else "El repartidor llegará a tu domicilio en unos treinta minutos.")
    with open("ticket_cocina.txt", "w", encoding="utf-8") as f:
        f.write(f"🍕 --- TICKET DE COCINA ---\n👤 CLIENTE: {nombre}\n📦 ENTREGA: {json_p['tipo_entrega'].upper()}\n------------------------------------------------\n🛒 PRODUCTOS:\n" + "\n".join(linhas) + f"\n------------------------------------------------\n💰 TOTAL NETO: {total:.2f} EUR\n")

# =====================================================================
# 🚀 EJECUCIÓN CENTRALITA
# =====================================================================
print("\n🚀 Centralita Abierta.")
json_pedido = form.ejecutar_formulario_inicial(stt_model, ollama, hablar_texto_dinamico)
nombre_cliente = json_pedido["nombre"]

CONTESTA_CON_MEMORIA_JSON = f"{PROMPT_TELEFONO}\n\n🚨 --- ESTADO PEDIDO ---\n- CLIENTE: {json_pedido['nombre']}\n- ENTREGA: {json_pedido['tipo_entrega'].upper()}\n\nConfirma en 6 palabras el producto añadido de forma simpática. ¡PROHIBIDO hablar de dinero!"
historial_chat = []

while True:
    try:
        pedido_cliente = form.escuchar_microfono(stt_model)
        low_text = pedido_cliente.lower()
        if not pedido_cliente.strip():
            hablar_texto_dinamico("¿Deseas añadir alguna pizza o bebida más?")
            continue

        lanzar_relleno_inmediato_sin_esperar()
        palabras_sueltas = low_text.replace(".", "").replace(",", "").replace("?", "").split()
        
        if any(p in palabras_sueltas for p in ["cuánto", "precio", "cuenta", "total", "cobrar", "cuesta", "nada", "adiós", "gracias", "listo", "terminar"]) or "nada más" in low_text or "ya está" in low_text:
            sd.wait()
            generar_ticket_y_despedida(nombre_cliente, json_pedido)
            break

        if any(p in palabras_sueltas for p in ["tardaréis", "tarda", "tiempo", "minutos"]):
            sd.wait()
            hablar_texto_dinamico(f"Tu pedido estará listo en unos veinte minutos, {nombre_cliente}.")
            continue

        confirmacion_python = escanear_frase_y_actualizar_carrito(pedido_cliente)
        if confirmacion_python:
            sd.wait()
            hablar_texto_dinamico(f"{confirmacion_python} ¿Qué más te pongo, {nombre_cliente}?")
            historial_chat.extend([{'role': 'user', 'content': pedido_cliente}, {'role': 'assistant', 'content': confirmacion_python}])
            continue

        if not any(p in palabras_sueltas for p in ["vale", "de acuerdo", "bueno", "ok", "hola", "sí", "si"]):
            sd.wait()
            hablar_texto_dinamico(f"Disculpa {nombre_cliente}, no te he entendido bien. ¿Me lo puedes repetir por favor?")
            continue

        historial_chat.append({'role': 'user', 'content': pedido_cliente})
        response = ollama.chat(model='qwen2.5:1.5b', messages=[{'role': 'system', 'content': CONTESTA_CON_MEMORIA_JSON}] + historial_chat[-4:])
        respuesta_dora = response['message']['content']
        historial_chat.append({'role': 'assistant', 'content': respuesta_dora})
        
        sd.wait()
        hablar_texto_dinamico(respuesta_dora)
        
    except KeyboardInterrupt:
        print("\n[INFO] Apagando centralita..."); sd.stop(); break
