# Libraries
import streamlit as st
import pandas as pd
import plotly.express as px

# Functions
from fn_formatar_valores import formatar_valores
from fn_carregar_dados import carregar_dados
from fn_footer import footer

# Configure
st.set_page_config(
    page_title='Dashboard de Vendas - Produtos',
    layout='wide'
)

# Load data
dados_raw = carregar_dados()

# Sidebar
st.sidebar.title('Filtros')

# Year filter
anos_disponiveis = sorted(list(dados_raw['Data da Compra'].dt.year.unique()), reverse=True)
ano_selecionado = st.sidebar.checkbox('Todo o período', value=True)
if not ano_selecionado:
    ano = st.sidebar.slider('Selecione o ano', min_value=min(anos_disponiveis), max_value=max(anos_disponiveis), value=(min(anos_disponiveis), max(anos_disponiveis)))
else:
    ano = (min(anos_disponiveis), max(anos_disponiveis))

# Region filter
regioes = sorted(list(dados_raw['Local da compra'].unique()))
regiao_selecionada = st.sidebar.multiselect('Selecione a Região/Estado', regioes)

# Category filter
categorias = sorted(list(dados_raw['Categoria do Produto'].unique()))
categoria_selecionada = st.sidebar.multiselect('Selecione a Categoria', categorias)

# Apply filters
dados_filtrados = dados_raw.copy()

# Year filter
if not ano_selecionado:
    dados_filtrados = dados_filtrados[(dados_filtrados['Data da Compra'].dt.year >= ano[0]) & (dados_filtrados['Data da Compra'].dt.year <= ano[1])]

# Region filter
if regiao_selecionada:
    dados_filtrados = dados_filtrados[dados_filtrados['Local da compra'].isin(regiao_selecionada)]

# Category filter
if categoria_selecionada:
    dados_filtrados = dados_filtrados[dados_filtrados['Categoria do Produto'].isin(categoria_selecionada)]

# Calculate metrics
receita_total = dados_filtrados['Preço'].sum()
qtd_vendas_total = dados_filtrados.shape[0]
ticket_medio = receita_total / qtd_vendas_total if qtd_vendas_total > 0 else 0

# Main interface
st.title('📊 Dashboard de Vendas - Produtos')
st.markdown("---")

# KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Receita Total', formatar_valores(receita_total, 'R$'))
with col2:
    st.metric('Quantidade de Vendas', formatar_valores(qtd_vendas_total))
with col3:
    st.metric('Ticket Médio', formatar_valores(ticket_medio, 'R$'))

st.markdown("---")

# Tabs
aba1, aba2, aba3, aba4 = st.tabs(['Visão Geral', 'Análise de Produtos', 'Análise de Vendedores', 'Dados Brutos'])

# Tab 1: Overview
with aba1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Mapa de Vendas")
        # Group by local for the map
        receita_estados = dados_filtrados.groupby('Local da compra')[['Preço']].sum()
        mapa_dados = dados_raw.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)
        
        mapa_dados['Preço Formatado'] = mapa_dados['Preço'].apply(lambda x: formatar_valores(x, 'R$'))

        fig_mapa = px.scatter_geo(
            mapa_dados,
            lat='lat',
            lon='lon',
            size='Preço',
            scope='south america',
            template='seaborn',
            hover_name='Local da compra',
            hover_data={'lat': False, 'lon': False, 'Preço': False, 'Preço Formatado': True},
            custom_data=['Preço Formatado'],
            title='Receita por Estado',
            color='Preço',
            color_continuous_scale='Viridis'
        )
        fig_mapa.update_traces(hovertemplate='<b>%{hovertext}</b><br>Preço=%{customdata[0]}')
        fig_mapa.update_layout(height=500, margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_mapa, use_container_width=True)

    with col2:
        st.subheader("Evolução Mensal")
        receita_mensal = dados_filtrados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))[['Preço']].sum().reset_index()
        receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.strftime('%b/%Y')
        
        fig_evolucao = px.line(
            receita_mensal,
            x='Mês',
            y='Preço',
            markers=True,
            title='Evolução da Receita Mensal',
            template='plotly_white'
        )
        fig_evolucao.update_layout(yaxis_title='Receita')
        st.plotly_chart(fig_evolucao, use_container_width=True)

# Tab 2: Product Analysis
with aba2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Receita por Categoria")
        receita_categoria = dados_filtrados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=True)
        fig_cat = px.bar(
            receita_categoria,
            x='Preço',
            y=receita_categoria.index,
            orientation='h',
            text_auto=True,
            title='Receita por Categoria',
            template='plotly_white'
        )
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with col2:
        st.subheader("Top 5 Estados (Receita)")
        top_estados = dados_filtrados.groupby('Local da compra')[['Preço']].sum().sort_values('Preço', ascending=False).head(5)
        fig_estados = px.bar(
            top_estados,
            x='Preço',
            y=top_estados.index,
            orientation='h',
            text_auto=True,
            title='Top 5 Estados em Vendas',
            template='plotly_white',
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig_estados, use_container_width=True)

# Tab 3: Seller Analysis
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores para visualizar', 2, 20, 5)
    
    vendedores = dados_filtrados.groupby('Vendedor')[['Preço']].sum()
    vendedores_qtd = dados_filtrados.groupby('Vendedor')['Preço'].count()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Top {qtd_vendedores} Vendedores (Receita)")
        top_vendedores_receita = vendedores.sort_values('Preço', ascending=False).head(qtd_vendedores)
        fig_vend_receita = px.bar(
            top_vendedores_receita,
            x='Preço',
            y=top_vendedores_receita.index,
            text_auto=True,
            title=f'Top {qtd_vendedores} por Receita',
            template='plotly_white'
        )
        st.plotly_chart(fig_vend_receita, use_container_width=True)
        
    with col2:
        st.subheader(f"Top {qtd_vendedores} Vendedores (Quantidade)")
        top_vendedores_qtd = vendedores_qtd.sort_values(ascending=False).head(qtd_vendedores)
        fig_vend_qtd = px.bar(
            x=top_vendedores_qtd.values,
            y=top_vendedores_qtd.index,
            text_auto=True,
            title=f'Top {qtd_vendedores} por Quantidade de Vendas',
            template='plotly_white'
        )
        fig_vend_qtd.update_layout(xaxis_title='Quantidade', yaxis_title='Vendedor')
        st.plotly_chart(fig_vend_qtd, use_container_width=True)

# Tab 4: Raw Data
with aba4:
    st.subheader("Base de Dados Completa")
    with st.expander("Visualizar Dados"):
        st.dataframe(dados_filtrados)
        
    st.download_button(
        label="Baixar Dados Filtrados (.csv)",
        data=dados_filtrados.to_csv(index=False).encode('utf-8'),
        file_name='vendas_filtradas.csv',
        mime='text/csv',
    )

if __name__ == "__main__":

    footer()
