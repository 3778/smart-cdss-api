import boto3
import os


secret_token = os.getenv('SMARTCDSS_SECRET_TOKEN', None)
ui_secret_token = os.getenv('UI_SMARTCDSS_SECRET_TOKEN', None)

# Paths
bucket = os.getenv('SMARTCDSS_BUCKET', None)
s3 = boto3.resource('s3').Bucket(bucket)
base_path = 'smart_cdss_api/api/'
sheets_path_base_mk = "mkdir -p " + base_path + "sheets/"
xlsx_path = base_path + 'sheets/Restricoes_e_Surrogates.xlsx'
data_path = base_path + 'dados_tratados.csv'
ibge_path = base_path + 'sheets/ibge_uf_municipio.csv'
institution_path = base_path + 'sheets/brglass_instituicoes.csv'
map_institution_path = base_path + 'sheets/map_uf_municipio_instituicao.csv'

data_url = f's3://{bucket}/dados_tratados.parq'
xlsx_url = f's3://{bucket}/sheets/Restricoes_e_Surrogates.xlsx'
ibge_url = f's3://{bucket}/sheets/ibge_uf_municipio.csv'
institution_url = f's3://{bucket}/sheets/brglass_instituicoes.csv'
map_institution_url = f's3://{bucket}/sheets/map_uf_municipio_instituicao.csv'

# Columns
todrop_cols = ['ID_Paciente', 'Idade', 'ID_Micro', 'ID_Antib']
cols_in_models = ['Idade categ.', 'Sexo', 'Atendimento',
                  'Material isolado', 'Grupo', 'Familia',
                  'Microrganismo', 'Antibiotico']

model_xcols = [cols_in_models[:-3] + [cols_in_models[-1]],
               cols_in_models[:-2] + [cols_in_models[-1]],
               cols_in_models]
location_cols = [
    "estabelecimento_sigla_estado",
    "estabelecimento_municipio",
    "estabelecimento_nome",        
]

antib_col = model_xcols[2][7]
prob_nb_col = 'Sensivel'
mean_col = "Mean"
count_col = "Amostra"
interval_min_col = "I.C. Min"
interval_max_col = "I.C. Max"
dosage_col = "Dosagem"
dosage_admin_col = "Administracao"
dosage_freq_col = "Frequencia"
dosage_rest_col = "Restricoes"
ycol = 'Resultado'
ylabel = 'Sensível'

# Constants
xlsx_surrogates = 'Surrogates'
xlsx_restrictions = 'Restricoes'
xlsx_restrictions_drop = 'ID_Antib'
xlsx_sitio = 'Sitio'
xlsx_sitio_col = 'subdivisao_sitio'
xlsx_group = 'Grupo'
xlsx_dosage = 'Dosagem'


opt_state = "estabelecimento_sigla_estado"
opt_city = "estabelecimento_municipio"
opt_institution_map = "estabelecimento_nome"
opt_institution = 'Estabelecimento'
opt_age = cols_in_models[0]
opt_sex = cols_in_models[1]
opt_sitio = cols_in_models[3]
opt_group = cols_in_models[4]
opt_family = cols_in_models[5]
opt_micro = cols_in_models[6]
opt_rest = 'restricoes'
opt_sepse = 'sepse'
opt_rest_fr = 'funcao_renal'
opt_rest_va = 'via_de_administracao'
opt_attend = cols_in_models[2]

# Return Json
opt_json_min_critical_sample = "n_critico"
opt_json_database_size = "amostras_banco"
opt_json_msg = "mensagem"
opt_json_antibiotico = "antibioticos"
opt_json_medic = "medicamento"

val_json_msg_error = "Ainda não possuímos dados suficientes para essa busca."

sepse_risk = ["baixo", "moderado", "alto"]
vals_rest_fr = [None, "normal", "leve-mod", "mod-grave", "grave", "falencia"]
vals_rest_va = [None, 'oral', 'parenteral']
group_grams = ["gram_negativo", "gram_positivo"]
attend_vals = ["Ambulatorial", "Hospitalar"]

# Implicity Restrictions
implicity_restrictions = {
    "idade": {
        "recem_nascido": "Recem Nascido",
        "lactente": "Recem Nascido",
        "crianca": "Crianca",
        "idoso": "Idoso"
    },
    "atendimento": {
        "comunitario": "Classificacao"
    },
    #"subdivisao_sitio": {
    #    "pielonefrite": "V.A. Parenteral"
    #},
}

restrictions_poss = [
    "diabetico", "imunossupressao", "gestante", "lactante",
    "nao_cf", "nao_pen"
]

# Dosage configs
dosage_age_map = {
    "1. Recém-nascido": "Crianca",
    "2. Lactente": "Crianca",
    "3. Criança": "Crianca",
    "4. Adolescente": "Adulto",
    "5. Adulto": "Adulto",
    "6. Idoso": "Adulto"
}


# Values of Json
values_columns = {
    "idade": cols_in_models[0],
    "sexo": cols_in_models[1],
    "atendimento": cols_in_models[2],
    "subdivisao_sitio": cols_in_models[3],
    "grupo": cols_in_models[4],
    "familia": cols_in_models[5],
    "microrganismo": cols_in_models[6],
}

optional_values_columns = {
    "uf": opt_state,
    "municipio": opt_city,
    "instituicao": opt_institution
}

values = {
    "idade": {
        "recem_nascido": "1. Recém-nascido",
        "lactente": "2. Lactente",
        "crianca": "3. Criança",
        "adolescente": "4. Adolescente",
        "adulto": "5. Adulto",
        "idoso": "6. Idoso"
    },

    "sexo": {
        "masculino": "Masculino",
        "feminino": "Feminino"
    },

    "atendimento": {
        "comunitario": "Ambulatorial",
        "hospitalar": "Hospitalar"
    }
}


# Aggregation age
aggregation_age = {
    "4. Adolescente": ["4. Adolescente", "5. Adulto"],
    "5. Adulto": ["4. Adolescente", "5. Adulto"]
}

# Exclude sitio in aggregation sex
exclude_sitio_in_aggregation_sex = [
    'Secreção Vaginal',
    'Secreção Uretral',
    'Raspado Uretral',
    'Urina'
]

