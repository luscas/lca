import pandas as pd
import numpy as np
import streamlit as st

from utils.emission_factors import get_emission_factor


class Industrial:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.gwp_factors = pd.read_excel("data/lca/gwp_kyoto.xlsx")

    def process(self):
        self.df["Quantidade"] = self.df["Quantidade"].fillna(0)

        self.df["Fonte do Fator de Emissão"] = self.df[
            "Nome no Estudo (Ecoinvent)"
        ].apply(
            lambda x: (
                get_emission_factor(x, "source")
                if get_emission_factor(x, "source")
                else "Não encontrado"
            )
        )

        self.df["Fator de Emissão Fóssil"] = self.df[
            "Nome no Estudo (Ecoinvent)"
        ].apply(lambda x: get_emission_factor(x, "fossil_emission_factor"))

        self.df["Fator de Emissão Biogênico"] = self.df[
            "Nome no Estudo (Ecoinvent)"
        ].apply(lambda x: get_emission_factor(x, "biogenic_emission_factor"))

        self.df["Fator de Remoção Biogênica"] = self.df[
            "Nome no Estudo (Ecoinvent)"
        ].apply(lambda x: get_emission_factor(x, "biogenic_removal_factor"))

        self.df["Fator de Emissão LUC"] = self.df["Nome no Estudo (Ecoinvent)"].apply(
            lambda x: get_emission_factor(x, "luc_emission_factor")
        )

        self.df["Unidade - Fator"] = self.df["Nome no Estudo (Ecoinvent)"].apply(
            lambda x: get_emission_factor(x, "unit")
        )

        self.df["Emissões Fósseis (tCO2e)"] = (
            self.df["Quantidade"] * self.df["Fator de Emissão Fóssil"]
        )

        self.df["Emissões Biogênicas (tCO2e)"] = (
            self.df["Quantidade"] * self.df["Fator de Emissão Biogênico"]
        )

        self.df["Remoções biogênicas (tCO2e)"] = (
            self.df["Quantidade"] * self.df["Fator de Remoção Biogênica"]
        )

        self.df["Emissões LUC (tCO2e)"] = (
            self.df["Quantidade"] * self.df["Fator de Emissão LUC"]
        )

        return self.df


def test_industrial():
    def highlight_empty_factor(row):
        """Highlight the entire row in red if `Unidade - Fator` is NaN."""
        if pd.isna(row["Unidade - Fator"]):
            return ["background-color: #D2665A"] * len(row)
        else:
            return [""] * len(row)

    file = st.file_uploader("Escolha um arquivo", type=["xlsx"], key="industrial")

    if file is None:
        return

    industrial = Industrial(pd.read_excel(file)).process()

    st.dataframe(
        industrial.style.apply(highlight_empty_factor, axis=1), hide_index=True
    )
