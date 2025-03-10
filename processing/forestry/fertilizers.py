import pandas as pd
import numpy as np
import streamlit as st


class ForestryFertilizers:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.factors_fertilizers = pd.read_excel("data/lca/factors/fertilizers.xlsx")
        self.gwp_kyoto = pd.read_excel("data/lca/gwp_kyoto.xlsx")
        self.emission_factors = pd.read_excel("data/lca/emission_factors.xlsx")

    def get_emission_factor(factor_name: str, factor_column: str):
        """
        Obtém um fator de emissão com base no nome e tipo.
        """

        factor_name = factor_name.lower()
        self.emission_factors["name"] = self.emission_factors["name"].str.lower()

        factor = self.emission_factors[self.emission_factors["name"] == factor_name]

        if factor.empty and factor_column in factor.columns:
            # raise ValueError(f"Fator de emissão não encontrado para {factor_name}")
            print(f"Fator de emissão não encontrado para {factor_name}")
            return None

        return factor[factor_column].values[0]

    def calculate_base_quantity(self):
        """Convert base quantity to kg"""
        try:
            return np.multiply(self.df["Quantidade utilizada"], 1000)
        except Exception as e:
            print("Erro ao calcular a quantidade base")
            print(e)

            return None

    def calculate_calcium_carbonate_equivalent(self, row):
        """Calculate calcium carbonate equivalent applied"""
        try:
            cao_factor = row["Teor de CaO (%)"] * self.factors_fertilizers.iloc[14]["value"]
            mgo_factor = row["Teor de MgO (%)"] * self.factors_fertilizers.iloc[15]["value"]
            return (cao_factor + mgo_factor) * row["Quantidade para cálculo (kg)"]
        except:
            return None

    def calculate_nitrogen_applied(self, row):
        """Calculate applied nitrogen quantity"""
        try:
            return row["Quantidade para cálculo (kg)"] * row["Teor de Nitrogênio (%)"]
        except:
            return None

    def calculate_co2_emissions(self, row):
        """Calculate CO2 emissions based on limestone type"""
        try:
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
        except:
            return None

    def calculate_n2o_emissions(self, row):
        """Calculate N2O emissions"""
        try:
            return (
                row["Quantidade de N aplicada (kg)"]
                * self.factors_fertilizers.iloc[6]["value"]
            )
        except:
            return None

    def calculate_use_emissions(self, row):
        """Calculate use emissions in tCO2e"""
        try:
            return np.divide(
                row["Emissões kgCO2"]
                + (row["Emissões kgN2O"] * self.gwp_kyoto.iloc[4]["ar6"]),
                1000,
            )
        except:
            return None

    def calculate_fossil_production_emissions(self, row):
        """Calculate fossil production emissions"""
        try:
            emission_factor = self.get_emission_factor(row["Nome no Estudo"], "fossil_emission_factor")

            print(emission_factor)

            return np.divide(
                row["Quantidade para cálculo (kg)"]
                * emission_factor,
                1000,
            )
        except:
            return None

    def calculate_biogenic_production_emissions(self, row):
        """Calculate biogenic production emissions"""
        try:
            return np.divide(
                row["Quantidade para cálculo (kg)"]
                * self.get_emission_factor(row["Nome no Estudo"], "biogenic_emission_factor"),
                1000,
            )
        except:
            return None

    def calculate_luc_production_emissions(self, row):
        """Calculate LUC production emissions"""
        try:
            return np.divide(
                row["Quantidade para cálculo (kg)"]
                * self.get_emission_factor(row["Nome no Estudo"], "luc_emission_factor"),
                1000,
            )
        except:
            return None

    def calculate_total_emissions(self, row):
        """Calculate total emissions"""
        try:
            return np.sum(
                row["Emissões Fósseis Produção tCO2e"] + row["Emissões Uso tCO2e"]
            )
        except:
            return None

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
    file = st.file_uploader("Escolha um arquivo", type=["xlsx"], key="fertilizers")
    if file is not None:
        df = pd.read_excel(file,sheet_name=0)
        forestry_fertilizers = ForestryFertilizers(df)

        processed = forestry_fertilizers.process()
        result = pd.DataFrame({
            "Emissões totais tCO2e": [processed["Emissões totais tCO2e"].sum()]
        })

        if processed is not None:
            result["Emissões Fósseis Produção tCO2e"] = processed[
                "Emissões Fósseis Produção tCO2e"
            ].sum()
            result["Emissões Biogênicas Produção tCO2e"] = processed[
                "Emissões Biogênicas Produção tCO2e"
            ].sum()
            result["Emissões LUC Produção tCO2e"] = processed["Emissões LUC Produção tCO2e"].sum()
            result["Emissões Uso tCO2e"] = processed["Emissões Uso tCO2e"].sum()
            result["Emissões kgCO2"] = processed["Emissões kgCO2"].sum()
            result["Emissões kgN2O"] = processed["Emissões kgN2O"].sum()

            st.dataframe(processed, hide_index=True)

            st.title('Resultados')
            st.dataframe(result, hide_index=True, use_container_width=True)

            st.toast("Processamento concluído com sucesso!")
