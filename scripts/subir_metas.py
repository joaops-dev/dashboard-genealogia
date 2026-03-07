import pandas as pd
import sqlite3
from datetime import datetime
import os

pasta_atual = os.path.dirname(os.path.abspath(__file__))
caminho_csv = os.path.join(pasta_atual, '..', 'data', 'meta_executores.csv')
caminho_banco = os.path.join(pasta_atual, '..', 'data', 'dados_genealogia.db')

df = pd.read_csv(caminho_csv)
df_filtrado = df[df['Clientes na Operação'] == 'Meta']
df_derretido = pd.melt(
    df_filtrado,
    id_vars = ['Clientes na Operação'],
    var_name = 'nome_responsavel',
    value_name = 'meta_fixa'
)
df_derretido = df_derretido.drop(columns = ['Clientes na Operação'])

df_derretido['mes'] = datetime.now().month
df_derretido['ano'] = datetime.now().year

conn = sqlite3.connect(caminho_banco)
df_derretido.to_sql('tabela_metas', conn, if_exists = 'append', index = False)
conn.commit()
conn.close()