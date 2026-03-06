import pandas as pd
import sqlite3
from datetime import datetime

df = pd.read_csv('meta_executores.csv')
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

conn = sqlite3.connect('dados_genealogia.db')
df_derretido.to_sql('tabela_metas', conn, if_exists = 'append', index = False)
conn.commit()
conn.close()