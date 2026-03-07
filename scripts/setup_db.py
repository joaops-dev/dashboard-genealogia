import pandas as pd
import sqlite3
import os

pasta_atual = os.path.dirname(os.path.abspath(__file__))
caminho_csv = os.path.join(pasta_atual, '..', 'data', 'tabela_clientes.csv')
caminho_banco = os.path.join(pasta_atual, '..', 'data', 'dados_genealogia.db')

df = pd.read_csv(caminho_csv)

conn = sqlite3.connect(caminho_banco)

df.columns = df.columns.str.lower().str.replace(' ', '_')
df.to_sql('tabela_clientes', conn, if_exists = 'replace', index = False)

conn.commit()
conn.close()
print(f'Sucesso! Banco de dados atualizado em: {caminho_banco}')