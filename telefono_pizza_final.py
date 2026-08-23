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
from config_pizzeria import PROMPT_TELEFONO, RUTA_VOZ_LOCAL, PRECIOS, MENU_OFICIAL, FRASES_RELLENO
import formulario_pedido as form

print("🔄 Inicializando Centralita Final con Control de Errores Activo (Whisper Base)...")
stt_model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=1, num_workers=1)
tts_pipeline = KPipeline(lang_code='e', repo_id=None)

if not os.path.exists(RUTA_VOZ_LOCAL):
    raise FileNotFoundError(f"No encuentro el archivo de voz en: {RUTA_VOZ_LOCAL}")

pack = torch.load(RUTA_VOZ_LOCAL, map_location='cpu')
silencio_hardware = np.zeros(9600, dtype=np.float32)

# --- CARRITO DE CONTROL NUMÉRICO REAL ---
carrito_interno = {
    "Pizzas": [],     
    "Bebidas": []     
}

def reproducir_wav_fijo(ruta_archivo, esperar=True):
    try:
        data, fs = sf.read(ruta_archivo, dtype='float32')
        sd.play(data, fs)
        if esperar: sd.wait()
    except: pass

def lanzar_relleno_inmediato_sin_esperar():
    print("⚡ [RELLENO EMITIDO DESDE CARPETA AL MILISEGUNDO]")
    idx = random.randint(0, len(FRASES_RELLENO) - 1)
    reproducir_wav_fijo(f"audios_fijos/relleno_{idx}.wav", esperar=False)

def hablar_texto_dinamico(texto):
    print(f"\n🤖 Dora: {texto}")
    generator = tts_pipeline(texto, voice=pack, speed=1.1)
    for _, _, audio in generator:
        sd.play(np.concatenate([silencio_hardware, audio]), 24000)
        sd.wait()

def escanear_frase_y_actualizar_carrito(texto_cliente):
    """Filtro semántico nativo. Python extrae los datos reales sin alucinaciones"""
    txt = texto_cliente.lower()
    
    # 1. ESCANEAR PIZZAS
    sabor_detectado = None
    for s in ["barbacoa", "barbaco", "robacoa", "carbonara", "carbonada", "margarita", "pepperoni", "peperoni", "vegetariana"]:
        if s in txt:
            if "barbaco" in s or "robacoa" in s: sabor_detectado = "Barbacoa"
            elif "peperoni" in s: sabor_detectado = "Pepperoni"
            elif "carbonada" in s: sabor_detectado = "Carbonara"
            else: sabor_detectado = s.capitalize()
            break
            
    tamanio_detectado = "Mediana" # Por defecto si no se especifica
    for t in ["individual", "mediana", "familiar", "familia"]:
        if t in txt:
            if "familia" in t: tamanio_detectado = "Familiar"
            else: tamanio_detectado = t.capitalize()
            break
            
    if sabor_detectado:
        clave_precio = f"Pizza {sabor_detectado} {tamanio_detectado}"
        precio_real = PRECIOS.get(clave_precio, 11.90)
        carrito_interno["Pizzas"].append({"sabor": sabor_detectado, "tamanio": tamanio_detectado, "precio": precio_real})
        print(f"🛒 [PYTHON CARRITO]: Añadida Pizza {sabor_detectado} {tamanio_detectado} ({precio_real:.2f}€)")
        return f"Anotada tu pizza {sabor_detectado} de tamaño {tamanio_detectado}."

    # 2. ESCENEAR BEBIDAS
    bebida_detectada = None
    if "coca" in txt or "cola" in txt:
        bebida_detectada = "Coca-Cola grande" if "grande" in txt else "Coca-Cola de lata"
    elif "fanta" in txt or "naranja" in txt or "limón" in txt:
        bebida_detectada = "Fanta grande" if "grande" in txt else "Fanta de lata"
    elif "cerveza" in txt or "birra" in txt:
        bebida_detectada = "Cerveza de lata"
    elif "agua" in txt:
        bebida_detectada = "Agua"
        
    if bebida_detectada:
        precio_real = PRECIOS.get(bebida_detectada, 2.00)
        carrito_interno["Bebidas"].append({"nombre": bebida_detectada, "precio": precio_real})
        print(f"🛒 [PYTHON CARRITO]: Añadida Bebida {bebida_detectada} ({precio_real:.2f}€)")
        return f"Apuntada la {bebida_detectada} para la cuenta."

    return None

def generar_ticket_y_despedida(nombre, json_p):
    total_cuenta = 0.0
    linhas_ticket = []
    
    for p in carrito_interno["Pizzas"]:
        total_cuenta += p["precio"]
        linhas_ticket.append(f" - 1x Pizza {p['sabor']} ({p['tamanio']}) -> {p['precio']:.2f}€")
        
    for b in carrito_interno["Bebidas"]:
        total_cuenta += b["precio"]
        linhas_ticket.append(f" - 1x {b['nombre']} -> {b['precio']:.2f}€")
        
    if total_cuenta == 0.0:
        hablar_texto_dinamico(f"Perfecto {nombre}. No hemos llegado a anotar ningún plato en tu pedido. Si cambias de opinión, llámanos de nuevo.")
        return

    hablar_texto_dinamico(f"Perfecto {nombre}. El total de tu comanda son exactamente {total_cuenta:.2f} euros.")
    if json_p["tipo_entrega"] == "recoger":
        hablar_texto_dinamico("En unos veinte minutos puedes pasar a recogerla por el local de la Calle Frambuesa. ¡Muchas gracias por tu llamada!")
    else:
        hablar_texto_dinamico("El repartidor llegará a tu domicilio en unos treinta minutos. ¡Muchas gracias por tu compra!")
        
    with open("ticket_cocina.txt", "w", encoding="utf-8") as f:
        f.write(f"🍕 --- TICKET DE COCINA - PIZZERÍA FRAMBUESA ---\n")
        f.write(f"👤 CLIENTE: {nombre}\n")
        f.write(f"📦 ENTREGA: {json_p['tipo_entrega'].upper()}\n")
        if json_p['tipo_entrega'] == 'domicilio':
            f.write(f"📍 DIRECCIÓN: {json_p['direccion']}\n")
            f.write(f"📞 TELÉFONO: {json_p['telefono']}\n")
        f.write(f"------------------------------------------------\n")
        f.write(f"🛒 PRODUCTOS EN COCINA:\n")
        for linea in linhas_ticket: f.write(f"{linea}\n")
        f.write(f"------------------------------------------------\n")
        f.write(f"💰 TOTAL NETO A COBRAR: {total_cuenta:.2f} EUR\n")
    print("\n📝 [SISTEMA] 'ticket_cocina.txt' guardado.")

# =====================================================================
# 🚀 FLUJO DE CONVERSACIÓN PRINCIPAL
# =====================================================================
print("\n🚀 Centralita Abierta.")

json_pedido = form.ejecutar_formulario_inicial(stt_model, ollama, hablar_texto_dinamico)
nombre_cliente = json_pedido["nombre"]

CONTESTA_CON_MEMORIA_JSON = (
    f"{PROMPT_TELEFONO}\n\n"
    f"🚨 --- ESTADO REAL DEL PEDIDO ACTUAL ---\n"
    f"- CLIENTE: {json_pedido['nombre']}\n"
    f"- ENTREGA CONFIRMADA: {json_pedido['tipo_entrega'].upper()}\n\n"
    f"INSTRUCCIÓN OBLIGATORIA:\n"
    f"El cliente está respondiendo de forma ordinaria o charlando. "
    f"Responde de forma muy simpática y corta (máximo 6 palabras) preguntándole qué pizza de nuestra carta desea pedir."
)

historial_chat = []

while True:
    try:
        pedido_cliente = form.escuchar_microfono(stt_model)
        low_text = pedido_cliente.lower()
        
        if not pedido_cliente.strip():
            hablar_texto_dinamico("¿Deseas añadir alguna pizza o bebida más?")
            continue

        lanzar_relleno_inmediato_sin_esperar()

        # --- ESCUDO RÍGIDO DE PALABRAS COMPLETAS DE CIERRE ---
        palabras_sueltas = low_text.replace(".", "").replace(",", "").replace("?", "").split()
        palabras_cierre = ["cuánto", "precio", "cuenta", "total", "cobrar", "cuesta", "nada", "adiós", "gracias", "listo", "terminar"]
        quiere_cerrar = any(p in palabras_sueltas for p in palabras_cierre) or "nada más" in low_text or "ya está" in low_text

        if quiere_cerrar:
            sd.wait() 
            generar_ticket_y_despedida(nombre_cliente, json_pedido)
            break

        # DETECCIÓN DE PREGUNTAS SOBRE EL TIEMPO
        es_pregunta_tiempo = any(p in palabras_sueltas for p in ["tardaréis", "tarda", "tiempo", "minutos"])
        if es_pregunta_tiempo:
            sd.wait()
            hablar_texto_dinamico(f"Tu pedido estará listo en unos veinte minutos, {nombre_cliente}.")
            continue

        # --- ACTUALIZACIÓN DE PRODUCTOS POR PYTHON ---
        confirmacion_python = escanear_frase_y_actualizar_carrito(pedido_cliente)
        
        if confirmacion_python:
            sd.wait()
            hablar_texto_dinamico(f"{confirmacion_python} ¿Qué más te pongo, {nombre_cliente}?")
            historial_chat.append({'role': 'user', 'content': pedido_cliente})
            historial_chat.append({'role': 'assistant', 'content': confirmacion_python})
            continue

        # --- 🚨 EL ESCUDO INTEGELENTE SARI SARI SUGERIDO POR IVÁN 🚨 ---
        # Si el cliente ha hablado, pero Python NO ha detectado ni cierre, ni tiempo, ni comida...
        # Detenemos el flujo y pedimos confirmación explícita para evitar bucles raros
        es_charla_ordinaria = any(p in palabras_sueltas for p in ["vale", "de acuerdo", "bueno", "ok", "hola", "sí", "si"])
        
        if not es_charla_ordinaria:
            sd.wait() # Fin del "un segundo..."
            print("⚠️ [SISTEMA]: Frase no identificada en el menú. Activando escudo de cortesía.")
            hablar_texto_dinamico(f"Disculpa {nombre_cliente}, no te he entendido bien. ¿Me lo puedes repetir por favor? De momento no he anotado nada nuevo a tu cuenta.")
            continue

        # En caso de que sea charla ordinaria tipo ("vale", "ok"), Qwen responde con cortesía
        historial_chat.append({'role': 'user', 'content': pedido_cliente})
        
        response = ollama.chat(model='qwen2.5:1.5b', messages=[
            {'role': 'system', 'content': CONTESTA_CON_MEMORIA_JSON}
        ] + historial_chat[-4:])
        
        respuesta_dora = response['message']['content']
        historial_chat.append({'role': 'assistant', 'content': respuesta_dora})
        
        sd.wait()
        hablar_texto_dinamico(respuesta_dora)
        
    except KeyboardInterrupt:
        print("\n[INFO] Apagando centralita de forma segura...")
        sd.stop()
        break
