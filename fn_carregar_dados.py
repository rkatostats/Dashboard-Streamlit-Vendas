import streamlit as st
import requests
import pandas as pd

@st.cache_data
def carregar_dados():
    url = 'https://labdados.com/produtos'
    response = requests.get(url)
    df = pd.DataFrame.from_dict(response.json())
    df['Data da Compra'] = pd.to_datetime(df['Data da Compra'], format='%d/%m/%Y')
    return df
