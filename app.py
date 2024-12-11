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

def comprimir_imagem(imagem, qualidade=85):
    """Comprime a imagem para melhorar o desempenho."""
    buffer = BytesIO()
    imagem.save(buffer, format="JPEG", optimize=True, quality=qualidade)
    buffer.seek(0)
    return Image.open(buffer)

def recortar_area_placa(imagem):
    """Recorta a região da placa na imagem (abaixo da faixa azul e à direita do 'BR')."""
    largura, altura = imagem.size
    # Ajustar os valores de corte conforme necessário
    faixa_superior = int(altura * 0.35)  # 35% da altura a partir do topo
    faixa_inferior = int(altura * 0.75)  # 75% da altura
    faixa_esquerda = int(largura * 0.15)  # 15% da largura a partir da esquerda
    faixa_direita = int(largura * 0.85)  # 85% da largura
    return imagem.crop((faixa_esquerda, faixa_superior, faixa_direita, faixa_inferior))

def processar_imagem(imagem):
    """Processa a imagem para extrair texto usando EasyOCR."""
    reader = easyocr.Reader(['pt'])  # Apenas português para melhor precisão
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

    # Comprimir imagem
    imagem = comprimir_imagem(imagem)
    st.image(imagem, caption="Imagem enviada", use_container_width=True)

    # Recortar a área da placa
    imagem_recortada = recortar_area_placa(imagem)
    st.image(imagem_recortada, caption="Área da placa recortada", use_container_width=True)

    # Processamento da imagem
    try:
        results = processar_imagem(imagem_recortada)
        st.write(f"Texto extraído: {', '.join(results)}")

        # Filtragem para encontrar a placa válida
        placa = filtrar_placa(results)
        if placa:
            st.success(f"Placa reconhecida: {placa}")

            # Gerar thumbnail
            thumbnail = imagem_recortada.resize((100, 50))
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
