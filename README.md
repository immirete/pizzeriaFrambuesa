# 🍕 Centralita Telefónica Local por Voz — Pizzería Frambuesa

> **Sistema automático de toma de pedidos por voz, 100 % local, privado y offline.**

Proyecto de código abierto que implementa una centralita telefónica inteligente para la gestión automática de pedidos de una pizzería.

El sistema combina **Speech-to-Text, un modelo de lenguaje pequeño (SLM) y Text-to-Speech**, ejecutándose completamente en local y sin depender de servicios de pago en la nube.

Está diseñado para funcionar de forma fluida en hardware de consumo. Ha sido probado en un **Intel Core i7 de 13.ª generación**, sin necesidad de una GPU dedicada.

---

## 📚 Índice

* [✨ Características](#-características)
* [🏗️ Arquitectura](#️-arquitectura)
* [🛠️ Tecnologías](#️-tecnologías)
* [💻 Requisitos](#-requisitos)
* [🚀 Instalación](#-instalación)

  * [Dependencias del sistema](#1-dependencias-del-sistema)
  * [Miniconda](#2-miniconda)
  * [Entorno Python](#3-entorno-python)
  * [Modelos locales](#4-modelos-locales)
* [▶️ Ejecución](#️-ejecución)
* [📁 Estructura del proyecto](#-estructura-del-proyecto)
* [🔒 Privacidad](#-privacidad)
* [📄 Licencia](#-licencia)

---

## ✨ Características

### 🎙️ Conversación por voz

El cliente interactúa con la centralita utilizando únicamente su voz.

El sistema realiza el flujo completo:

**Cliente → STT → SLM → lógica Python → TTS → Cliente**

### ⚡ VAD dinámico

El micrófono no utiliza bloques de grabación de duración fija.

El sistema detecta automáticamente cuándo el cliente deja de hablar y finaliza la escucha después de **1,5 segundos de silencio continuado**.

### 🗣️ Camuflaje de latencia

Mientras el modelo de lenguaje procesa la respuesta, un hilo independiente reproduce un pequeño audio de relleno previamente generado.

Por ejemplo:

> *"A ver..."*

> *"Entiendo..."*

Esto permite ocultar parte de la latencia de inferencia y conseguir una conversación más natural.

### 🧠 Lógica de negocio controlada por Python

El modelo de lenguaje **no calcula precios ni decide qué productos existen**.

Python mantiene el control sobre:

* Productos disponibles.
* Precios.
* Cantidades.
* Mapeo semántico.
* Estado del pedido.
* Generación del ticket.

Esto reduce el riesgo de errores o "alucinaciones" del modelo.

### 📋 Cuestionario guiado

La conversación sigue un flujo determinista controlado por Python:

```text
Nombre
  ↓
Modo de entrega
  ↓
Validación de dirección
  ↓
Comanda
  ↓
Confirmación
  ↓
Ticket de cocina
```

De esta forma, el modelo de lenguaje se utiliza como componente conversacional, pero **no controla el flujo crítico de la aplicación**.

### 🧾 Ticket de cocina

Al finalizar la llamada se genera automáticamente:

```text
ticket_cocina.txt
```

con el detalle del pedido para la cocina.

---

## 🏗️ Arquitectura

La arquitectura está dividida en varios componentes independientes:

```text
                 ┌──────────────────┐
                 │    Micrófono     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   VAD dinámico   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Faster-Whisper  │
                 │       STT        │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   Lógica Python  │
                 │  Máquina estados │
                 └────────┬─────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
        ┌──────────────┐    ┌──────────────┐
        │    Ollama    │    │  Diccionario │
        │ Qwen 2.5 1.5B│    │  de precios  │
        └──────┬───────┘    └──────────────┘
               │
               ▼
        ┌──────────────┐
        │    Kokoro    │
        │      TTS     │
        └──────┬───────┘
               │
               ▼
        🔊 Altavoz / teléfono
```

---

## 🛠️ Tecnologías

| Componente       | Tecnología                 | Función                                |
| ---------------- | -------------------------- | -------------------------------------- |
| 🎙️ STT          | **Faster-Whisper**         | Transcripción de voz                   |
| 🧠 SLM           | **Ollama + Qwen 2.5 1.5B** | Comprensión y generación de respuestas |
| 🔊 TTS           | **Kokoro-82M**             | Síntesis de voz                        |
| 🎤 Audio         | **sounddevice**            | Captura y reproducción                 |
| 💾 Audio         | **soundfile**              | Gestión de archivos WAV                |
| 🐍 Runtime       | **Python 3.12**            | Lógica de la aplicación                |
| 📐 Procesamiento | **SciPy**                  | Procesamiento de audio                 |

---

## 💻 Requisitos

### Hardware

El proyecto está pensado para funcionar en CPU y no requiere una GPU dedicada.

Hardware de referencia:

* Intel Core i7 de 13.ª generación.
* RAM suficiente para ejecutar los modelos locales.
* Micrófono.
* Altavoces o dispositivo de audio.

### Software

* Python 3.12.
* Miniconda.
* Ollama.
* `espeak-ng`.
* PortAudio.

---

# 🚀 Instalación

## 1. Dependencias del sistema

Antes de configurar Python, instala las dependencias necesarias para audio y síntesis de voz.

### 🐧 Linux — Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y espeak-ng libportaudio2
```

### 🍏 macOS

Requiere [Homebrew](https://brew.sh/).

```bash
brew install espeak-ng portaudio
```

### 🪟 Windows

Descarga e instala `espeak-ng` desde su repositorio oficial.

Después, asegúrate de que la ruta de instalación está disponible en las variables de entorno del sistema.

Habitualmente:

```text
C:\Program Files\eSpeak NG
```

---

## 2. Miniconda

Instala Miniconda para crear un entorno Python aislado.

### 🐧 Linux

```bash
mkdir -p ~/miniconda3

wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
  -O ~/miniconda3/miniconda.sh

bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3

rm -f ~/miniconda3/miniconda.sh

~/miniconda3/bin/conda init bash
```

Cierra y vuelve a abrir la terminal después de ejecutar `conda init`.

### 🍏 macOS

Para Apple Silicon utiliza el instalador `arm64`; para Macs Intel, utiliza `x86_64`.

```bash
mkdir -p ~/miniconda3

curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh \
  -o ~/miniconda3/miniconda.sh

bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3

rm -f ~/miniconda3/miniconda.sh

~/miniconda3/bin/conda init bash
```

> **Nota:** En un Mac Intel sustituye `arm64` por `x86_64`.

### 🪟 Windows

Abre **PowerShell** y descarga el instalador de Miniconda.

Después de instalarlo, abre **Anaconda Prompt** desde el menú Inicio.

---

## 3. Entorno Python

Con una nueva terminal abierta:

```bash
conda create -n kokoro_env python=3.12 -y

conda activate kokoro_env
```

Instala las dependencias:

```bash
pip install \
  kokoro \
  soundfile \
  sounddevice \
  faster-whisper \
  ollama \
  scipy
```

---

## 4. Modelos locales

### 🧠 Ollama

Instala [Ollama](https://ollama.com/) y descarga el modelo utilizado por la centralita:

```bash
ollama run qwen2.5:1.5b
```

Esto descargará el modelo y permitirá ejecutarlo localmente.

### 🔊 Kokoro

Descarga el archivo de voz:

```text
ef_dora.pt
```

y colócalo en la carpeta raíz del proyecto.

La voz utilizada es:

```text
Kokoro-82M
Voz: ef_dora
Sample rate: 24 kHz
```

---

# ▶️ Ejecución

## 🚀 Inicio Automático (Auto-Setup)

Gracias al nuevo motor de autocuración por capas, no se necesitan scripts intermedios de preparación de audio. Para arrancar la centralita por primera vez, simplemente ejecuta en tu terminal:

```bash
python telefono_pizza_final.py
```

### ¿Qué ocurrirá en el primer arranque?
1. El script comprobará si el archivo de voz `ef_dora.pt` está en la raíz. Si falta, **lo descargará de internet automáticamente**.
2. Verificará la existencia de la caché local de audios de respuesta inmediata. Si falta algún archivo, **los grabará todos de golpe** en la carpeta local.
3. El sistema iniciará inmediatamente el servicio de escucha activa y Dora te saludará de viva voz por tus auriculares.

*(A partir del segundo arranque, el proceso se saltará las descargas y se activará en menos de un segundo de forma 100% offline).*

---

## 📁 Estructura del proyecto

Una estructura recomendada sería:

```text
pizzeria-frambuesa/
│
├── telefono_pizza_final.py
├── autocreador.py
├── ef_dora.pt
│
├── audio/
│   ├── a_ver.wav
│   ├── entiendo.wav
│   └── ...
│
├── ticket_cocina.txt
│
├── README.md
└── LICENSE
```

---

## 🔒 Privacidad

Uno de los objetivos principales del proyecto es mantener los datos **localmente**.

La arquitectura no requiere enviar las conversaciones a una API de IA externa:

```text
🎙️ Voz
  ↓
💻 Procesamiento local
  ↓
🧠 Modelo local
  ↓
🔊 Voz sintetizada
```

No se necesita una suscripción a servicios de IA en la nube para ejecutar los componentes principales del sistema.

> **Importante:** La privacidad final dependerá también de la configuración del sistema operativo, del hardware y de cualquier componente externo que se añada posteriormente.

---

## 🎯 Objetivos del proyecto

Este proyecto busca demostrar que es posible construir una centralita conversacional funcional utilizando **IA local y hardware de consumo**, manteniendo el control determinista de la lógica de negocio.

Los principios fundamentales son:

* 🏠 **Local-first**
* 🔒 **Privacidad**
* ⚡ **Baja latencia percibida**
* 🧠 **IA como componente, no como controlador**
* 💰 **Sin dependencia de APIs de pago**
* 🧮 **Lógica de negocio determinista**

---

## 📄 Licencia

Este proyecto es software de código abierto.

Consulta el archivo [`LICENSE`](LICENSE) para conocer las condiciones de uso, modificación y distribución.

---

## ⭐ Contribuciones

Las contribuciones, mejoras y propuestas son bienvenidas.

Si encuentras un problema o tienes una idea para mejorar el sistema, puedes abrir un **Issue** o enviar un **Pull Request**.
