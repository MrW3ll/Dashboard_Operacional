import sys
import pandas as pd
import datetime as dt
import engine as engs
import numpy as np

from sqlalchemy import text
from pathlib import Path

sys.path.insert(0, str(Path("C:/Users/wconceicao/OneDrive - Grupo A Educação SA/Área de Trabalho/Projetos")))

metas_dados = pd.read_excel(r'P:\Mais_Campus_CallCenter\Sales Ops - Time Leonardo\Patric_Barbosa\documentação\python\Dash\files\meta_dados_ies.xlsx')
metas_dados = pd.DataFrame(metas_dados)


def carregar_dados() -> dict[str, pd.DataFrame]:
    engs = engs.get_engine()

    queries = [
        'painel_tickets_operadores.sql',
        'painel_vendas_operadores.sql',
    ]

    resultado = {}

    for nome_query in queries:
        chave = nome_query.replace(".sql","")
        query = text(engs.load_query(nome_query))

        resultado[chave] = pd.read_sql(query,engs)

        return resultado

def tratar_dados(raw: dict[str,pd.DataFrame]) -> pd.DataFrame:
    df_tickets = raw['painel_tickets_operadores']
    df_vendas = raw['painel_vendas_operadores']

    
    print("📊 Colunas de painel_tickets:", df_tickets.columns.tolist())
    print(f"📊 Registros em painel_tickets: {len(df_tickets)}")
    print("📊 Primeiras linhas:\n", df_tickets.head())
    
    print("\n📊 Colunas de painel_vendas:", df_vendas.columns.tolist())
    print(f"📊 Registros em painel_vendas: {len(df_vendas)}")
    

    vendas = df_vendas[
        ['ies_name','operator_user','vendas']
    ].groupby(['ies_name','operator_user']).sum().reset_index()

    df_tickets.columns = df_tickets.columns.str.lower().str.replace(" ","_")

