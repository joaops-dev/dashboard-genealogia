import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
from datetime import datetime
import unicodedata
import os

# -----------------------------------------------------------------------------
# 1. SETUP E CONSTANTES
# -----------------------------------------------------------------------------
st.set_page_config(page_title = 'Dashboard Genealogia', layout = 'wide')
st.title('Painel de Clientes')

PALETA_STATUS = {
    '>=180 dias': '#FF4B4B',
    '91-179 dias': '#FF8C00',
    '31-90 dias': '#FFC300',
    '<30 dias': '#00CC96',
    'Sem data': '#8D99AE'
}

ORDEM_STATUS = ['>=180 dias', '91-179 dias', '31-90 dias', '<30 dias', 'Sem data']
TIME_EXECUTORES = [
    'Érica Silva de Almeida Martins',
    'Bruna Rocha Amaral',
    'Leandro Pires Costa',
    'Isabella Fernandes Fukushima',
    'Rayssa Gomes Carvalho',
    'Emerson de Oliveira Figueredo'
]

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
    caminho_banco = os.path.join(pasta_atual, 'data', 'dados_genealogia.db')

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
# 2. DEFININDO OS DASHBOARDS
# 2.1 DASHBOARD DOS EXECUTORES
# -----------------------------------------------------------------------------
def dashboard_executor(nome_colaborador):
    if nome_colaborador == 'Executores':
        st.title('Visão Global: Todos os Executores')
        st.info('Mostrando a carteira de TODA a equipe de execução!')
        df_colaborador = df[df['nome_responsavel'].isin(TIME_EXECUTORES)]

    else:
        st.title(f'Carteira de: {nome_colaborador}')
        st.info(f'O sistema busca as metas apenas de {nome_colaborador}!')
        df_colaborador = df[df['nome_responsavel'] == nome_colaborador]

    # -----------------------------------------------------------------------------
    # 2.1.1 TRANSFORMAÇÃO E FILTROS (ETL - Transform)
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------------------
    # 2.1.2 REGRAS DE NEGÓCIO E KPIs
    # -----------------------------------------------------------------------------
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    df_alerta = df_colaborador[
        (df_colaborador['data_vencimento'].dt.month == mes_atual) &
        (df_colaborador['data_vencimento'].dt.year == ano_atual) &
        (df_colaborador['data_dif'] < 180)
    ].sort_values(by = 'data_dif', ascending = False)

    df_criticos = df_colaborador[
        df_colaborador['data_dif'] >= 180
    ].sort_values(by = 'data_dif', ascending = False)

    clientes_criticos = len(df_criticos)
    clientes_alerta = len(df_alerta)
    
    meta_mensal = df_metas[
        (df_metas['mes'] == mes_atual) &
        (df_metas['ano'] == ano_atual)
    ]

    meta_alvo = None

    if nome_colaborador == 'Executores':
        meta_equipe = meta_mensal[meta_mensal['nome_responsavel'].isin(TIME_EXECUTORES)]
        if not meta_mensal.empty:
            meta_alvo = int(meta_equipe['meta_fixa'].sum())

    else:
        meta_individual = meta_mensal[meta_mensal['nome_responsavel'] == nome_colaborador]
        if not meta_individual.empty:
            meta_alvo = int(meta_individual['meta_fixa'].iloc[0])

    distancia_meta = 0
    cor_delta = 'normal'

    if meta_alvo is not None:
        clientes_fim_mes = clientes_criticos + clientes_alerta
        distancia_meta = clientes_fim_mes - meta_alvo

        if distancia_meta > 0:
            cor_delta = 'inverse'
        elif distancia_meta == 0:
            cor_delta = 'normal'
        else:
            cor_delta = 'yellow'

    # -----------------------------------------------------------------------------
    # 2.1.3 RENDERIZAÇÃO DA INTERFACE VISUAL
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

    col_kpi.metric(
        'Clientes >= 180 Dias',
        clientes_criticos,
        delta = distancia_meta,
        delta_color = cor_delta
    )

    col_kpi.subheader('Dias na Casa')
    tabela_clientes = df_colaborador['faixa_dias_pesquisa'].value_counts().reset_index(name = 'quantidade')
    fig_clientes = px.pie(
        tabela_clientes,
        values = 'quantidade',
        names = 'faixa_dias_pesquisa',
        hole = 0.4,
        color = 'faixa_dias_pesquisa',
        color_discrete_map = PALETA_STATUS,
        category_orders = {'faixa_dias_pesquisa': ORDEM_STATUS}
    )
    fig_clientes.update_traces(sort = False)
    col_kpi.plotly_chart(fig_clientes, width = 'stretch', key = f'grafico_exec_{nome_colaborador}')

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

# -----------------------------------------------------------------------------
# 2.2 DASHBOARD DOS PESQUISADORES
# -----------------------------------------------------------------------------
def dashboard_pesquisador(nome_colaborador):
    if nome_colaborador == 'Pesquisadores':
        st.title('Visão Global: Todos os Pesquisadores')
        st.info('Mostrando a carteira de TODA a equipe de pesquisa!')
        df_colaborador = df

    else:
        st.title(f'Carteira de: {nome_colaborador}')
        st.info(f'O sistema busca as metas apenas de {nome_colaborador}!')
        df_colaborador = df[df['nome_responsavel'] == nome_colaborador]
        st.dataframe(df_colaborador)

# -----------------------------------------------------------------------------
# 2.3 DASHBOARD DA GENEALOGIA (VISÃO MACRO)
# -----------------------------------------------------------------------------
def dashboard_genealogia(visao_escolhida):
    if visao_escolhida == 'Genealogia':
        st.title('Visão Macro: Genealogia')
        df_visao = df

    elif visao_escolhida == 'Executores':
        st.title('Visão Macro: Executores')
        df_visao =df[df['nome_responsavel'].isin(TIME_EXECUTORES)]

    else:
        st.title(f'Visão Macro: {visao_escolhida}')
        df_visao = df[df['nome_responsavel'] == visao_escolhida]

    # -----------------------------------------------------------------------------
    # 2.3.1 TRANSFORMAÇÃO E FILTROS (ETL - Transform)
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------------------
    # 2.3.2 REGRAS DE NEGÓCIO E KPIs
    # -----------------------------------------------------------------------------
    df_criticos = df_visao[df_visao['data_dif'] >= 180]
    clientes_criticos = len(df_criticos)

    # -----------------------------------------------------------------------------
    # 2.3.3 RENDERIZAÇÃO DA INTERFACE VISUAL
    # -----------------------------------------------------------------------------
    st.markdown('---')
    st.header(f'Mostrando {len(df_visao)} Clientes')

    col_kpi, col_grafico = st.columns(2)

    col_kpi.metric('Clientes >= 180 Dias', clientes_criticos)

    tabela_clientes = df_visao['faixa_dias_pesquisa'].value_counts().reset_index(name = 'quantidade')
    fig_clientes = px.pie(
        tabela_clientes,
        values = 'quantidade',
        names = 'faixa_dias_pesquisa',
        hole = 0.4,
        color = 'faixa_dias_pesquisa',
        color_discrete_map = PALETA_STATUS,
        category_orders = {'faixa_dias_pesquisa': ORDEM_STATUS}
    )
    fig_clientes.update_traces(sort = False)
    col_grafico.plotly_chart(fig_clientes, width = 'stretch', key = f'grafico_gen_{visao_escolhida}')

    with st.expander('Ver Tabela Completa'):
        st.dataframe(df_visao, width = 'stretch', hide_index = True)

# -----------------------------------------------------------------------------
# 3. DESENHANDO AS DIFERENTES VISÕES DO SITE
# -----------------------------------------------------------------------------
login = st.secrets['usuarios']

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if st.session_state['logado'] == False:
    st.title('Acesso Restrito')

    usuario_digitado = st.text_input('Usuário')
    senha_digitada = st.text_input('Senha', type = 'password')

    if st.button('Entrar'):
        if usuario_digitado in login and login[usuario_digitado]['senha'] == senha_digitada:
            st.session_state['logado'] = True

            st.session_state['nome'] = login[usuario_digitado]['nome_real']
            st.session_state['cargo'] = login[usuario_digitado]['cargo']
            
            st.rerun()
else:
    cargo = st.session_state['cargo']

    if cargo in ['gestor', 'coordenador']:
        nome_logado = st.session_state['nome']
        st.title(f'Seja bem-vindo, {nome_logado}')

        aba_genealogia, aba_executores, aba_pesquisadores = st.tabs(['Genealogia', 'Executores', 'Pesquisadores'])

        with aba_genealogia:
            nomes_unicos = df['nome_responsavel'].unique().tolist()
            lista_geral = ['Genealogia', 'Executores'] + sorted(nomes_unicos, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            visao_escolhida = st.selectbox('Selecione a Visão Macro:', lista_geral, key = 'sel_gen')
            dashboard_genealogia(visao_escolhida)

        with aba_executores:
            lista_executores = ['Executores'] + sorted(TIME_EXECUTORES, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            executor_escolhido = st.selectbox('Selecione o Executor:', lista_executores, key = 'sel_exec')
            dashboard_executor(executor_escolhido)

        with aba_pesquisadores:
            lista_pesquisadores = ['Pesquisadores'] + sorted(['Vanessa Rocha', 'Ian De Carvalho Castello Branco'], key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            pesquisador_escolhido = st.selectbox('Selecione o Pesquisador:', lista_pesquisadores, key = 'sel_pesq')
            dashboard_pesquisador(pesquisador_escolhido)

    elif cargo == 'executor':
        nome_logado = st.session_state['nome']
        dashboard_executor(nome_logado)
       
    elif cargo == 'pesquisador':
        nome_logado = st.session_state['nome']
        dashboard_pesquisador(nome_logado)

    if st.sidebar.button('Sair'):
        st.session_state['logado'] = False
        st.rerun()

# Rodapé do Sistema
st.sidebar.markdown('---')
st.sidebar.caption('Build v2.0.0 | Dev: João Pedro')