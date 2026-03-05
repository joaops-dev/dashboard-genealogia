import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title = 'Dashboard Genealogia', layout = 'wide')
st.title('Painel de Clientes')

# -----------------------------------------------------------------------------
# 2. EXTRAÇÃO DE DADOS (ETL - Extract)
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    """
    Conecta ao banco SQLite local, extrai os dados dos clientes.
    Armazenado em cache para otimizar a performance.
    """
    conn = sqlite3.connect('dados_genealogia.db')
    query = 'SELECT * FROM tabela_clientes'
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['data_inicio_pesquisas'] = pd.to_datetime(df['data_inicio_pesquisas'], dayfirst = True, errors = 'coerce')
    df['data_vencimento'] = df['data_inicio_pesquisas'] + pd.to_timedelta(180, unit = 'd')
    df['data_dif'] = (pd.Timestamp.now() - df['data_inicio_pesquisas']).dt.days
    return df

df = carregar_dados()

# -----------------------------------------------------------------------------
# 3. TRANSFORMAÇÃO E FILTROS (ETL - Transform)
# -----------------------------------------------------------------------------
with st.sidebar.expander('Quem é Você?'):
    opcoes_executor = df['nome_responsavel'].unique().tolist()
    filtro_executor = st.selectbox('Executores', opcoes_executor)
    if filtro_executor:
        df_colaborador = df[df['nome_responsavel'] == filtro_executor]
    else:
        df_colaborador = df

# -----------------------------------------------------------------------------
# 4. REGRAS DE NEGÓCIO E KPIs
# -----------------------------------------------------------------------------
mes_atual = datetime.now().month
ano_atual = datetime.now().year

df_alerta = df_colaborador[(df_colaborador['data_vencimento'].dt.month == mes_atual) & (df_colaborador['data_vencimento'].dt.year == ano_atual)]

meta_clientes = len(df_colaborador[df_colaborador['data_dif'] >= 180])
meta_alvo = int(meta_clientes * 0.9)
reducao_necessaria = meta_alvo - meta_clientes

# -----------------------------------------------------------------------------
# 5. RENDERIZAÇÃO DA INTERFACE VISUAL
# -----------------------------------------------------------------------------
# Gráfico de Dias na Casa
st.markdown('---')
st.header(f'Mostrando {len(df_colaborador)} Clientes')

#Visualização de Gráficos e Tabelas de Meta
col_clientes, col_kpi = st.columns(2)

col_kpi.metric('Clientes >= 180 Dias', meta_clientes, delta = reducao_necessaria)

col_kpi.subheader('Dias na Casa')
tabela_clientes = df_colaborador['faixa_dias_pesquisa'].value_counts().reset_index(name = 'quantidade')
fig_clientes = px.pie(tabela_clientes, values = 'quantidade', names = 'faixa_dias_pesquisa', hole = 0.4)
col_kpi.plotly_chart(fig_clientes, width = 'stretch')

col_clientes.warning('⚠️ Clientes próximos de estourar o prazo')
col_clientes.dataframe(df_alerta[['nome_cliente', 'link_do_app', 'data_dif', 'data_inicio_pesquisas', 'data_vencimento']], width = 'stretch', height = 450, hide_index = True)

#Visualização da Carteira
with st.expander('Sua Carteira'):
    st.dataframe(df_colaborador, width = 'stretch', hide_index = True)

# Rodapé do Sistema
st.sidebar.markdown('---')
st.sidebar.caption('🛠️ Test Build | Dev: João Pedro')