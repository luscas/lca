import pandas as pd
import streamlit as st

from utils.emission_factors import get_emission_factor


class QuartzMining:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def process(self):
        self.df["Quantidade"] = self.df["Quantidade"].fillna(0)
        self.df["Nome no estudo"] = self.df["Nome no estudo"].fillna("-")

        self.df["Fonte do Fator de Emissão"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "source")
                if get_emission_factor(x, "source")
                else "Não encontrado"
            )
        )

        self.df["Fator de Emissão Fóssil"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "fossil_emission_factor")
                if get_emission_factor(x, "fossil_emission_factor")
                else 0
            )
        )

        self.df["Fator de Emissão Biogênico"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "biogenic_emission_factor")
                if get_emission_factor(x, "biogenic_emission_factor")
                else 0
            )
        )

        self.df["Fator de Remoção Biogênica"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "biogenic_removal_factor")
                if get_emission_factor(x, "biogenic_removal_factor")
                else 0
            )
        )

        self.df["Fator de Emissão LUC"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "luc_emission_factor")
                if get_emission_factor(x, "luc_emission_factor")
                else 0
            )
        )

        self.df["Unidade - Fator"] = self.df["Nome no estudo"].apply(
            lambda x: (
                get_emission_factor(x, "unit")
                if get_emission_factor(x, "unit")
                else "Não encontrado"
            )
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


def test_quartz_mining():
    def highlight_empty_factor(row):
        """Highlight the entire row in red if `Unidade - Fator` is NaN."""
        if pd.isna(row["Unidade - Fator"]):
            return ["background-color: #D2665A"] * len(row)
        else:
            return [""] * len(row)

    quartz_mining = QuartzMining(
        pd.read_excel("data/lca/mock/quartz_mining.xlsx")
    ).process()

    st.dataframe(
        quartz_mining.style.apply(highlight_empty_factor, axis=1), hide_index=True
    )
