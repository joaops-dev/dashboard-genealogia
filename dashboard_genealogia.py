import time
import requests
import unicodedata
import urllib.parse
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from streamlit_cookies_controller import CookieController

# -----------------------------------------------------------------------------
# 1. SETUP E CONSTANTES
# -----------------------------------------------------------------------------
st.set_page_config(page_title = 'Cleitin 3.1', layout = 'wide')

st.markdown(
    '''
    <style>
    [data-testid='stElementToolbar'] {
        display: none !important;
    }

    button[title='Download as CSV'] {
        visibility: hidden;
        display: none !important;
    }
    </style>
    ''',
    unsafe_allow_html = True
)

controller = CookieController()
st.title('Painel de Clientes')

TEMAS_GRAFICO = {
    'Corporativo': {
        '>=180 dias': '#FF4B4B', '91-179 dias': '#FF8C00',
        '31-90 dias': '#FFC300', '<30 dias': '#00CC96', 'Sem data': '#8D99AE'
    },
    'Cidadania4u': {
        '>=180 dias': '#8B1C31', '91-179 dias': '#D4AF37',
        '31-90 dias': '#004B87', '<30 dias': '#008C45', 'Sem data': '#A9A9A9'
    },
    'Hacker': {
        '>=180 dias': '#FF0000', '91-179 dias': '#FFD300', 
        '31-90 dias': '#008F11', '<30 dias': '#00FF41', 'Sem data': '#4D4D4D'
    },
    'Kali Linux': {
        '>=180 dias': '#E74C3C', '91-179 dias': '#F39C12', 
        '31-90 dias': '#2980B9', '<30 dias': '#1ABC9C', 'Sem data': '#7F8C8D'
    },
    'Mr. Robot': {
        '>=180 dias': '#8A0303', '91-179 dias': '#C0392B', 
        '31-90 dias': '#BDC3C7', '<30 dias': '#ECF0F1', 'Sem data': '#2C3E50'
    },
    'Cleitin': {
        '>=180 dias': '#FF007F', '91-179 dias': '#FF7F50', 
        '31-90 dias': '#00E5FF', '<30 dias': '#39FF14', 'Sem data': '#9D4EDD'
    }
}

if 'paleta_atual' not in st.session_state:
    st.session_state['paleta_atual'] = TEMAS_GRAFICO['Corporativo']

ORDEM_STATUS = ['>=180 dias', '91-179 dias', '31-90 dias', '<30 dias', 'Sem data']

TIME_EXECUTORES = [
    'Érica Silva de Almeida Martins',
    'Bruna Rocha Amaral',
    'Leandro Pires Costa',
    'Isabella Fernandes Fukushima',
    'Rayssa Gomes Carvalho',
    'Emerson de Oliveira Figueredo'
]
TIME_PESQUISADORES = [
    'Ian Castello',
    'Vanessa Rocha',
    'Ana Beatriz Sobral',
    'Thaiane Alves Araujo',
    'Lourena'
]

API_URL = 'https://api-genealogia.onrender.com'

# -----------------------------------------------------------------------------
# 2. EXTRAÇÃO DE DADOS (ETL - Extract)
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados():

    """
    Busca os dados no FastAPI e aplica as transformações de negócio.
    """
    try:
        res_clientes = requests.get(f'{API_URL}/clientes')
        df = pd.DataFrame(res_clientes.json())

        res_metas = requests.get(f'{API_URL}/metas')
        df_metas = pd.DataFrame(res_metas.json())

        df['data_inicio_pesquisas'] = pd.to_datetime(df['data_inicio_pesquisas'], dayfirst = True, errors = 'coerce')
        df['data_vencimento'] = df['data_inicio_pesquisas'] + pd.to_timedelta(180, unit = 'd')
        df['data_dif'] = (pd.Timestamp.now() - df['data_inicio_pesquisas']).dt.days
        df['data_regressiva'] = (180 - df['data_dif']).clip(lower = 0)
        df['nome_responsavel'] = df['nome_responsavel'].fillna('Sem Responsável')

        return df, df_metas

    except Exception as e:
        st.error(f'Erro ao conectar com a API: {e}')
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl = 600)
def buscar_nota(nome):
    try:
        nome_url = urllib.parse.quote(nome)
        res = requests.get(f'{API_URL}/notas/{nome_url}', timeout = 5)

        if res.status_code == 200:
            return res.json().get('texto', '')
        
    except:
        pass
    
    return ''

def bloco_de_notas(nome_usuario):
    st.markdown('---')
    st.subheader(f'Bloco de Notas {nome_usuario}')

    texto_atual = buscar_nota(nome_usuario)

    texto_editado = st.text_area(
        'Seu espaço livre',
        value = texto_atual,
        height = 300,
        placeholder = 'Digite seus rascunhos, pendências e lembretes aqui...',
        label_visibility = 'collapsed',
        key = f'nota_{nome_usuario}'
    )

    if st.button('Salvar Bloco de Notas', key = f'btn_{nome_usuario}', width = 'stretch'):
        payload = {'dono_nota': nome_usuario, 'texto': texto_editado}

        try:
            res = requests.post(f'{API_URL}/notas', json = payload)

            if res.status_code == 200:
                buscar_nota.clear()
                st.toast('Anotações salvas com sucesso!', icon = '✅')
                time.sleep(1)
                st.rerun()

            else:
                st.error('Erro ao salvar no banco.')

        except Exception as e:
            st.error(f'Erro de conexão: {e}')

def enviar_csv(arquivo, endpoint):
    try:
        files = {'arquivo': (arquivo.name, arquivo.getvalue(), 'text/csv')}
        response = requests.post(f'{API_URL}/{endpoint}', files = files)

        if response.status_code == 200:
            resultado = response.json()

            if resultado.get('sucesso'):
                st.sidebar.success(resultado.get('mensagem'))
                st.cache_data.clear()
                time.sleep(1.5)
                st.rerun()

            else:
                st.sidebar.error(f'Erro na API: {resultado.get("erro")}')

        else:
            st.sidebar.error(f'Erro de conexão: {response.status_code}')

    except Exception as e:
        st.sidebar.error(f'Falha ao enviar: {e}')

df, df_metas = carregar_dados()

# -----------------------------------------------------------------------------
# 2. DEFININDO OS DASHBOARDS
# 2.1 DASHBOARD DOS EXECUTORES
# -----------------------------------------------------------------------------
def dashboard_executor(nome_colaborador):
    if nome_colaborador == 'Executores':
        st.title('Visão Global: Todos os Executores')
        df_colaborador = df[df['nome_responsavel'].isin(TIME_EXECUTORES)]

    else:
        st.title(f'Carteira de: {nome_colaborador}')
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
    ].sort_values(by = 'dias_sem_novas_notas', ascending = False)

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
        'dias_sem_novas_notas': st.column_config.NumberColumn('Dias Sem Notas', format = '%d dias', help = 'Quantidade de dias que a nota está atrasada'),
        'link_do_app': st.column_config.LinkColumn('Link do App', display_text = 'Abrir Link'),
        'faixa_dias_pesquisa': st.column_config.TextColumn('Status do Cliente'),
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
        color_discrete_map = st.session_state['paleta_atual'],
        category_orders = {'faixa_dias_pesquisa': ORDEM_STATUS}
    )
    fig_clientes.update_traces(sort = False)
    col_kpi.plotly_chart(fig_clientes, width = 'stretch', key = f'grafico_exec_{nome_colaborador}', config = {'displayModeBar': False})

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
        df_criticos[['nome_cliente', 'link_do_app', 'dias_sem_novas_notas', 'data_dif', 'data_inicio_pesquisas', 'data_vencimento']],
        column_config = configuracao_padrao,
        width = 'stretch',
        hide_index = True
    )

    #Visualização da Carteira
    colunas_carteira = [
        'nome_cliente',
        'dias_sem_novas_notas',
        'link_do_app',
        'data_dif',
        'faixa_dias_pesquisa',
        'data_inicio_pesquisas',
        'data_vencimento'
    ]

    df_carteira = df_colaborador[colunas_carteira].sort_values(
        by = 'dias_sem_novas_notas',
        ascending = False
    )

    with st.expander('Sua Carteira'):
        st.dataframe(
            df_carteira,
            column_config = configuracao_padrao,
            width = 'stretch',
            hide_index = True
        )
    
    bloco_de_notas(nome_colaborador)

# -----------------------------------------------------------------------------
# 2.2 DASHBOARD DOS PESQUISADORES
# -----------------------------------------------------------------------------
def dashboard_pesquisador(nome_colaborador):
    if nome_colaborador == 'Pesquisadores':
        st.title('Visão Global: Todos os Pesquisadores')
        df_colaborador = df[df['nome_responsavel'].isin(TIME_PESQUISADORES)]

    else:
        st.title(f'Carteira de: {nome_colaborador}')
        df_colaborador = df[df['nome_responsavel'] == nome_colaborador]

    # -----------------------------------------------------------------------------
    # 2.2.1 TRANSFORMAÇÃO E FILTROS (ETL - Transform)
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------------------
    # 2.2.2 REGRAS DE NEGÓCIO E KPIs
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
    ].sort_values(by = 'dias_sem_novas_notas', ascending = False)

    clientes_criticos = len(df_criticos)
    clientes_alerta = len(df_alerta)
    
    meta_mensal = df_metas[
        (df_metas['mes'] == mes_atual) &
        (df_metas['ano'] == ano_atual)
    ]

    meta_alvo = None

    if nome_colaborador == 'Pesquisadores':
        meta_equipe = meta_mensal[meta_mensal['nome_responsavel'].isin(TIME_PESQUISADORES)]
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
    # 2.2.3 RENDERIZAÇÃO DA INTERFACE VISUAL
    # -----------------------------------------------------------------------------
    configuracao_padrao = {
        'nome_cliente': st.column_config.TextColumn('Nome do Cliente'),
        'dias_sem_novas_notas': st.column_config.NumberColumn('Dias Sem Notas', format = '%d dias', help = 'Quantidade de dias que a nota está atrasada'),
        'link_do_app': st.column_config.LinkColumn('Link do App', display_text = 'Abrir Link'),
        'faixa_dias_pesquisa': st.column_config.TextColumn('Status do Cliente'),
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
        color_discrete_map = st.session_state['paleta_atual'],
        category_orders = {'faixa_dias_pesquisa': ORDEM_STATUS}
    )
    fig_clientes.update_traces(sort = False)
    col_kpi.plotly_chart(fig_clientes, width = 'stretch', key = f'grafico_exec_{nome_colaborador}', config = {'displayModeBar': False})

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
        df_criticos[['nome_cliente', 'link_do_app', 'dias_sem_novas_notas', 'data_dif', 'data_inicio_pesquisas', 'data_vencimento']],
        column_config = configuracao_padrao,
        width = 'stretch',
        hide_index = True
    )

    #Visualização da Carteira
    colunas_carteira = [
        'nome_cliente',
        'dias_sem_novas_notas',
        'link_do_app',
        'data_dif',
        'faixa_dias_pesquisa',
        'data_inicio_pesquisas',
        'data_vencimento'
    ]

    df_carteira = df_colaborador[colunas_carteira].sort_values(
        by = 'dias_sem_novas_notas',
        ascending = False
    )

    with st.expander('Sua Carteira'):
        st.dataframe(
            df_carteira,
            column_config = configuracao_padrao,
            width = 'stretch',
            hide_index = True
        )

    bloco_de_notas(nome_colaborador)

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

    elif visao_escolhida == 'Pesquisadores':
        st.title('Visão Macro: Pesquisadores')
        df_visao =df[df['nome_responsavel'].isin(TIME_PESQUISADORES)]

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

    col_kpi, col_tabela = st.columns(2)

    col_kpi.metric('Clientes >= 180 Dias', clientes_criticos)

    tabela_clientes = df_visao['faixa_dias_pesquisa'].value_counts().reset_index(name = 'quantidade')
    fig_clientes = px.pie(
        tabela_clientes,
        values = 'quantidade',
        names = 'faixa_dias_pesquisa',
        hole = 0.4,
        color = 'faixa_dias_pesquisa',
        color_discrete_map = st.session_state['paleta_atual'],
        category_orders = {'faixa_dias_pesquisa': ORDEM_STATUS}
    )
    fig_clientes.update_traces(sort = False)
    col_kpi.plotly_chart(fig_clientes, width = 'stretch', key = f'grafico_gen_{visao_escolhida}', config = {'displayModeBar': False})

    col_tabela.info('Mostrando Todos Clientes')
    col_tabela.dataframe(df_visao, width = 'stretch', hide_index = True)

# -----------------------------------------------------------------------------
# 3. DESENHANDO AS DIFERENTES VISÕES DO SITE
# -----------------------------------------------------------------------------
login = st.secrets['usuarios']

cookie_usuario = controller.get('usuario_logado')
cookie_cargo = controller.get('cargo_logado')

if cookie_usuario and cookie_cargo:
    st.session_state['logado'] = True
    st.session_state['nome'] = cookie_usuario
    st.session_state['cargo'] = cookie_cargo

if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'cargo' not in st.session_state:
    st.session_state['cargo'] = None
if 'nome' not in st.session_state:
    st.session_state['nome'] = None

if st.session_state['logado'] == False:
    st.title('Acesso Restrito')

    usuario_digitado = st.text_input('Usuário')
    senha_digitada = st.text_input('Senha', type = 'password')

    if st.button('Entrar'):
        if usuario_digitado in login and login[usuario_digitado]['senha'] == senha_digitada:
            st.session_state['logado'] = True
            st.session_state['nome'] = login[usuario_digitado]['nome_real']
            st.session_state['cargo'] = login[usuario_digitado]['cargo']

            controller.set('usuario_logado', login[usuario_digitado]['nome_real'], max_age = 86400)
            controller.set('cargo_logado', login[usuario_digitado]['cargo'], max_age = 86400)
            
            st.success('Login efetuado! Carregando...')
            time.sleep(1.0)
            st.rerun()

        else:
            st.error('Usuário ou senha incorretos.')

else:
    cargo = st.session_state['cargo']

    #VISUALIZAÇÃO DO GESTOR, COORDENADOR E DEV
    if cargo in ['dev', 'gestor', 'coordenador']:
        nome_logado = st.session_state['nome']
        st.title(f'Seja bem-vindo, {nome_logado}')

        with st.sidebar.expander('Atualizar Dados', expanded = False):
            up_clientes = st.file_uploader('CSV de Clientes', type = ['csv'], key = 'up_cli')

            if up_clientes:
                if st.button('Confirmar Upload Clientes', width = 'stretch'):
                    enviar_csv(up_clientes, 'upload-clientes')

            st.markdown('---')
            up_metas = st.file_uploader('CSV de Metas', type = ['csv'], key = 'up_met')

            if up_metas:
                if st.button('Confirmar Upload Metas', width = 'stretch'):
                    enviar_csv(up_metas, 'upload-metas')

        if cargo == 'dev' or nome_logado == 'João Pedro Silva Freitas':
            st.sidebar.header('Ferramentas VIP')

            if st.sidebar.button('Limpar Cache do Banco'):
                st.cache_data.clear()
                st.toast('Cache limpo com sucesso!', icon = '✅')
                time.sleep(1.5)
                st.rerun()

            tema_escolhido = st.sidebar.selectbox('Paleta de Cores:', list(TEMAS_GRAFICO.keys()))

            if st.session_state.get('paleta_atual') != TEMAS_GRAFICO[tema_escolhido]:
                st.session_state['paleta_atual'] = TEMAS_GRAFICO[tema_escolhido]
                st.rerun()

        aba_genealogia, aba_executores, aba_pesquisadores = st.tabs(['Genealogia', 'Executores', 'Pesquisadores'])

        with aba_genealogia:
            nomes_unicos = df['nome_responsavel'].unique().tolist()
            lista_geral = ['Genealogia', 'Executores', 'Pesquisadores'] + sorted(nomes_unicos, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            visao_escolhida = st.selectbox('Selecione a Visão Macro:', lista_geral, key = 'sel_gen')
            dashboard_genealogia(visao_escolhida)

        with aba_executores:
            lista_executores = ['Executores'] + sorted(TIME_EXECUTORES, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            executor_escolhido = st.selectbox('Selecione o Executor:', lista_executores, key = 'sel_exec')
            dashboard_executor(executor_escolhido)

        with aba_pesquisadores:
            lista_pesquisadores = ['Pesquisadores'] + sorted(TIME_PESQUISADORES, key = lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore'))
            pesquisador_escolhido = st.selectbox('Selecione o Pesquisador:', lista_pesquisadores, key = 'sel_pesq')
            dashboard_pesquisador(pesquisador_escolhido)

    #VISUALIZAÇÃO DO EXECUTOR
    elif cargo == 'executor':
        nome_logado = st.session_state['nome']
        dashboard_executor(nome_logado)
    
    #VISUALIZAÇÃO DO PESQUISADOR
    elif cargo == 'pesquisador':
        nome_logado = st.session_state['nome']
        dashboard_pesquisador(nome_logado)

    if st.sidebar.button('Sair'):
        controller.remove('usuario_logado')
        controller.remove('cargo_logado')
        st.session_state.clear()
        time.sleep(1.5)
        st.rerun()

# Rodapé do Sistema
st.sidebar.markdown('---')
st.sidebar.caption('Build v3.1.0 | Dev: João Pedro')