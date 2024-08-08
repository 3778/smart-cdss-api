import base64
from json import dumps
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as plt_go

from smart_cdss_api.conf import conf
from smart_cdss_api.api import load


@st.cache(suppress_st_warning=True)
def download():
    with st.spinner('Loading Data...'):
        load.download()
    st.success('Loaded')


def load_data():
    df, _, _ = load.load_data(2)
    return df


def load_map_sitio():
    return load.load_map_sitio()


def make_dfs(df):
    df_analise = []
    aux = 0
    for i in range(-5, -1):
        df_analise.append(
            df
            .groupby(list(df.columns[:i]) + [conf.antib_col])
            [conf.antib_col]
            .agg(['count']))
        df_analise[aux] = df_analise[aux][~(df_analise[aux]['count'] < sample)]
        aux += 1
    return df_analise


def map_reverse_sitio(sitios):
    respost = []
    df_sitios = load_map_sitio()
    for sitio in sitios:
        material_sitio = (
            df_sitios[(df_sitios[conf.opt_sitio]
                   == sitio)]
            [conf.xlsx_sitio_col]
            .values
        )
        material_sitio = list(material_sitio)
        respost += material_sitio
    return respost


def make_chart(df):
    df_group = df.copy()
    df = df.reset_index()
    ids = []
    labels = []
    parents = []
    values = []
    aux = len(df.columns)
    for index, row in df.iterrows():
        for i in range(1, aux):
            val_id = "|".join(row.values[0:i])
            val_parent = "|".join(row.values[0:(i - 1)])
            if val_id not in ids:
                ids.append(val_id)
                parents.append(val_parent)
                labels.append(row.values[(i - 1)])
                if i == (aux - 1):
                    values.append(row.values[i])
                else:
                    mask = (
                        df[list(df.columns[:i])] == row.values[:i]
                    ).all(axis=1)
                    v_aux = df[mask]['count'].sum()
                    values.append(v_aux)

    fig = plt_go.Figure()
    fig.add_trace(plt_go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        textinfo="label+percent root",
        branchvalues="total",
    ))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig)


def make_href(df, text):
    csv = df.to_csv()
    b64_csv = base64.b64encode(csv.encode()).decode()
    size = (3 * len(b64_csv) / 4) / (1_024 ** 2)
    return f"""
    <a download='data.csv'
       href="data:file/csv;base64,{b64_csv}">
       """+text+""" ({size:.02} MB)
    </a><br>
    """


def make_json_version(df):
    df = df.reset_index()
    cols = list(df.columns)
    df = df[cols[:-1]]
    df = (
          df.groupby(cols[:-2])
          [conf.antib_col]
          .agg(['count']))

    df.reset_index(inplace=True)
    columns = []
    for c in list(df.columns)[:-1]:
        df[c] = df[c].apply(remake_values, args=[c])
        invert_map = {v: k for k, v in conf.values_columns.items()} 
        columns.append(invert_map[c])
    columns.append("Qt. Antibiotico")
    df.columns = columns
    return df


def remake_values(data, k):
    invert_map = {v: k for k, v in conf.values_columns.items()} 
    key = invert_map[k]
    value = None
    if key in conf.values.keys():
        invert_map_v = {v: k for k, v in conf.values[key].items()} 
        val = data
        value = invert_map_v[val]
    elif k == conf.opt_sitio:
        value = map_reverse_sitio([data])
    else:
        value = data
    return value


st.sidebar.header('Amostra')
sample = st.sidebar.slider(
    'Quantidade mínima de amostra por antibiótico',
    0, 600, 100)
st.sidebar.markdown("Amostra: " + str(sample))

download()
df = load_data()
df_analise = make_dfs(df)

st.title('Análise de Amostra Smartcdss')
st.write("Total de Amostras BD: " + str(df.shape[0]))

aux_header = ["Dados Ambulatoriais", "Dados com Grupo", "Dados com Familia",
              "Dados com Microorganismo"]
for i in range(0, 4):
    st.header(aux_header[i])
    st.write("Total de combinações: " + str(df_analise[i].shape[0]))
    st.write("Total de Amostras: " + str(df_analise[i]['count'].sum()))
    if st.checkbox("Mostrar Gráfico", key='g' + str(i)):
        make_chart(df_analise[i])
    href = make_href(df_analise[i], "Clique para baixar tabela em CSV")
    st.markdown(href, unsafe_allow_html=True)
    if st.checkbox("Mostrar Tabela", key=i):
        st.table(df_analise[i])
    if st.checkbox("Mostrar Combinações Json", key=i+2):
        df_j = make_json_version(df_analise[i])
        href = make_href(df_j, "Clique para baixar a tabela de entrada em CSV")
        st.markdown(href, unsafe_allow_html=True)
        st.table(df_j)
