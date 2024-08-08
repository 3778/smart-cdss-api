import pandas as pd
import joblib
import json
import os
from unidecode import unidecode

from smart_cdss_api.conf import conf

min_sample = 30
min_critical_sample = 100

df_data = None
df_sheets = None
map_institution = None


def get_min_sample():
    return min_sample


def set_min_sample(new_val):
    global min_sample
    min_sample = new_val


def download():
     # Make Paths
    os.system(conf.sheets_path_base_mk)

    data_path_s3 = conf.data_path[len(conf.base_path):]
    xlsx_path_s3 = conf.xlsx_path[len(conf.base_path):]
    map_institution_path_s3 = conf.map_institution_path[len(conf.base_path):]

    # Download Data
    if not os.path.isfile(conf.data_path):
        conf.s3.download_file(data_path_s3, conf.data_path)
    # Download Sheets
    if not os.path.isfile(conf.xlsx_path):
        conf.s3.download_file(xlsx_path_s3, conf.xlsx_path)
    if not os.path.isfile(conf.map_institution_path):
        conf.s3.download_file(map_institution_path_s3, conf.map_institution_path)

    global df_data
    df_data = pd.read_csv(conf.data_path, sep='\t', dtype=object) 

    global df_sheets
    df_sheets = pd.ExcelFile(conf.xlsx_path)

    global map_institution
    map_institution = pd.read_csv(conf.map_institution_path, sep=',', dtype=str)
    

def load_data(model_index):
    df = (
        df_data
        .drop(conf.todrop_cols, axis=1)
        [
            [conf.opt_institution]
            + conf.model_xcols[model_index]
            + [conf.ycol]
        ]
    )
    X = df.copy()
    y = X.pop(conf.ycol)
    return df, X, y


def load_data_id(model_index):
    df = (
        df_data
        .drop(conf.todrop_cols[1:], axis=1)
        [[conf.todrop_cols[0]]
         + conf.model_xcols[model_index] + [conf.ycol]]
    )
    X = df.copy()
    y = X.pop(conf.ycol)
    return df, X, y


def get_parameters(json_file):
    json_values = pd.json_normalize(json_file, max_level=0).iloc[0]
    selected_options = {}
    # Load Data
    df, X, _ = load_data(2)

    if json_values['filtro']:
        selected_options = pd.json_normalize(json_file["filtro"], max_level=0).iloc[0]

        # Not apply restrictions
        if conf.opt_rest in selected_options.index:
            selected_options.pop(conf.opt_rest)

        # Change sitio values
        if conf.opt_sitio in selected_options.index:
            selected_options = map_sitio(selected_options)

        # Remove sepse filter 
        if conf.opt_sepse in selected_options.index:
            selected_options.pop(conf.opt_sepse)

        # Pass Default values of Json to Dic
        _selected_options = {}
        for key, value in selected_options.items():
            if key in conf.values_columns.keys():
                key = conf.values_columns[key]
            if key in conf.optional_values_columns.keys():
                key = conf.optional_values_columns[key]

            _selected_options[key] = value 
        selected_options = _selected_options


    parameter = json_values["parametro"]
    # If filter in map_institution
    if parameter in conf.optional_values_columns.keys():
        if parameter != 'instituicao':
            parameter = conf.optional_values_columns[parameter]
        else:
            parameter = conf.opt_institution_map

        mask = pd.Series(index=map_institution.index, data=True)
        if conf.opt_state in selected_options.keys():
            if selected_options[conf.opt_state]:
                mask = map_institution[conf.opt_state] == selected_options[conf.opt_state]

        if conf.opt_city in selected_options.keys():
            if selected_options[conf.opt_city]:
                mask = map_institution[conf.opt_city] == selected_options[conf.opt_city]

        return list(
            map_institution.loc[
                mask,
                parameter
            ].unique()
        )


    parameter_col = parameter
    if parameter in conf.values_columns.keys():
        parameter_col = conf.values_columns[parameter]

    df_f = apply_filter(df, selected_options)
    valid_values = list(df_f[parameter_col].unique())
    if parameter in conf.values.keys():
        reverse_values = {v:k for k, v in conf.values[parameter].items()}
        valid_values = [reverse_values[val] for val in valid_values]

    # Get valid sitios maps
    if parameter == conf.xlsx_sitio_col:
        df_sitios = load_map_sitio()
        valid_values = list(
            df_sitios.loc[
                df_sitios[conf.opt_sitio].isin(valid_values),
                conf.xlsx_sitio_col
            ]
            .unique()
        )

    return valid_values


def load_options():
    df, _, _ = load_data(2)
    options = {}
    for c in df.columns:
        if c == conf.ycol:
            continue
        options[c] = list(df[c].unique())
    combines_group = {}
    combines_family = {}
    for g in df[conf.opt_group].unique():
        combines_group[g] = (
            [None] + list(
                df[df[conf.opt_group] == g][conf.opt_family].unique()
            )
        )
        for f in combines_group[g]:
            combines_family[f] = (
                [None] + list(
                    df[df[conf.opt_family] == f][conf.opt_micro].unique()
                )
            )

    return options, combines_group, combines_family


def load_surrogates():
    surrogates = (
        pd.read_excel(df_sheets, sheet_name=conf.xlsx_surrogates)
        .dropna(how='all')
        .set_index(conf.antib_col)
    )
    surrogates.index = (
        surrogates.index
        .map(unidecode)
        .map(str.lower)
    )
    return surrogates


def load_restrictions():
    restrictions = (
        pd.read_excel(df_sheets, sheet_name=conf.xlsx_restrictions)
        .dropna(how='all')
        .drop([conf.xlsx_restrictions_drop], axis=1)
        .set_index(conf.antib_col)
    )
    restrictions.index = (
        restrictions.index
        .map(unidecode)
        .map(str.lower)
    )
    return restrictions


def load_map_sitio():
    df_sitios = (
        pd.read_excel(df_sheets,
                      sheet_name=conf.xlsx_sitio)
        .fillna(method='ffill')
    )
    return df_sitios


def load_dosage():
    df_dosage = (
        pd.read_excel(df_sheets,
                      sheet_name=conf.xlsx_dosage,
                      header=[0,1,2])
        .fillna("")
    )
    df_dosage = df_dosage.drop([df_dosage.columns[0]], axis=1)
    df_dosage = df_dosage.set_index(df_dosage.columns[0])

    df_dosage.index.name = conf.antib_col
    df_dosage.index = (
        df_dosage.index
        .map(unidecode)
        .map(str.lower)
    )
    return df_dosage


def load_group():
    df_group = (
        pd.read_excel(df_sheets,
                      sheet_name=conf.xlsx_group)
        .fillna(method='ffill')
        .set_index(conf.antib_col)
    )
    df_group.index = (
        df_group.index
        .map(unidecode)
        .map(str.lower)
    )
    return df_group


def read_json(json_file):
    values = pd.json_normalize(json_file, max_level=0).iloc[0]

    # Pass Default values of Json to Dic
    selected_options = {}
    for key in conf.values_columns:
        val = values[key]
        if key in conf.values.keys():
            val = conf.values[key][val]

        selected_options[conf.values_columns[key]] = val

    for key in conf.optional_values_columns.keys():
        if key in values.index:
            val = values[key]
            if val:
                key = conf.optional_values_columns[key]
                selected_options[key] = val

    # Make Restrictions
    selected_restrictions = make_restrictions(values)

    # Verify Sitio
    selected_options = map_sitio(selected_options)

    # Add Sepse risk to selected_options
    selected_options[conf.opt_sepse] = values[conf.opt_sepse]

    # Model Selection
    model_index = 2
    if not selected_options[conf.opt_micro]:
        model_index = 1
        del selected_options[conf.opt_micro]
    if not selected_options[conf.opt_family]:
        if model_index == 2 and selected_options[conf.opt_micro]:
            selected_options[conf.opt_family] = (
                list(
                    df_data.loc[
                        df_data[conf.opt_micro] == selected_options[conf.opt_micro],
                        conf.opt_family
                    ]
                    .unique()
                )
                [0]
            )
        else:
            model_index = 0
        del selected_options[conf.opt_family]
    if not selected_options[conf.opt_group]:
        model_index = 0
        del selected_options[conf.opt_group]

    return (model_index, selected_options, selected_restrictions)


def make_restrictions(values):
    selected_restrictions = []
    for key in conf.implicity_restrictions.keys():
        val = values[key]
        if val in conf.implicity_restrictions[key].keys():
            selected_restrictions.append(conf.implicity_restrictions[key][val])

    for rest in values[conf.opt_rest]:
        if rest == conf.opt_rest_fr:
            val = values[conf.opt_rest][rest]
            if val is not None:
                val = (val
                       .replace('-', " ")
                       .title()
                       .replace(" ", "-")
                )
                val = "F.R. " + val
                selected_restrictions.append(val)

        elif rest == conf.opt_rest_va:
            val = values[conf.opt_rest][rest]
            if val is not None:
                val = "V.A. " + val.title()
                selected_restrictions.append(val)

        elif values[conf.opt_rest][rest]:
            val = rest.replace('_', " ").title()
            selected_restrictions.append(val)

    return selected_restrictions


def map_sitio(selected_options):
    respost = None

    df_sitios = load_map_sitio()
    material_sitio = (
        df_sitios[(df_sitios[conf.xlsx_sitio_col]
                   == selected_options[conf.opt_sitio])]
        [conf.opt_sitio]
        .values
    )

    selected_options[conf.opt_sitio] = list(material_sitio)
    respost = selected_options

    return respost


def select_antibiotics(df):
    df = (
        df
        .assign(target=lambda x: x[conf.ycol] == conf.ylabel)
        .groupby(conf.antib_col)
        ['target']
        .agg(['mean', 'count'])
        .sort_values(by='count', ascending=False))
    # Remove Antibiotics with less samples
    df = df[~(df['count'] < min_sample)]
    return df


def select_surrogate(df, surrogates):
    df_surrogate = pd.DataFrame(columns=[conf.prob_nb_col,
                                         conf.mean_col,
                                         conf.count_col])
    for antib in df.index:
        antib_ul = unidecode(antib.lower())
        if antib_ul in surrogates.index:
            # Pick base values of bs3
            prob_nb = float(df.loc[[antib]][conf.prob_nb_col])
            mean = float(df.loc[[antib]][conf.mean_col])
            count = int(df.loc[[antib]][conf.count_col])

            # Pick surrogates of antibiotic
            surT = surrogates.loc[[antib_ul]].T.dropna().set_index([antib_ul])

            # Copy informations to surrogate
            surT[conf.prob_nb_col] = prob_nb
            surT[conf.mean_col] = mean
            surT[conf.count_col] = count

            df_surrogate = df_surrogate.append(surT)
    return df_surrogate


def apply_filter(df, selected_options):

    df, selected_options = apply_location_filter(df, selected_options)

    for opt in selected_options.keys():
        if opt == conf.opt_age:
            age_value = [selected_options[opt]]
            if selected_options[opt] in conf.aggregation_age.keys():
                age_value = conf.aggregation_age[selected_options[opt]]
            df = df[(df[opt].isin(age_value))]
        elif opt == conf.opt_sitio:
            df = df[(df[opt].isin(selected_options[opt]))]
        elif opt == conf.opt_sex:
            join_sex = True
            for sitio in selected_options[conf.opt_sitio]:
                if sitio in conf.exclude_sitio_in_aggregation_sex:
                    join_sex = False
                    break
            if not join_sex:
                df = df[(df[opt] == selected_options[opt])]
        else:
            df = df[(df[opt] == selected_options[opt])]
    return df


def apply_location_filter(df, selected_options):
    filter_institutes = []
    if conf.opt_institution in selected_options.keys():
        institution = selected_options.pop(conf.opt_institution)
        if institution:
            filter_institutes = list(
                map_institution.loc[
                    map_institution[conf.opt_institution_map] == institution,
                    conf.opt_institution_map
                ]
                .unique()
            )

    if conf.opt_city in selected_options.keys():
        city = selected_options.pop(conf.opt_city)
        if city and (not filter_institutes):
            filter_institutes = list(
                map_institution.loc[
                    map_institution[conf.opt_city] == city,
                    conf.opt_institution_map
                ]
                .unique()
            )

    if conf.opt_state in selected_options.keys():
        state = selected_options.pop(conf.opt_state)
        if state and (not filter_institutes):
            filter_institutes = list(
                map_institution.loc[
                    map_institution[conf.opt_state] == state,
                    conf.opt_institution_map
                ]
                .unique()
            )
    
    if filter_institutes:
        df = df.loc[df[conf.opt_institution].isin(filter_institutes)]
    
    return df, selected_options


def apply_restriction(df, restrictions, selected_restrictions):
    for antib in df.index:
        for rest in selected_restrictions:
            # Pick value of restiction
            val = restrictions.loc[[unidecode(antib.lower())], [rest]].values[0]
            # Apply restriction to probability of antibiotic
            df.loc[[antib], [conf.prob_nb_col]] *= float(val)
    return df


def apply_trusted_interval(df):
    df_interval = pd.DataFrame(columns=[conf.interval_max_col,
                                        conf.interval_min_col])
    for antib in df.index:
        # Values in df to calc
        value = float(df.loc[antib, conf.prob_nb_col])  # D
        count_val = int(df.loc[antib, conf.count_col])  # E
        # Calc values of min and max interval
        base = 1.96*(value*(1-value)/count_val)**0.5
        min_value = value - base
        max_value = value + base

        # Make in interval [0,1]
        if min_value < 0:
            min_value = 0
        if max_value > 1:
            max_value = 1
        # Apply in df
        df_interval.loc[antib] = [max_value, min_value]
    return df.join(df_interval)


def apply_dosage(df, selected_options):
    # Picking Dosage
    dosage_age = conf.dosage_age_map[selected_options[conf.cols_in_models[0]]]
    # Route of Administration
    restrictions = load_restrictions()
    df_dosage = load_dosage()

    df[conf.dosage_col] = [{}] * len(df)
    df[conf.dosage_admin_col] = [{}] * len(df)
    df[conf.dosage_freq_col] = [{}] * len(df)
    df[conf.dosage_rest_col] = [""] * len(df)
    for antib in df.index:
        dosage = {conf.vals_rest_va[1]: None,
                   conf.vals_rest_va[2]: None
                 }

        administration = {conf.vals_rest_va[1]: False,
                          conf.vals_rest_va[2]: False}
        frequency = {conf.vals_rest_va[1]: None,
                     conf.vals_rest_va[2]: None}

        for key in administration.keys():
            route_adm = key.title()
            val = restrictions.loc[[unidecode(antib.lower())], ["V.A. " + route_adm]].values[0]
            if val == 1:
                antib_ul = unidecode(antib.lower())
                dosage[key] = df_dosage.loc[antib_ul,
                                            (dosage_age, route_adm, conf.dosage_col)]
                administration[key] = True
                frequency[key] = df_dosage.loc[antib_ul,
                                               (dosage_age, route_adm, conf.dosage_freq_col)]
        dosage_restriction = df_dosage.loc[antib_ul,
                                           (dosage_age, route_adm, conf.dosage_rest_col)]

        df.loc[[antib], [conf.dosage_col]] = [dosage]
        df.loc[[antib], [conf.dosage_admin_col]] = [administration]
        df.loc[[antib], [conf.dosage_freq_col]] = [frequency]
        df.loc[[antib], [conf.dosage_rest_col]] = dosage_restriction
    return df


def apply_in_model(df_amb_filt, df, X,
                   selected_options, selection_antib):
    out = []

    vals = X[conf.opt_group].unique()

    # Porcent of GRAMs in filtered base
    gram_porcent = df_amb_filt[conf.opt_group].value_counts(normalize=True)

    for antib in selection_antib.index:
        # Apply Probability with GRAM compensate
        values = selection_antib.loc[[antib]]
        prob_nb = None

        # Verify if is Simple (= NaN)
        if conf.opt_group not in selected_options.keys():
            # ====Applying in Mean NB====
            df_a = df_amb_filt.copy()
            # Appling Antibiotic filter to Ambul. Filtered Base
            df_a = df_a[df_a[conf.antib_col] == antib]

            # Piking Porcent of GRAMs Sensivel in Antibotic
            antsen_porcent = (
                df_a
                .assign(target=lambda x: x[conf.ycol] == conf.ylabel)
                .groupby(conf.opt_group)
                ['target']
                .agg(['mean'])
            )

            # Make ponderation for GRAMs in this antibiotic
            prob_nb = 0
            for gram in antsen_porcent.index:
                prob_nb += (
                    antsen_porcent.loc[gram]['mean'] * gram_porcent[gram]
                )

        else:
            prob_nb = values['mean'][0]

        mean = values['mean'][0]
        count = values['count'][0]

        out.append((antib, prob_nb, mean, count))
    return (pd.DataFrame(out, columns=[conf.antib_col,
                                       conf.prob_nb_col,
                                       conf.mean_col,
                                       conf.count_col])
            .set_index([conf.antib_col])
            .sort_values(by=conf.prob_nb_col, ascending=False))


def apply_df_refine(df, selected_restrictions):
    # Apply Restrictios
    if selected_restrictions:
        restrictions = load_restrictions()
        df = apply_restriction(df,
                               restrictions,
                               selected_restrictions)
        # Remove Prob == 0
        df = df[df[conf.prob_nb_col] > 0]
    # df = apply_trusted_interval(df)

    return df


def application_in_model(data):
    (selected_options, selected_restrictions,
     surrogates, df_filter, df, X) = data

    # Pick Prob for Antibiotic
    selection_antib = select_antibiotics(df_filter)
    df_prob = apply_in_model(df_filter, df, X,
                             selected_options, selection_antib)

    # Apply Surrogate
    df_surrogate = select_surrogate(df_prob, surrogates)
    df_ret = df_prob.append(df_surrogate)
    df_ret = apply_df_refine(df_ret, selected_restrictions)

    df_ret = df_ret.sort_values(by=conf.prob_nb_col, ascending=False)

    return df_ret


def apply_sepse_correlation(data, model_index, qt_correlation):
    (selected_options, selected_restrictions,
     surrogates, df_filter, df, X) = data

    df_id, _, _ = load_data_id(model_index)
    df_group = load_group()
    df_group_col = df_group.columns[0]
    first_returns = []
    id_col = conf.todrop_cols[0]
    val_ponderate = 1
    for i in range(0, qt_correlation):
        # Aply in model
        df = df_id.drop([id_col], axis=1)
        X = df.copy()
        X.pop(conf.ycol)
        df_filter = apply_filter(df, selected_options)
        data = (selected_options, selected_restrictions,
                surrogates, df_filter, df, X)
        df_run = application_in_model(data)
        # Make mask to pick ids
        if not df_run.empty:
            # Remove group antib
            if not first_returns:
                best_antib = df_run.iloc[[0]].copy()
            else:
                for antib_index in list(df_run.index):
                    best_antib = df_run.loc[[antib_index]].copy()
                    best_group = df_group.loc[unidecode(best_antib.index[0].lower()),
                                              df_group_col]
                    select = True
                    for antib_row in first_returns:
                        antib = antib_row.index[0]
                        antib_group = df_group.loc[unidecode(antib.lower()), df_group_col]
                        if best_group == antib_group:
                            select = False
                            break

                    if select:
                        break

            # Make Ponderation
            new_prob = best_antib[conf.prob_nb_col][0] * val_ponderate
            new_mean = best_antib[conf.mean_col][0] * val_ponderate
            best_antib[conf.prob_nb_col] = new_prob
            best_antib[conf.mean_col] = new_mean
            val_ponderate -= new_prob
            # Pick Ids
            mask1 = df_id[conf.antib_col] == best_antib.index[0]
            mask2 = df_id[conf.ycol] == conf.ylabel
            mask = mask1 & mask2
            ids = df_id[mask][id_col].values
            # Remove pacient ids from dataframe
            df_id = df_id[~(df_id[id_col].isin(ids))]
            # Add to list
            first_returns.append(best_antib)
        else:
            # Just to pick the structure
            if not first_returns:
                first_returns.append(df_run.copy())
            break
    df_return = (
        pd
        .DataFrame(
            [],
            columns=[conf.antib_col, conf.count_col]
        )
        .set_index([conf.antib_col])
    )
    df_return = pd.concat([df_return]+first_returns)
    return df_return


def make_json_out(df):
    if not df.empty:
        df.reset_index(inplace=True)
        df.rename(lambda s: s.replace('.','_').replace(" ","").lower(),
                  axis='columns', inplace=True)
        df.rename(columns={'index': conf.opt_json_medic}, inplace=True)
        json_df = df.to_dict('records')
        msg = None
    else:
        json_df = []
        msg = conf.val_json_msg_error

    ret_json = {conf.opt_json_min_critical_sample: min_critical_sample,
                conf.opt_json_database_size: df_data.shape[0],
                conf.opt_json_msg: msg,
                conf.opt_json_antibiotico: json_df} 

    return ret_json


def application(json_file):
    data = read_json(json_file)

    model_index, selected_options, selected_restrictions = data

    # Pikking Sepse Risk
    sepse_risk = selected_options[conf.opt_sepse]
    del selected_options[conf.opt_sepse]

    # Load Data
    df, X, _ = load_data(model_index)
    df_filter = apply_filter(df, selected_options)
    surrogates = load_surrogates()

    # Make data
    data = (selected_options, selected_restrictions,
            surrogates, df_filter, df, X)

    df_return = None
    if sepse_risk == conf.sepse_risk[0]:
        # Sepse Risk is Low
        df_return = application_in_model(data)

    elif sepse_risk == conf.sepse_risk[1]:
        # Sepse Risk is Moderate
        df_return = apply_sepse_correlation(data, model_index, 2)

    elif sepse_risk == conf.sepse_risk[2]:
        # Sepse Risk is High
        df_return = apply_sepse_correlation(data, model_index, 3)

    # Apply Trusted Interval
    df_return = apply_trusted_interval(df_return)

    # Apply Dosage
    df_return = apply_dosage(df_return, selected_options)

    # Ascending Data Frame
    df_return = df_return.sort_values(by=conf.prob_nb_col, ascending=False)

    # Remove Mean Col
    df_return.drop([conf.mean_col], axis=1, inplace=True)

    # Reorder Columns
    df_return = df_return[[conf.prob_nb_col,
                           conf.interval_max_col,
                           conf.interval_min_col,
                           conf.count_col,
                           conf.dosage_col,
                           conf.dosage_admin_col,
                           conf.dosage_freq_col,
                           conf.dosage_rest_col,
                           ]]

    # Make Json Return
    ret_json = make_json_out(df_return)
    return ret_json


def verify_request(json_file, all_fields=True):

    def load_values_json():
        df, _, _ = load_data(2)
        df = df[conf.cols_in_models[4:7]]
        options = {}
        for c in df.columns:
            options[c.lower()] = list(df[c].unique())
        return options

    def verify_location(field, value):
        if not value:
            return True
        col = conf.opt_institution_map
        if field != 'instituicao':
            col = conf.optional_values_columns[field]

        return value in list(map_institution[col].unique())

    def verify_subdivisao_sitio(value):
        df_sitio = load_map_sitio()
        return value in list(df_sitio[conf.xlsx_sitio_col].unique())

    def verify_funcao_renal(value):
        return value in conf.vals_rest_fr

    def verify_via_administracao(value):
        return value in conf.vals_rest_va

    def verify_restrictions_poss(value):
        return isinstance(value, bool)

    def _verify_request(json_file):
        required_fields_1st_level = set(
            list(conf.values_columns.keys()) +
            [conf.opt_sepse, conf.opt_rest]
        )
        # FIXME when need to use the new fields, then change to required
        if all_fields:
            assert (
                set(
                    [ False 
                        for field in required_fields_1st_level
                        if field not in set(json_file.keys())
                    ]
                ) == set()
            )

        required_fields_2nd_level = set(
            conf.restrictions_poss +
            [conf.opt_rest_va, conf.opt_rest_fr]
        )
        if all_fields:
            assert (
                required_fields_2nd_level == set(json_file['restricoes'].keys())
            )

        options = load_values_json()

        for field in json_file.keys():
            value = json_file[field]
            if field in conf.optional_values_columns.keys():
                assert (
                    verify_location(field, value)
                )
            elif field in conf.values:
                assert (
                    value in conf.values[field].keys()
                )
            elif field == conf.xlsx_sitio_col:
                assert (
                    verify_subdivisao_sitio(value)
                )
            elif field in options.keys():
                assert (
                    (value in options[field]
                     or value == None)
                )
            elif field == conf.opt_sepse:
                assert (
                    value in conf.sepse_risk
                )
            elif field == conf.opt_rest:
                for subfield in json_file[field]:
                    value = json_file[field][subfield]
                    if subfield in conf.restrictions_poss:
                        assert (
                            verify_restrictions_poss(value)
                        )
                    if subfield == conf.opt_rest_va:
                        assert (
                            verify_via_administracao(value)
                        )
                    if subfield == conf.opt_rest_fr:
                        assert (
                            verify_funcao_renal(value)
                        )

    try:
        _verify_request(json_file)
    except AssertionError:
        return False
    return True


def validate_token(token):
    return token == conf.secret_token


def validate_ui_token(token):
    return token == conf.ui_secret_token
