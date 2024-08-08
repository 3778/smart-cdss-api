import pandas as pd 
import requests
import time
import os
import json

SECRET_TOKEN = os.environ['SMARTCDSS_SECRET_TOKEN']
IP = 'http://localhost:8010'

"""
{
    "filtro": {
          "uf": "11",
          "municipio": "1100015",
          "instituicao": "Hospital Marcelino Champagnat",
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
    }, 
    "parametro": "municipio"
}
"""

testes = {
    "uf": {
        "filtro": {
        }, 
        "parametro": "uf"
    },
    "municipio": {
        "filtro": {
            "uf": "PR"
        }, 
        "parametro": "municipio"
    },
    "instituicao": {
        "filtro": {
            "uf": "PR",
            "municipio": "CURITIBA",
        }, 
        "parametro": "instituicao"
    },
    "idade":{
        "filtro": {
            "uf": "PR",
            "municipio": "CURITIBA",
            "instituicao": "Hospital Nossa Senhora das Graças",
        }, 
        "parametro": "idade"
    },
    "sitio":{
        "filtro": {
            "uf": "PR",
            "municipio": "CURITIBA",
            "instituicao": "Hospital Nossa Senhora das Graças",
        }, 
        "parametro": "subdivisao_sitio"
    },
    "filter": {
        "filtro": {
            "uf": "PR",
            "municipio": "CURITIBA",
            "instituicao": "Hospital Nosa Senhora das Graças",
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

        }, 
        "parametro": "uf"
    },

}

def test_api(dict_json, ip=IP):
    start = time.time()
    response = requests.post(
        f'{ip}/smartcdss/api/v1.0/get_parameter/',
        json=dict_json,
        #headers={'TOKEN': SECRET_TOKEN}
        headers={'Authorization': 'Bearer ' + SECRET_TOKEN}
    )
    time_elapsed = time.time() - start
    return response.status_code, time_elapsed, response.content


for name_test, test in testes.items():
    status, time_t, content = test_api(dict_json=test)
    json_return = json.dumps(json.loads(content.decode()), indent=4)
    print(f"==========={name_test}==========")
    print(f"""
    Status: {status}
    Time: {time_t}
    Return: {json_return}
    """)
