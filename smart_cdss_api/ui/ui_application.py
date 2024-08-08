import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as plt_go
import json

from smart_cdss_api.conf import conf
from smart_cdss_api.api import load

user_ok = "smartcdss"

st.title('Smartcdss Api UI')


@st.cache(suppress_st_warning=True)
def download():
    with st.spinner('Loading Data...'):
        load.download()
    st.success('Loaded')


def load_options():
    return load.load_options()


def load_map_sitio():
    return list(load.load_map_sitio()[conf.xlsx_sitio_col].unique())


df = None
rest_selected = {}
labs = ['grupo', 'familia', 'microrganismo']
selected = {}


def make_json():
    selected[conf.opt_rest] = rest_selected
    json_return = json.dumps(selected, ensure_ascii=False)
    return json.loads(json_return)


def print_df_result(df):
    st.header('Antibióticos')
    st.table(df)

    if 'Amostra' in df.columns:
        chart = 'barh'
        if selected[conf.opt_sepse] == conf.sepse_risk[0]:
            fig = plt_go.Figure()
            df = df.iloc[::-1, :]
            for antib in df.index:
                ic_min = df.loc[antib, conf.interval_min_col]
                ic_max = df.loc[antib, conf.interval_max_col]
                val = df.loc[antib, conf.prob_nb_col]
                fig.add_trace(plt_go.Box(
                    x=[ic_min, val, ic_max],
                    y=[antib, antib, antib],
                    name=antib,
                    hoverinfo="x+name",
                    orientation="h",
                ))
        else:
            fig = plt_go.Figure()
            fig.add_trace(plt_go.Sunburst(
                name="",
                labels=(["Antibiotico"] + list(df.index)),
                parents=["", "Antibiotico", "Antibiotico", "Antibiotico"],
                values=([1] + list(df[conf.prob_nb_col].values)),
                textinfo="label+percent parent",
                branchvalues="total",
            ))
            fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig)

    st.header("Dosagem")
    cols_model = [conf.dosage_col, conf.dosage_admin_col, conf.dosage_freq_col]
    cols_dosage = [(x, conf.vals_rest_va[1].title()) for x in cols_model]
    cols_dosage += [(x, conf.vals_rest_va[2].title()) for x in cols_model]
    cols_dosage.sort()

    df_dosage = pd.DataFrame(columns = cols_dosage, index=df.index)
    df_dosage.columns = pd.MultiIndex.from_tuples(cols_dosage, names=['Col','Via'])

    for antib in df.index:
        for c in cols_model:
            for r in conf.vals_rest_va[1:]:
                df_dosage.loc[antib, (c, r.title())] = (
                        df.loc[antib,c][r]
                )

    df_dosage[conf.dosage_rest_col] = df[conf.dosage_rest_col]

    st.table(df_dosage)


def send_api():
    api_json = make_json()
    ret_json = load.application(api_json)
    try:
        aux_json = ret_json[conf.opt_json_antibiotico]
        if aux_json:
            df = pd.DataFrame(aux_json).set_index(conf.opt_json_medic)
            df.rename(lambda s: s.replace('_','.',1).replace('_','. ').title(),
                      axis='columns', inplace=True)
        else:
            df = pd.DataFrame()
        if not df.empty:
            print_df_result(df)
            st.json(ret_json)
        else:
            st.subheader("Não há resultados (^ ^;)")
            st.write("Desculpe, mas estamos trabalhando para aumentar a nossa\
                    Base de Dados.")
            st.write("Lembre-se que a consulta deve fazer sentido\
                    em casos reais.")
            st.write("Tente diminuir o número mínimo de amostras\
                    ou fazer uma nova consulta com outros dados.")
    except ValueError as e:
        st.subheader("Subdivisão de Sítio em Tratamento (^ ^;)")
        st.write("A subdivisão de sítio selecionada é um caso especial a qual\
                está sendo analisada separadamente.")
        st.write(ret_json)


def login_on():
    download()
    options, combines_group, combines_family = load_options()
    sitios = load_map_sitio()

    st.sidebar.header('Amostra')
    new_sample = st.sidebar.slider(
        'Quantidade mínima de amostra por antibiótico',
        0, 300, 30)
    load.set_min_sample(new_sample)
    sample = load.get_min_sample()
    st.sidebar.markdown("Amostra: " + str(sample))

    st.sidebar.header('Riscos')
    aux_sepse = st.sidebar.selectbox(conf.opt_sepse, conf.sepse_risk)

    st.sidebar.header('Dados Ambulatoriais')
    for amb in conf.values.keys():
        selected[amb] = (
            st.sidebar.selectbox(amb, list(conf.values[amb].keys()))
        )

    selected[conf.xlsx_sitio_col] = (
        st.sidebar.selectbox(conf.xlsx_sitio_col, sitios)
    )

    st.sidebar.header('Dados Laboratoriais')

    options[conf.opt_group].insert(0, None)
    combines_group[None] = [None]
    combines_family[None] = [None]

    selected[labs[0]] = (
        st.sidebar.selectbox(labs[0], options[conf.opt_group])
    )
    selected[labs[1]] = (
        st.sidebar.selectbox(labs[1], combines_group[selected[labs[0]]])
    )
    selected[labs[2]] = (
        st.sidebar.selectbox(labs[2], combines_family[selected[labs[1]]])
    )
    selected[conf.opt_sepse] = aux_sepse

    st.sidebar.header('Restrições')
    aux_name = ["diabetico", "imunossupressao", "gestante",
                "alergico a cefalosporina", "alergico a penicilina",
                "neoplasia"]
    aux_fr = conf.vals_rest_fr
    if aux_sepse in conf.sepse_risk[1:]:
        aux_va = [conf.vals_rest_va[-1]]
    else:
        aux_va = conf.vals_rest_va
    aux_rest_va = st.sidebar.selectbox(conf.opt_rest_va, aux_va)
    aux_rest_fr = st.sidebar.selectbox(conf.opt_rest_fr, aux_fr)
    i = 0
    for rest in conf.restrictions_poss:
        rest_selected[rest] = (st.sidebar.checkbox(aux_name[i]))
        i += 1
    rest_selected[conf.opt_rest_va] = aux_rest_va
    rest_selected[conf.opt_rest_fr] = aux_rest_fr

    if st.button("Buscar"):
        send_api()


st.sidebar.header('Login')
user = st.sidebar.text_input("User")
password = st.sidebar.text_input("Password", type="password")

if user == user_ok and load.validate_ui_token(password):
    st.write(
        "Preencha os dados nos campos ao lado e "
        "clique em 'Buscar' para efetuar a pesquisa"
    )
    login_on()
