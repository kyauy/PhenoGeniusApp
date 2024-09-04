import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import ujson as json
import pickle as pk
from plotnine import *

# -- Set page config
apptitle = "PhenoGenius"

st.set_page_config(
    page_title=apptitle,
    page_icon=":genie:",
    layout="wide",
    initial_sidebar_state="auto",
)

# -- Set Sidebar
image_pg = Image.open("data/img/phenogenius.png")
st.sidebar.image(image_pg, caption=None, width=100)
st.sidebar.title("PhenoGenius")

st.sidebar.header(
    "Learning phenotypic patterns in genetic diseases by symptom interaction modeling"
)

st.sidebar.markdown(
    """
 This webapp presents symptom interaction models in genetic diseases to provide:
 - Standardized clinical descriptions 
 - Interpretable matches between symptoms and genes

 Code source is available in GitHub:
 [https://github.com/kyauy/PhenoGenius](https://github.com/kyauy/PhenoGenius)

 Last update: 2024-07-15

 PhenoGenius is a collaborative project from:
"""
)

image_uga = Image.open("data/img/logo-uga.png")
st.sidebar.image(image_uga, caption=None, width=95)

image_seqone = Image.open("data/img/logo-seqone.png")
st.sidebar.image(image_seqone, caption=None, width=95)

image_miai = Image.open("data/img/logoMIAI-rvb.png")
st.sidebar.image(image_miai, caption=None, width=95)

image_chuga = Image.open("data/img/logo-chuga.png")
st.sidebar.image(image_chuga, caption=None, width=60)


@st.cache_data(max_entries=50)
def convert_df(df):
    return df.to_csv(sep="\t").encode("utf-8")


@st.cache_data(max_entries=50)
def load_data():
    matrix = pd.read_csv(
        "data/resources/ohe_all_thesaurus_weighted_2024.tsv.gz",
        sep="\t",
        compression="gzip",
        index_col=0,
    )
    return matrix


@st.cache_data(hash_funcs={"Pickle": lambda _: None}, max_entries=50)
def load_nmf_model():
    with open("data/resources/pheno_NMF_390_model_42_2024.pkl", "rb") as pickle_file:
        pheno_NMF = pk.load(pickle_file)
    with open("data/resources/pheno_NMF_390_matrix_42_2024.pkl", "rb") as pickle_file:
        reduced = pk.load(pickle_file)
    return pheno_NMF, reduced


@st.cache_data(max_entries=50)
def symbol_to_id_to_dict():
    # from NCBI
    ncbi_df = pd.read_csv("data/resources/Homo_sapiens.gene_info.gz", sep="\t")
    ncbi_df = ncbi_df[ncbi_df["#tax_id"] == 9606]
    ncbi_df_ncbi = ncbi_df.set_index("Symbol")
    ncbi_to_dict_ncbi = ncbi_df_ncbi["GeneID"].to_dict()
    ncbi_df = ncbi_df.set_index("GeneID")
    ncbi_to_dict = ncbi_df["Symbol"].to_dict()
    return ncbi_to_dict_ncbi, ncbi_to_dict


@st.cache_data(hash_funcs={"_json.Scanner": hash}, max_entries=50)
def load_hp_ontology():
    with open("data/resources/hpo_obo_2024.json") as json_data:
        data_dict = json.load(json_data)
    return data_dict


@st.cache_data(max_entries=50)
def hpo_description_to_id():
    data_dict = {}
    for key, value in hp_onto.items():
        data_dict[value["name"]] = key
    return data_dict


@st.cache_data(max_entries=50)
def load_topic_data():
    topic = pd.read_csv(
        "data/resources/main_topics_hpo_390_42_filtered_norm_004_2024.tsv",
        sep="\t",
        index_col=0,
    )
    return topic


@st.cache_data(hash_funcs={"_json.Scanner": hash}, max_entries=50)
def load_similarity_dict():
    with open("data/resources/similarity_dict_threshold_80.json") as json_data:
        data_dict = json.load(json_data)
    return data_dict


def get_symbol(gene):
    if gene in symbol.keys():
        return symbol[gene]


def get_hpo_name(hpo):
    names = {}
    if hpo in hp_onto.keys():
        names[hpo] = hp_onto[hpo]["name"]
    return names


def get_hpo_name_only(hpo):
    if hpo in hp_onto.keys():
        return hp_onto[hpo]["name"]
    else:
        return None


def get_hpo_name_list(hpo_list, hp_onto):
    names = {}
    for hpo in hpo_list:
        if hpo in hp_onto.keys():
            names[hpo] = hp_onto[hpo]["name"]
    return names


def get_similar_terms(hpo_list, similarity_terms_dict):
    hpo_list_w_simi = {}
    for term in hpo_list:
        hpo_list_w_simi[term] = 1
        if term in similarity_terms_dict.keys():
            for key, value in similarity_terms_dict[term].items():
                if value > 0.8:
                    score = value / len(similarity_terms_dict[term].keys())
                    if key in hpo_list_w_simi.keys():
                        if score > hpo_list_w_simi[key]:
                            hpo_list_w_simi[key] = score
                        else:
                            pass
                    else:
                        hpo_list_w_simi[key] = score
    hpo_list_all = hpo_list_w_simi.keys()
    return hpo_list_w_simi, list(hpo_list_all)


def score(hpo_list, matrix):
    # Create a copy of the filtered matrix to avoid SettingWithCopyWarning
    matrix_filter = matrix[hpo_list].copy()

    # Use .loc to safely add or modify columns in the copy of the DataFrame
    matrix_filter.loc[:, "sum"] = matrix_filter.sum(axis=1)
    matrix_filter.loc[:, "gene_symbol"] = matrix_filter.index.to_series().apply(
        get_symbol
    )

    # Return the modified DataFrame sorted by 'sum'
    return matrix_filter.sort_values("sum", ascending=False)


def score_sim_add(hpo_list_add, matrix, sim_dict):
    # Ensure matrix_filter is a copy to avoid modifying the original DataFrame
    matrix_filter = matrix[hpo_list_add].copy()

    # Iterate through sim_dict to update matrix_filter values
    for key, value in sim_dict.items():
        if key in matrix_filter.columns:
            matrix_filter[key] = (
                matrix_filter[key] * value
            )  # Direct column assignment is fine here

    # Calculate the sum and assign gene_symbol, using direct assignment for these operations
    matrix_filter["sum"] = matrix_filter.sum(axis=1)
    matrix_filter["gene_symbol"] = matrix_filter.index.to_series().apply(get_symbol)

    # Return the DataFrame sorted by 'sum'
    return matrix_filter.sort_values("sum", ascending=False)


def get_phenotype_specificity(gene_diag, data_patient):
    rank = data_patient.loc[int(ncbi[gene_diag]), "rank"]
    max_rank = data_patient["rank"].max()
    if rank == max_rank:
        return "D - the reported phenotype is NOT consistent with what is expected for the gene/genomic region or not consistent in general."
    elif rank < 41:
        return "A - the reported phenotype is highly specific and relatively unique to the gene (top 40, 50 perc of diagnosis in PhenoGenius cohort)."
    elif rank < 250:
        return "B - the reported phenotype is consistent with the gene, is highly specific, but not necessarily unique to the gene (top 250, 75 perc of diagnosis in PhenoGenius cohort)."
    else:
        return "C - the phenotype is reported with limited association with the gene, not highly specific and/or with high genetic heterogeneity."


def get_relatives_list(hpo_list, hp_onto):
    all_list = []
    for hpo in hpo_list:
        all_list.append(hpo)
        if hpo in hp_onto.keys():
            for parent in hp_onto[hpo]["parents"]:
                all_list.append(parent)
            for children in hp_onto[hpo]["childrens"]:
                all_list.append(children)
    return list(set(all_list))


def get_hpo_id(hpo_list):
    hpo_id = []
    for description in hpo_list:
        hpo_id.append(hp_desc_id[description])
    return ",".join(hpo_id)


hp_onto = load_hp_ontology()
hp_desc_id = hpo_description_to_id()
ncbi, symbol = symbol_to_id_to_dict()


with st.form("my_form"):
    c1, c2 = st.columns(2)
    with c1:
        hpo_raw = st.multiselect(
            "Select interactively your HPOs or...",
            list(hp_desc_id.keys()),
            ["Renal cyst", "Hepatic cysts"],
        )
    with c2:
        hpo = st.text_input(
            "copy/paste your HPOs, separated with comma",
            "HP:0000107,HP:0001407",
        )
    gene_diag_input = st.multiselect(
        "Optional: provide HGNC gene symbol to be tested",
        options=list(ncbi.keys()),
        default=["PKD1"],
        max_selections=1,
    )
    submit_button = st.form_submit_button(
        label="Submit",
    )


if submit_button:
    if hpo_raw != ["Renal cyst", "Hepatic cysts"] and len(hpo_raw) > 0:
        hpo = get_hpo_id(hpo_raw)
    data = load_data()
    pheno_NMF, reduced = load_nmf_model()
    topic = load_topic_data()
    similarity_terms_dict = load_similarity_dict()

    hpo_list_ini = hpo.strip().split(",")

    if gene_diag_input:
        if gene_diag_input[0] in ncbi.keys():
            gene_diag = gene_diag_input[0]
        else:
            st.write(
                gene_diag_input
                + " gene are not in our database. Please check gene name (need to be in CAPITAL format)."
            )
            gene_diag = None
    else:
        gene_diag = None

    hpo_list_up = []
    for hpo in hpo_list_ini:
        if hpo in ["HP:0000001"]:
            pass
        elif len(hpo) != 10:
            st.write(
                "Incorrect HPO format: "
                + hpo
                + ". Please check (7-digits terms with prefix HP:, and separed by commas)."
            )
            pass
        elif hpo not in data.columns:
            pass
            st.write(hpo + " not available in current database. Please modify.")
        else:
            if data[hpo].astype(bool).sum(axis=0) != 0:
                hpo_list_up.append(hpo)
            else:
                hpo_to_test = hp_onto[hpo]["direct_parent"][0]
                while data[hpo_to_test].astype(bool).sum(
                    axis=0
                ) == 0 and hpo_to_test not in ["HP:0000001"]:
                    hpo_to_test = hp_onto[hpo_to_test]["direct_parent"][0]
                if hpo_to_test in ["HP:0000001"]:
                    st.write(
                        "No gene-HPO associations was found for "
                        + hpo
                        + " and parents."
                    )
                else:
                    hpo_list_up.append(hpo_to_test)
                    st.write(
                        "We replaced: ",
                        hpo,
                        " by ",
                        hp_onto[hpo]["direct_parent"][0],
                        "-",
                        get_hpo_name(hpo_to_test),
                    )
    hpo_list = list(set(hpo_list_up))
    del hpo_list_up

    if hpo_list:
        with st.expander("See HPO inputs"):
            st.write(get_hpo_name_list(hpo_list_ini, hp_onto))
            del hpo_list_ini

        hpo_list_name = get_relatives_list(hpo_list, hp_onto)

        st.header("Clinical description with symptom interaction modeling")

        witness = np.zeros(len(data.columns))
        witness_nmf = np.matmul(pheno_NMF.components_, witness)

        patient = np.zeros(len(data.columns))
        for hpo in hpo_list:
            hpo_index = list(data.columns).index(hpo)
            patient[hpo_index] = 1

        patient_nmf = np.matmul(pheno_NMF.components_, patient)

        witness_sugg_df = (
            pd.DataFrame(reduced)
            .set_index(data.index)
            .apply(lambda x: (x - witness_nmf) ** 2, axis=1)
        )
        patient_sugg_df = (
            pd.DataFrame(reduced)
            .set_index(data.index)
            .apply(lambda x: (x - patient_nmf) ** 2, axis=1)
        )

        case_sugg_df = (patient_sugg_df - witness_sugg_df).sum()

        patient_df_info = pd.DataFrame(case_sugg_df).merge(
            topic, left_index=True, right_index=True
        )

        patient_df_info["mean_score"] = round(
            patient_df_info[0] / (patient_df_info["total_weight"] ** 2), 4
        )

        patient_df_info_write = patient_df_info[
            ["mean_score", "main_term", "n_hpo", "hpo_name", "hpo_list", "weight"]
        ].sort_values("mean_score", ascending=False)

        del case_sugg_df
        del patient_sugg_df
        del witness_sugg_df
        del patient

        with st.expander("See projection in groups of symptoms dimension*"):
            st.dataframe(patient_df_info_write)
            st.write(
                "\* For interpretability, we report only the top 10% of the 390 groups of interacting symptom associations"
            )
            match_proj_csv = convert_df(patient_df_info_write)

            st.download_button(
                "Download description projection",
                match_proj_csv,
                "clin_desc_projected.tsv",
                "text/csv",
                key="download-csv-proj",
            )

        sim_dict, hpo_list_add = get_similar_terms(hpo_list, similarity_terms_dict)
        similar_list = list(set(hpo_list_add) - set(hpo_list))
        similar_list_desc = get_hpo_name_list(similar_list, hp_onto)

        if similar_list_desc:
            with st.expander("See symptoms with similarity > 80%"):
                similar_list_desc_df = pd.DataFrame.from_dict(
                    similar_list_desc, orient="index"
                )
                similar_list_desc_df.columns = ["description"]
                st.write(similar_list_desc_df)
                del similar_list_desc_df
        del similar_list
        del similar_list_desc

        st.header("Phenotype matching")
        results_sum = score(hpo_list, data)
        results_sum["matchs"] = results_sum[hpo_list].astype(bool).sum(axis=1)
        results_sum["score"] = results_sum["matchs"] + results_sum["sum"]
        results_sum["rank"] = (
            results_sum["score"].rank(ascending=False, method="max").astype(int)
        )
        cols = results_sum.columns.tolist()
        cols = cols[-4:] + cols[:-4]
        match = results_sum[cols].sort_values(by=["score"], ascending=False)
        st.dataframe(match[match["score"] > 1.01].drop(columns=["sum"]))
        match_csv = convert_df(match)

        st.download_button(
            "Download matching results",
            match_csv,
            "match.tsv",
            "text/csv",
            key="download-csv-match",
        )

        if gene_diag:
            if int(ncbi[gene_diag]) in results_sum.index:
                p = (
                    ggplot(match, aes("score"))
                    + geom_density()
                    + geom_vline(
                        xintercept=results_sum.loc[int(ncbi[gene_diag]), "score"],
                        linetype="dashed",
                        color="red",
                        size=1.5,
                    )
                    + ggtitle("Matching score distribution")
                    + xlab("Gene matching score")
                    + ylab("% of genes")
                    + theme_bw()
                    + theme(
                        text=element_text(size=12),
                        figure_size=(5, 5),
                        axis_ticks=element_line(colour="black", size=4),
                        axis_line=element_line(colour="black", size=2),
                        axis_text_x=element_text(angle=45, hjust=1),
                        axis_text_y=element_text(angle=60, hjust=1),
                        subplots_adjust={"wspace": 0.1},
                        legend_position=(0.7, 0.35),
                    )
                )
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.pyplot(ggplot.draw(p))

                st.write(
                    "Gene ID rank:",
                    results_sum.loc[int(ncbi[gene_diag]), "rank"],
                    "  |  ",
                    "Gene ID count:",
                    round(results_sum.loc[int(ncbi[gene_diag]), "sum"], 4),
                )
                st.write(results_sum.loc[[int(ncbi[gene_diag])]])
                st.write(
                    "Gene ID phenotype specificity:",
                    get_phenotype_specificity(gene_diag, results_sum),
                )
                del p

            else:
                st.write("Gene ID rank:", " Gene not available in PhenoGenius database")
        del results_sum
        del match

        st.header("Phenotype matching by similarity of symptoms")
        results_sum_add = score_sim_add(hpo_list_add, data, sim_dict)
        results_sum_add["rank"] = (
            results_sum_add["sum"].rank(ascending=False, method="max").astype(int)
        )
        cols = results_sum_add.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        match_sim = results_sum_add[cols].sort_values(by=["sum"], ascending=False)
        st.dataframe(match_sim[match_sim["sum"] > 0.01])

        match_sim_csv = convert_df(match_sim)

        st.download_button(
            "Download matching results",
            match_sim_csv,
            "match_sim.tsv",
            "text/csv",
            key="download-csv-match-sim",
        )

        if gene_diag:
            if int(ncbi[gene_diag]) in results_sum_add.index:
                p2 = (
                    ggplot(match_sim, aes("sum"))
                    + geom_density()
                    + geom_vline(
                        xintercept=results_sum_add.loc[int(ncbi[gene_diag]), "sum"],
                        linetype="dashed",
                        color="red",
                        size=1.5,
                    )
                    + ggtitle("Matching score distribution")
                    + xlab("Gene matching score")
                    + ylab("% of genes")
                    + theme_bw()
                    + theme(
                        text=element_text(size=12),
                        figure_size=(5, 5),
                        axis_ticks=element_line(colour="black", size=4),
                        axis_line=element_line(colour="black", size=2),
                        axis_text_x=element_text(angle=45, hjust=1),
                        axis_text_y=element_text(angle=60, hjust=1),
                        subplots_adjust={"wspace": 0.1},
                        legend_position=(0.7, 0.35),
                    )
                )
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.pyplot(ggplot.draw(p2))

                st.write(
                    "Gene ID rank:",
                    results_sum_add.loc[int(ncbi[gene_diag]), "rank"],
                    "  |  ",
                    "Gene ID count:",
                    round(results_sum_add.loc[int(ncbi[gene_diag]), "sum"], 4),
                )
                st.write(
                    "Gene ID phenotype specificity:",
                    get_phenotype_specificity(gene_diag, results_sum_add),
                )
                del p2

            else:
                st.write("Gene ID rank:", " Gene not available in PhenoGenius database")

        del sim_dict
        del hpo_list_add
        del results_sum_add
        del match_sim

        st.header("Phenotype matching by groups of symptoms")

        patient_df = (
            pd.DataFrame(reduced)
            .set_index(data.index)
            .apply(lambda x: sum((x - patient_nmf) ** 2), axis=1)
        )

        witness_df = (
            pd.DataFrame(reduced)
            .set_index(data.index)
            .apply(lambda x: sum((x - witness_nmf) ** 2), axis=1)
        )
        del patient_nmf
        del witness
        del witness_nmf

        case_df = pd.DataFrame(patient_df - witness_df)
        case_df.columns = ["score"]
        case_df["score_norm"] = abs(case_df["score"] - case_df["score"].max())
        # case_df["frequency"] = matrix_frequency["variant_number"]
        case_df["sum"] = case_df["score_norm"]  # + case_df["frequency"]
        case_df_sort = case_df.sort_values(by="sum", ascending=False)
        case_df_sort["rank"] = (
            case_df_sort["sum"].rank(ascending=False, method="max").astype(int)
        )
        case_df_sort["gene_symbol"] = case_df_sort.index.to_series().apply(get_symbol)
        match_nmf = case_df_sort[["gene_symbol", "rank", "sum"]]
        st.dataframe(match_nmf[match_nmf["sum"] > 0.01])

        match_nmf_csv = convert_df(match_nmf)

        st.download_button(
            "Download matching results",
            match_nmf_csv,
            "match_groups.tsv",
            "text/csv",
            key="download-csv-match-groups",
        )

        if gene_diag:
            if int(ncbi[gene_diag]) in case_df_sort.index:
                p3 = (
                    ggplot(match_nmf, aes("sum"))
                    + geom_density()
                    + geom_vline(
                        xintercept=case_df_sort.loc[int(ncbi[gene_diag]), "sum"],
                        linetype="dashed",
                        color="red",
                        size=1.5,
                    )
                    + ggtitle("Matching score distribution")
                    + xlab("Gene matching score")
                    + ylab("% of genes")
                    + theme_bw()
                    + theme(
                        text=element_text(size=12),
                        figure_size=(5, 5),
                        axis_ticks=element_line(colour="black", size=4),
                        axis_line=element_line(colour="black", size=2),
                        axis_text_x=element_text(angle=45, hjust=1),
                        axis_text_y=element_text(angle=60, hjust=1),
                        subplots_adjust={"wspace": 0.1},
                        legend_position=(0.7, 0.35),
                    )
                )
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.pyplot(ggplot.draw(p3))

                st.write(
                    "Gene ID rank:",
                    case_df_sort.loc[int(ncbi[gene_diag]), "rank"],
                    "  |  ",
                    "Gene ID count:",
                    round(case_df_sort.loc[int(ncbi[gene_diag]), "sum"], 4),
                )
                st.write(
                    "Gene ID phenotype specificity:",
                    get_phenotype_specificity(gene_diag, case_df_sort),
                )
                del p3
            else:
                st.write("Gene ID rank:", " Gene not available in PhenoGenius database")
            del case_df_sort
            del match_nmf
            del case_df

    else:
        st.write(
            "No HPO terms provided in correct format.",
        )
