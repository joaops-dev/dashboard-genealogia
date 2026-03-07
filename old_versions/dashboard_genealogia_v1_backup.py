import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
from datetime import datetime
import unicodedata
import os

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
    Conecta ao banco SQLite local e extrai os dados dos clientes.
    Armazenado em cache para otimizar a performance.
    """
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_banco = os.path.join(pasta_atual, 'dados_genealogia.db')

    conn = sqlite3.connect(caminho_banco)
    query = 'SELECT * FROM tabela_clientes'
    df = pd.read_sql_query(query, conn)

    query_metas = 'SELECT * FROM tabela_metas'
    df_metas = pd.read_sql_query(query_metas, conn)
    conn.close()

    df['data_inicio_pesquisas'] = pd.to_datetime(df['data_inicio_pesquisas'], dayfirst = True, errors = 'coerce')
    df['data_vencimento'] = df['data_inicio_pesquisas'] + pd.to_timedelta(180, unit = 'd')
    df['data_dif'] = (pd.Timestamp.now() - df['data_inicio_pesquisas']).dt.days
    df['data_regressiva'] = (180 - df['data_dif']).clip(lower = 0)
    df['nome_responsavel'] = df['nome_responsavel'].fillna('Sem Responsável')

    return df, df_metas

df, df_metas = carregar_dados()

# -----------------------------------------------------------------------------
# 3. TRANSFORMAÇÃO E FILTROS (ETL - Transform)
# -----------------------------------------------------------------------------
with st.sidebar.expander('Quem é Você?'):
    nomes_unicos = df['nome_responsavel'].unique().tolist()

    opcoes_executor = sorted(nomes_unicos, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
    opcoes_executor.insert(0, 'Genealogia')
    filtro_executor = st.selectbox('Executores', opcoes_executor)

    if filtro_executor == 'Genealogia':
        df_colaborador = df
    else:
        df_colaborador = df[df['nome_responsavel'] == filtro_executor]

# -----------------------------------------------------------------------------
# 4. REGRAS DE NEGÓCIO E KPIs
# -----------------------------------------------------------------------------
mes_atual = datetime.now().month
ano_atual = datetime.now().year

df_alerta = df_colaborador[
    (df_colaborador['data_vencimento'].dt.month == mes_atual) &
    (df_colaborador['data_vencimento'].dt.year == ano_atual)
].sort_values(by = 'data_dif', ascending = False)

df_criticos = df_colaborador[df_colaborador['data_dif'] >= 180].sort_values(by = 'data_dif', ascending = False)

meta_clientes = len(df_criticos)
meta_executor = df_metas[
    (df_metas['nome_responsavel'] == filtro_executor) &
    (df_metas['mes'] == mes_atual) &
    (df_metas['ano'] == ano_atual)
]

if not meta_executor.empty:
    meta_alvo = int(meta_executor['meta_fixa'].iloc[0])
    distancia_meta = meta_alvo - meta_clientes
else:
    distancia_meta = 0

# -----------------------------------------------------------------------------
# 5. RENDERIZAÇÃO DA INTERFACE VISUAL
# -----------------------------------------------------------------------------
configuracao_padrao = {
    'nome_cliente': st.column_config.TextColumn('Nome do Cliente'),
    'link_do_app': st.column_config.LinkColumn('Link do App', display_text = 'Abrir Link'),
    'data_dif': st.column_config.NumberColumn('Dias de Casa', format = '%d dias'),
    'data_regressiva': st.column_config.NumberColumn('Dias Restantes', format = '%d dias'),
    'data_inicio_pesquisas': st.column_config.DateColumn('Início', format = 'DD/MM/YYYY'),
    'data_vencimento': st.column_config.DateColumn('Vencimento', format = 'DD/MM/YYYY')
}

# Gráfico de Dias na Casa
st.markdown('---')
st.header(f'Mostrando {len(df_colaborador)} Clientes')

#Visualização de Gráficos e Tabelas de Meta
col_kpi, col_clientes = st.columns(2)

col_kpi.metric('Clientes >= 180 Dias', meta_clientes, delta = distancia_meta)

col_kpi.subheader('Dias na Casa')
tabela_clientes = df_colaborador['faixa_dias_pesquisa'].value_counts().reset_index(name = 'quantidade')
fig_clientes = px.pie(tabela_clientes, values = 'quantidade', names = 'faixa_dias_pesquisa', hole = 0.4)
col_kpi.plotly_chart(fig_clientes, width = 'stretch')

col_clientes.warning('⚠️ Clientes próximos de estourar o prazo')
col_clientes.dataframe(
    df_alerta[['nome_cliente', 'link_do_app', 'data_dif', 'data_regressiva', 'data_vencimento']],
    column_config = configuracao_padrao,
    width = 'stretch',
    height = 475,
    hide_index = True
)

st.subheader('Clientes >= 180 Dias')
st.dataframe(
    df_criticos[['nome_cliente', 'link_do_app', 'data_dif', 'data_inicio_pesquisas', 'data_vencimento']],
    column_config = configuracao_padrao,
    width = 'stretch',
    hide_index = True
)

#Visualização da Carteira
with st.expander('Sua Carteira'):
    st.dataframe(
        df_colaborador,
        column_config = configuracao_padrao,
        width = 'stretch',
        hide_index = True
    )

# Rodapé do Sistema
st.sidebar.markdown('---')
st.sidebar.caption('Build v1.0.0 | Dev: João Pedro')