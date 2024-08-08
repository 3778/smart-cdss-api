from multiprocessing.pool import ThreadPool
import pandas as pd
import requests
import time
import os
import json

SECRET_TOKEN = os.environ['SMARTCDSS_SECRET_TOKEN']
IP = 'http://localhost:8010'

sample_json = {
  "idade": "adulto",
  "sexo": "feminino",
  "atendimento": "comunitario",
  "subdivisao_sitio": "cistite",
  "grupo": "gram_negativo",
  "familia": None,
  "microrganismo": "escherichia_coli",
  "sepse": "alto",
  "restricoes": {
    "diabetico": False,
    "imunossupressao": False,
    "gestante": False,
    "lactante": False,
    "nao_cf": False,
    "nao_pen": False,
    "via_de_administracao": None,
    "funcao_renal": None
  }
}

sample_json_new = {
  "idade": "adulto",
  "sexo": "feminino",
  "atendimento": "comunitario",
  "subdivisao_sitio": "infeccao_primaria_da_cs",
  "grupo": None,
  "familia": None,
  "microrganismo": None,
  "sepse": "alto",
  "restricoes": {
    "diabetico": False,
    "imunossupressao": False,
    "gestante": False,
    "lactante": False,
    "nao_cf": False,
    "nao_pen": False,
    "via_de_administracao": None,
    "funcao_renal":None 
  }
}

sample_json_lactente ={
  "uf": "PR",
  "municipio": None, #"CURITIBA"
  "instituicao": "Hospital Nossa Senhora das Graças", #"Hospital Marcelino Champagnat",
  "idade": "lactente",
  "sexo": "feminino",
  "atendimento": "comunitario",
  "subdivisao_sitio": "cistite",
  "grupo": None,
  "familia": None,
  "microrganismo": None,
  "sepse": "baixo",
  "restricoes": {
    "diabetico": False,
    "imunossupressao": False,
    "gestante": False,
    "lactante": True,
    "nao_cf": False,
    "nao_pen": False,
    "via_de_administracao": None,
    "funcao_renal": None
  }
}

def test_api(dict_json=sample_json, ip=IP):
    start = time.time()
    response = requests.post(
        f'{ip}/smartcdss/api/v1.0/',
        json=dict_json,
        #headers={'TOKEN': SECRET_TOKEN}
        headers={'Authorization': 'Bearer ' + SECRET_TOKEN}
    )
    time_elapsed = time.time() - start
    return response.status_code, time_elapsed, response.content

status, time, content = test_api(dict_json=sample_json_lactente)
json_return = json.dumps(json.loads(content.decode()), indent=4)
print(f"""
Status: {status}
Time: {time}
Return: {json_return}
""")
