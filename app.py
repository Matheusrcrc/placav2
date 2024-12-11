import streamlit as st
import cv2
import pytesseract
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import re
from io import BytesIO
import os

# Configurações iniciais
st.set_page_config(page_title="Reconhecimento de Placas", layout="wide", initial_sidebar_state="expanded")
st.title("Reconhecimento de Placas Mercosul")

# Configuração do caminho do Tesseract para Streamlit Cloud ou ambientes locais
if os.name == "nt":  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
elif os.name == "posix":  # Linux ou Streamlit Cloud
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
else:
    st.error("Sistema operacional não suportado para configurar o Tesseract.")

# Inicialização da tabela de dados
if "placas" not in st.session_state:
    st.session_state["placas"] = pd.DataFrame(columns=["Timestamp", "Número da Placa", "Thumbnail"])

def processar_imagem(imagem):
    """Processa a imagem para extrair texto usando OCR."""
    imagem_array = np.array(imagem)
    if len(imagem_array.shape) == 2:  # Imagem já está em escala de cinza
        imagem_cinza = imagem_array
    elif len(imagem_array.shape) == 3:  # Imagem colorida
        imagem_cinza = cv2.cvtColor(imagem_array, cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError("Formato de imagem não suportado.")

    # Testar diferentes valores de --psm para melhor precisão
    psm_options = [6, 8, 11]  # Exemplos de modos de segmentação de página
    for psm in psm_options:
        texto_extraido = pytesseract.image_to_string(imagem_cinza, config=f"--psm {psm}")
        if texto_extraido.strip():
            return texto_extraido
    return ""

def salvar_dados(timestamp, placa, thumbnail):
    """Salva os dados na tabela."""
    nova_linha = {
        "Timestamp": timestamp,
        "Número da Placa": placa,
        "Thumbnail": thumbnail
    }
    st.session_state["placas"] = pd.concat([st.session_state["placas"], pd.DataFrame([nova_linha])], ignore_index=True)

# Upload de imagem
uploaded_file = st.file_uploader("Envie uma imagem da placa:", type=["jpg", "jpeg", "png"])
if uploaded_file:
    imagem = Image.open(uploaded_file)
    st.image(imagem, caption="Imagem enviada", use_container_width=True)

    # Processamento da imagem
    try:
        texto_extraido = processar_imagem(imagem)
        st.write(f"Texto extraído: {texto_extraido}")

        # Verificação de padrão de placa Mercosul
        padrao_placa = r"[A-Z]{3}\d{1}[A-Z]{1}\d{2}"
        if re.match(padrao_placa, texto_extraido.strip()):
            placa = texto_extraido.strip()
            st.success(f"Placa reconhecida: {placa}")

            # Gerar thumbnail
            thumbnail = imagem.resize((100, 50))
            thumbnail_buffer = BytesIO()
            thumbnail.save(thumbnail_buffer, format="JPEG")
            thumbnail_bytes = thumbnail_buffer.getvalue()

            # Salvar os dados
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            salvar_dados(timestamp, placa, thumbnail_bytes)
        else:
            st.error("Nenhuma placa válida foi encontrada na imagem.")
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")

# Exibir tabela de dados
st.write("### Dados das placas reconhecidas")
if not st.session_state["placas"].empty:
    st.dataframe(st.session_state["placas"].drop(columns=["Thumbnail"]))
