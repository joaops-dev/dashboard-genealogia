import streamlit as st

def dashboard_executor(nome_pessoa):
    if nome_pessoa == 'Executores':
        st.title('Visão Global: Todos os Executores')
        st.info('Mostrando a carteira de TODA a equipe de execução!')
        #df_executor = df

    else:
        st.title(f'Carteira de: {nome_pessoa}')
        st.subheader('Executor')
        st.info(f'O sistema busca as metas apenas de {nome_pessoa}!')
        #seria o código pra carregar a tabela, mas como esse é o arquivo de teste não vai ter, finge que tem tho.
        #df_executor = df[df['nome_responsavel'] == nome_pessoa]
        #st.dataframe(df_executor)

def dashboard_pesquisador(nome_pessoa):
    if nome_pessoa == 'Pesquisadores':
        st.title('Visão Global: Todos os Pesquisadores')
        st.info('Mostrando a carteira de TODA a equipe de pesquisa!')
        #df_pesquisador = df

    else:
        st.title(f'Carteira de: {nome_pessoa}')
        st.subheader('Pesquisador')
        st.info(f'O sistema busca as metas apenas de {nome_pessoa}!')
        #seria o código pra carregar a tabela, mas como esse é o arquivo de teste não vai ter, finge que tem tho.
        #df_pesquisador = df[df['nome_responsavel'] == nome_pessoa]
        #st.dataframe(df_pesquisador)

login = {
    'joaopedro.silva': {'senha': '000', 'nome_real': 'João Pedro Silva Freitas', 'cargo': 'executor'},
    'leandro.pires': {'senha': '0001', 'nome_real': 'Leandro Pires Costa', 'cargo': 'executor'},
    'vanessa.rocha': {'senha': '111', 'nome_real': 'Vanessa Rocha', 'cargo': 'pesquisador'},
    'ian.castello': {'senha': '1112', 'nome_real': 'Ian De Carvalho Castello Branco', 'cargo': 'pesquisador'},
    'lucas.hernandes': {'senha': '222', 'nome_real': 'Lucas Vinicius Hernandes Alves Da Mota', 'cargo': 'gestor'},
    'luiza.sahara': {'senha': '333', 'nome_real': 'Luiza Sahara Da Silva Santos', 'cargo': 'coordenador'}
}

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if st.session_state['logado'] == False:
    st.title('Acesso Restrito')

    usuario_digitado = st.text_input('Usuário')
    senha_digitada = st.text_input('Senha')

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
        aba_executores, aba_pesquisadores = st.tabs(['Executores', 'Pesquisadores'])

        with aba_executores:
            lista_executores = sorted(['João Pedro Silva Freitas', 'Leandro Pires Costa'])
            lista_executores.insert(0, 'Executores')
            executor_escolhido = st.selectbox('De quem é a carteira que você quer ver?', lista_executores)
            dashboard_executor(executor_escolhido)

        with aba_pesquisadores:
            lista_pesquisadores = sorted(['Vanessa Rocha', 'Ian De Carvalho Castello Branco'])
            lista_pesquisadores.insert(0, 'Pesquisadores')
            pesquisador_escolhido = st.selectbox('De quem é a carteira que você quer ver?', lista_pesquisadores)
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