import pandas as pd
import numpy as np
import streamlit as st


class Carbonization:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.carbonization_factors = pd.read_excel("data/lca/carbonization.xlsx")
        self.gwp_factors = pd.read_excel("data/lca/gwp_kyoto.xlsx")

    def calculate_emission_ch4(self, row: pd.Series) -> float:
        return (
            self.carbonization_factors.iloc[8]["value"]
            * row["Rendimento Gravimétrico (%)"]
            + self.carbonization_factors.iloc[9]["value"]
        ) * row["Produção de Carvão Vegetal"]

    def calculate_emission_biogenic_co2(self, row: pd.Series) -> float:
        return ((2.21 * 44) / (1.07 * 16)) * row["Emissões de CH4 (tCO2e)"]

    def calculate_total_emission_biogenic_co2(self, row: pd.Series) -> float:
        return (
            row["Emissões de CH4 (tCO2e)"] * self.gwp_factors.iloc[1]["ar6"] / 1000
            + row["Emissões CO2 - biogênico (kgCO2)"] / 1000
        )

    def process(self):
        self.df["Produção de Carvão Vegetal"].fillna(0)
        self.df["Rendimento Gravimétrico (%)"].fillna(0)

        self.df["Madeira"] = np.divide(
            self.df["Produção de Carvão Vegetal"],
            self.df["Rendimento Gravimétrico (%)"],
        )

        self.df["Emissões de CH4 (tCO2e)"] = self.df.apply(
            self.calculate_emission_ch4, axis=1
        )

        self.df["Emissões CO2 - biogênico (kgCO2)"] = self.df.apply(
            self.calculate_emission_biogenic_co2, axis=1
        )

        # TODO: Na verdade seria Emissões totais - tCO2e ao invés de emissões biogênicas
        # Esse caso de "Emissões biogênicas" só se aplica a RIMA
        self.df["Emissões Biogênicas Totais (tCO2e)"] = self.df.apply(
            self.calculate_total_emission_biogenic_co2, axis=1
        )

        return self.df


def test_carbonization():
    file = st.file_uploader("Escolha um arquivo", type=["xlsx"], key="carbonization")
    if file is None:
        return

    carbonization = Carbonization(
        pd.read_excel(file)
    ).process()

    result = pd.DataFrame(
        {
            "Madeira": [carbonization["Madeira"].sum()],
            "Emissões totais tCO2e": [carbonization["Emissões Biogênicas Totais (tCO2e)"].sum()],
        }
    )

    result["Emissões de CH4 (tCO2e)"] = carbonization[
        "Emissões de CH4 (tCO2e)"
    ].sum()

    result["Emissões CO2 - biogênico (kgCO2)"] = carbonization[
        "Emissões CO2 - biogênico (kgCO2)"
    ].sum()

    st.dataframe(carbonization, hide_index=True)

    st.title("Resultados")
    st.dataframe(result, hide_index=True, use_container_width=True)
