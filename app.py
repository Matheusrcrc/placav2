import streamlit as st
import easyocr
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import re
from io import BytesIO

# Configurações iniciais
st.set_page_config(page_title="Reconhecimento de Placas", layout="wide", initial_sidebar_state="expanded")
st.title("Reconhecimento de Placas Mercosul")

# Inicialização da tabela de dados
if "placas" not in st.session_state:
    st.session_state["placas"] = pd.DataFrame(columns=["Timestamp", "Número da Placa", "Thumbnail"])

def processar_imagem(imagem):
    """Processa a imagem para extrair texto usando EasyOCR."""
    reader = easyocr.Reader(['en', 'pt'])  # Configura os idiomas do OCR
    results = reader.readtext(np.array(imagem), detail=0)
    return results

def filtrar_placa(results):
    """Filtra o texto para identificar apenas o padrão de placa Mercosul."""
    padrao_placa = r"[A-Z]{3}\d{1}[A-Z]{1}\d{2}"
    for text in results:
        if re.match(padrao_placa, text):
            return text
    return None

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
        results = processar_imagem(imagem)
        st.write(f"Texto extraído: {', '.join(results)}")

        # Filtragem para encontrar a placa válida
        placa = filtrar_placa(results)
        if placa:
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
