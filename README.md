# Smart Cdss API
## Instalar
Para criar um enviroment e instalar as dependêndias, execute:

> `make install`

*Será perguntado o Token de Segurança utilizado na API, e a senha utiliazda na UI.

##  Usar
Para executar as aplicações existêntes, execute:

>Executar a API localmente

>`make launch-api`

>Executar o Jupyter Notebook

>`make launch-jupyter`

>Executar uma UI de uso da API

>`make launch-ui`

>Executar uma UI para Analisar informações do BD

>`make launch-analytics`

>Visualizar a Documentação

>`make launch-documentation`

>Verificar PEP8 dos arquivos desevolvidos

>`make check-pep`

##  Deploy
Para colocar a API no Lambda:

*Lembre-se sempre de informar o Token de Segurança da API.

>Subir API para Lambda:

>`make zappa-deploy`

>Atualizar API do Lambda:

>`make zappa-update`

>Retirar API do Lambda:

>`make zappa-undeploy`

###Error

Se aparecer um erro com relação a lib binária, o zappa apareceu com esse bug em
alguns projetos. Para solucionar esse problema, olhe o comentario do deanq: 

https://github.com/Miserlou/Zappa/issues/755#issuecomment-649250473


## Documentação
### Visão Geral:

Smart Cdss API é um software desenvolvido para a análise da sensibilidade de antibióticos com base em dados ambulatoriais que podem ser complementados com dados clínicos. Sua utilização implica no envio de informações no formato Json para o endereço url da api. O retorno, no formato Json, possui alguns dados, bem como uma lista de medicamentos que surtem efeito para o caso especificado.

### Método de Acesso:

Para utilizar a API, o Header da requisição deve conter duas chaves. A primeira é referente ao conteúdo Json definido no Body. A segunda chave deve ser chamada de ‘Token’ e seu valor deve ser o **token** de acesso informado.

### Json de Entrada:

O Json de entrada deverá possuir o formato especificado nesta seção, não admitindo campos a mais ou a menos. Cada campo possui um tipo (string, bool) sendo que alguns campos aceitam (null). Os campos não aceitam valores que não sejam de seu tipo, resultando em um erro 400. Passar para um campo um valor não especificado aqui, poderá resultar em um erro 400/500 ou em uma resposta vazia.

|Parâmetros|Subseção|Valores
|---|---|---
|idade|   |"recem_nascido”,”lactente”,”crianca”,”adolescente”,”adulto”,”idoso”
|sexo|   |“feminino”,”masculino”
|atendimento|   |“comunitario”,”hospitalar”
|subdivisao_sitio|   |Valor*
|grupo|   |**null**,Valor*
|familia|   |**null**,Valor*
|microrganismo|   |**null**,Valor*
|sepse|   |“baixo”,”moderado”,”alto”
restricoes|diabetico|**true**,**false**
restricoes|imunossupressao|**true**,**false**
restricoes|gestante|**true**,**false**
restricoes|nao_cf|**true**,**false**
restricoes|nao_pen|**true**,**false**
restricoes|via_de_administracao|**null**,”oral”,”parenteral”
restricoes|funcao_renal|**null**,“normal”,“leve-mod”,“mod-grave”,“grave”,“falencia”

*Valor informado separadamente, correspondente a uma subdivisão de sito, um grupo, uma familia ou um microrganismo válidos na base de dados.

Os campos, “grupo”, “familia” e “microrganismo” são complementares, nessa ordem. Ou seja, não pode haver uma especificação de valor para “familia” com o valor  **null** em “grupo”. Bem como não pode haver uma especificação de valor para “microrganismo”, com os campos “grupo” e “familia” com o valor de  **null** . Caso seja enviado o valor de “alto” para o campo “sepse”, é esperado que o campo “via_de_administracao” possua o valor de “parenteral”. O valor  **null** no campo “via_de_administracao” demonstra que não há restrição quanto a exclusividade da administração do medicamento. As restrições “nao_cf” e “nao_pen” estão relacionadas à não utilização de medicamentos com base no grupo  **Cefalosporina** e  **Penicilina**  respectivamente.

**Exemplo Json in:**
```json
{
    "idade": "adulto",
    "sexo": "masculino",
    "atendimento": "hospitalar",
    "subdivisao_sitio": "*********",
    "grupo": null,
    "familia": null,
    "microrganismo": null,
    "sepse": "baixo",
    "restricoes": {
        "diabetico": false,
        "imunossupressao": false,
        "gestante": false,
        "nao_cf": false,
        "nao_pen": false,
        "via_de_administracao": null,
        "funcao_renal": "normal"
    }
}
```

### Json de retorno:

O Json de retorno possui apenas dois campos:

 - **n_critico**, o qual possui o valor do número mínimo de amostra que um antibiótico deve ter para não possuir um alerta de amostragem pequena; 
 - **antibioticos**, o qual é uma lista de subseções contendo as informações dos antibióticos que atendem a tal consulta.

Tais subseções possuem os seguintes campos:

 - **medicamento**, contendo o nome do antibiótico;
 - **sensivel**, contendo a sensibilidade do medicamento;
 - **i_c_max**, contendo o valor máximo do intervalo de confiança;
 - **i_c_min**, contendo o valor mínimo do intervalo de confiança;
 - **amostra**, contendo a quantidade de ocorrências desse medicamento nesse caso analisado na base de dados;
 - **dosagem**, valor da dosagem (**campo ainda em modificações).

Caso não haja dados suficientes para a consulta, a lista do campo **antibioticos** retornará vazia.

A lista de antibióticos pode sofre alterações dependendo do valor do campo **sepse** informado no Json de input. Caso o valor seja ‘baixo“, será retornado uma lista, onde cada elemento será um medicamento com atuação no estado consultado, juntamente com suas informações. Caso o valor seja “moderado” ou “alto”, será retornado uma lista com a combinação dos medicamentos junstamente com uma probabilidade cumulativa.

**Exemplo Json out “sepse” = “baixo”:**
```json
{
    "n_critico":  100 ,
    "antibioticos": [
        {
            "medicamento": "Antib1",
            "sensivel": 0.8338198498748958,
            "i_c_max": 0.9438104119656554,
            "i_c_min": 0.7238292877841361,
            "amostra": 44,
            "dosagem": 100
        },
        {
            "medicamento": "Antib2",
            "sensivel": 0.7798165137614679,
            "i_c_max": 0.915177467826587,
            "i_c_min": 0.6444555596963487,
            "amostra": 36,
            "dosagem": 100
        }
    ]
}
```

**Exemplo Json out “sepse” = “moderado”/”alto”:**
```json
{
    "n_critico":  100,
    "antibioticos": [
        {
            "medicamento": "Antib1",
            "sensivel": 0.8338198498748958,
            "i_c_max": 0.9438104119656554,
            "i_c_min": 0.7238292877841361,
            "amostra": 44,
            "dosagem": 100
        },
        {
            "medicamento": "Antib1 + Antib2",
            "sensivel": 0.9098165137614679,
            "i_c_max": 0.95177467826587,
            "i_c_min": 0.8544555596963487,
            "amostra": 76,
            "dosagem": 100
        },
        {
            "medicamento": "Antib1 + Antib2 + Antib3",
            "sensivel": 0.9598165137614679,
            "i_c_max": 0.98177467826587,
            "i_c_min": 0.9344555596963487,
            "amostra": 101,
            "dosagem": 100
        }
    ]
}
```

