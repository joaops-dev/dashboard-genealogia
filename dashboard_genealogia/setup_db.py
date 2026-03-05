import pandas as pd
import sqlite3

df = pd.read_csv('tabela_clientes.csv')

conn = sqlite3.connect('dados_genealogia.db')

df.columns = df.columns.str.lower().str.replace(' ', '_')
df.to_sql('tabela_clientes', conn, if_exists = 'replace', index = False)

conn.commit()
conn.close()
print('Banco de dados atualizado com sucesso')