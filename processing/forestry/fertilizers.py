import pandas as pd
import numpy as np
import streamlit as st

# ** Utils
from utils.emission_factors import get_emission_factor


class ForestryFertilizers:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.factors_fertilizers = pd.read_excel("data/lca/factors/fertilizers.xlsx")
        self.gwp_kyoto = pd.read_excel("data/lca/gwp_kyoto.xlsx")

    def calculate_base_quantity(self):
        """Convert base quantity to kg"""
        return self.df["Quantidade utilizada"] * 1000

    def calculate_calcium_carbonate_equivalent(self, row):
        """Calculate calcium carbonate equivalent applied"""
        cao_factor = row["Teor de CaO (%)"] * self.factors_fertilizers.iloc[14]["value"]
        mgo_factor = row["Teor de MgO (%)"] * self.factors_fertilizers.iloc[15]["value"]
        return (cao_factor + mgo_factor) * row["Quantidade para cálculo (kg)"]

    def calculate_nitrogen_applied(self, row):
        """Calculate applied nitrogen quantity"""
        return row["Quantidade para cálculo (kg)"] * row["Teor de Nitrogênio (%)"]

    def calculate_co2_emissions(self, row):
        """Calculate CO2 emissions based on limestone type"""
        if row["Calcário Calcítico ou Dolomítico"] == "Calcítico":
            return (
                row["Quantidade de equivalência em carbonato de cálcio aplicada (kg)"]
                * self.factors_fertilizers.iloc[12]["value"]
            )
        elif row["Calcário Calcítico ou Dolomítico"] == "Dolomítico":
            return (
                row["Quantidade de equivalência em carbonato de cálcio aplicada (kg)"]
                * self.factors_fertilizers.iloc[13]["value"]
            )
        return 0

    def calculate_n2o_emissions(self, row):
        """Calculate N2O emissions"""
        return (
            row["Quantidade de N aplicada (kg)"]
            * self.factors_fertilizers.iloc[6]["value"]
        )

    def calculate_use_emissions(self, row):
        """Calculate use emissions in tCO2e"""
        return np.divide(
            row["Emissões kgCO2"]
            + (row["Emissões kgN2O"] * self.gwp_kyoto.iloc[4]["ar6"]),
            1000,
        )

    def calculate_fossil_production_emissions(self, row):
        """Calculate fossil production emissions"""
        return np.divide(
            row["Quantidade para cálculo (kg)"]
            * get_emission_factor(row["Nome no Estudo"], "fossil_emission_factor"),
            1000,
        )

    def calculate_biogenic_production_emissions(self, row):
        """Calculate biogenic production emissions"""
        return np.divide(
            row["Quantidade para cálculo (kg)"]
            * get_emission_factor(row["Nome no Estudo"], "biogenic_emission_factor"),
            1000,
        )

    def calculate_luc_production_emissions(self, row):
        """Calculate LUC production emissions"""
        return np.divide(
            row["Quantidade para cálculo (kg)"]
            * get_emission_factor(row["Nome no Estudo"], "luc_emission_factor"),
            1000,
        )

    def calculate_total_emissions(self, row):
        """Calculate total emissions"""
        return np.sum(
            row["Emissões Fósseis Produção tCO2e"] + row["Emissões Uso tCO2e"]
        )

    def process(self):
        """Main processing method that orchestrates all calculations"""
        self.df["Quantidade para cálculo (kg)"] = self.calculate_base_quantity()

        self.df["Quantidade de equivalência em carbonato de cálcio aplicada (kg)"] = (
            self.df.apply(self.calculate_calcium_carbonate_equivalent, axis=1)
        )

        self.df["Quantidade de N aplicada (kg)"] = self.df.apply(
            self.calculate_nitrogen_applied, axis=1
        )

        self.df["Emissões kgCO2"] = self.df.apply(self.calculate_co2_emissions, axis=1)

        self.df["Emissões kgN2O"] = self.df.apply(self.calculate_n2o_emissions, axis=1)

        self.df["Emissões Uso tCO2e"] = self.df.apply(
            self.calculate_use_emissions, axis=1
        )

        self.df["Emissões Fósseis Produção tCO2e"] = self.df.apply(
            self.calculate_fossil_production_emissions, axis=1
        )

        self.df["Emissões Biogênicas Produção tCO2e"] = self.df.apply(
            self.calculate_biogenic_production_emissions, axis=1
        )

        self.df["Emissões LUC Produção tCO2e"] = self.df.apply(
            self.calculate_luc_production_emissions, axis=1
        )

        self.df["Emissões totais tCO2e"] = self.df.apply(
            self.calculate_total_emissions, axis=1
        )

        # st.toast("Cálculo de emissões de fertilizantes concluído com sucesso!")

        return self.df


def test_forestry_fertilizers():
    df = pd.read_excel("data/lca/mock/forestry_fertilizers.xlsx")
    forestry_fertilizers = ForestryFertilizers(df)

    st.dataframe(forestry_fertilizers.process(), hide_index=True)
