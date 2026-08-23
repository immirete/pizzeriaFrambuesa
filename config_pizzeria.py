# config_pizzeria.py

# Ruta del archivo de voz de Dora en tu Dell Latitude
RUTA_VOZ_LOCAL = "em_dora.pt"

NOMBRE_PIZZERIA = "Pizzería Frambuesa"
DIRECCION_RECOGIDA = "Calle Frambuesa 4, Sant Adrià de Besòs"

# Menú oficial detallado de tu negocio
MENU_OFICIAL = {
    "pizzas": ["Barbacoa", "Carbonara", "Margarita", "Pepperoni", "Vegetariana"],
    "tamanios": ["Individual", "Mediana", "Familiar"],
    "bebidas": ["Coca-Cola de lata", "Coca-Cola grande", "Fanta de lata", "Fanta grande", "Cerveza de lata", "Agua"]
}

# --- TABLA DE PRECIOS DETALLADA POR PRODUCTO Y TAMAÑO ---
# Ahora Python puede buscar el precio exacto cruzando el sabor de la pizza con su tamaño
PRECIOS = {
    # Precios de Pizzas por tipo y tamaño
    "Pizza Barbacoa Individual": 7.50,
    "Pizza Barbacoa Mediana": 11.90,
    "Pizza Barbacoa Familiar": 15.90,
    
    "Pizza Carbonara Individual": 7.50,
    "Pizza Carbonara Mediana": 11.90,
    "Pizza Carbonara Familiar": 15.90,
    
    "Pizza Margarita Individual": 6.50,
    "Pizza Margarita Mediana": 9.90,
    "Pizza Margarita Familiar": 12.90,
    
    "Pizza Pepperoni Individual": 7.50,
    "Pizza Pepperoni Mediana": 11.90,
    "Pizza Pepperoni Familiar": 15.90,
    
    "Pizza Vegetariana Individual": 7.00,
    "Pizza Vegetariana Mediana": 11.20,
    "Pizza Vegetariana Familiar": 14.90,
    
    # Precios de Bebidas y Formatos
    "Coca-Cola de lata": 2.00,
    "Coca-Cola grande": 3.50,
    "Fanta de lata": 2.00,
    "Fanta grande": 3.50,
    "Cerveza de lata": 2.00,
    "Agua": 1.50
}

# Tus frases de relleno personalizadas para eliminar la latencia (Sirve de plano para grabar_fijos.py)
FRASES_RELLENO = [
    "A ver...si, ahora mismo",
    "Estupendo... Voy a ello",
    "Un segundo...Si, enseguida ",
    "Vale...entendido",
    "Entendido! Déjame ver..."
]

# PROMPT DE INSTRUCCIONES RÍGIDAS PARA QWEN
PROMPT_TELEFONO = (
    f"Eres Dora, la telefonista automatizada de la '{NOMBRE_PIZZERIA}'. Tu único trabajo es tomar pedidos por teléfono.\n"
    f"Ubicación para recogidas: {DIRECCION_RECOGIDA}.\n\n"
    "CARTA OFICIAL DE PRODUCTOS:\n"
    f"- Pizzas válidas: {', '.join(MENU_OFICIAL['pizzas'])}\n"
    f"- Tamaños válidos: {', '.join(MENU_OFICIAL['tamanios'])}\n"
    f"- Bebidas válidas: {', '.join(MENU_OFICIAL['bebidas'])}\n\n"
    "REGLAS TOTALMENTE OBLIGATORIAS:\n"
    "1. El cliente ya te ha dicho su nombre. Dirígete a él por su nombre en cada frase de forma cercana (ej: 'Perfecto Iván...').\n"
    "2. Responde SIEMPRE con una única frase muy corta y al grano (máximo 12 palabras).\n"
    "3. Si el cliente dice mal un ingrediente (ej: 'cargonara' o 'barbaco'), asimila que es 'Carbonara' o 'Barbacoa' según la carta, pero no le digas cómo hablar.\n"
    "4. Si el cliente pide una bebida, asegúrate de confirmar si la quiere de 'lata' o 'grande' según nuestra carta.\n"
    "5. Si el pedido es para RECOGER, recuérdale sutilmente la dirección de Calle Frambuesa.\n"
    "6. Si el pedido es para ENVIAR a domicilio, debes solicitar obligatoriamente al cliente: su Dirección de entrega completa y su Teléfono de contacto.\n"
    "7. Si el cliente pide la cuenta o pregunta cuánto cuesta, NO inventes números. Limítate a decir algo como: 'Perfecto, un segundo que te calculo el total'.\n"
    "8. No saludes dos veces, no repitas tu propio nombre y no inventes productos fuera de la carta. Mantén un tono rápido y comercial."
)
