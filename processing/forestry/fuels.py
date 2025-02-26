import pandas as pd
import numpy as np
from streamlit_react_flow import react_flow
import streamlit as st
import json
import graphviz


class ForestryFuels:
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa a classe ForestryFuels com um DataFrame.

        :param df: DataFrame contendo os dados de combustíveis florestais.
        """
        self.df = df
        self.densities = pd.read_excel("data/lca/densities.xlsx")
        self.emission_factors = pd.read_excel("data/lca/emission_factors.xlsx")

    def get_off_road_factors(self, fuel_type: str, column_name: str):
        """
        Obtém fatores de emissão para um tipo de combustível específico.

        :param fuel_type: Tipo de combustível.
        :param column_name: Nome da coluna para o fator desejado.
        :return: Valor do fator de emissão.
        """
        try:
            orf = pd.read_excel(
                "data/lca/mobile_combustion.xlsx", sheet_name="off_road"
            )
            orf["fuel_transportation"] = (
                orf["fuel_transportation"].str.lower().str.strip()
            )
            return orf[orf["fuel_transportation"] == fuel_type][column_name].values[0]
        except (FileNotFoundError, KeyError, IndexError) as e:
            print(f"Erro ao obter fatores para {fuel_type}: {e}")
            # np.nan
            return 0

    def get_emission_factors(self, name: str, column_name: str) -> float:
        try:
            factor = self.emission_factors[self.emission_factors["name"] == name]

            return factor[column_name].values[0]
        except (FileNotFoundError, KeyError, IndexError) as e:
            print(f"Erro ao obter fatores para {name}: {e}")
            return 0

    def get_density(self, name: str, column_name: str) -> float:
        try:
            factor = self.densities[self.densities["fuel"] == name]

            return factor[column_name].values[0]
        except (FileNotFoundError, KeyError, IndexError) as e:
            print(f"Erro ao obter densidade para {name}: {e}")
            return 0

    def calculate_emissions_co2(self, fuel, consumption):
        """
        Calcula as emissões de CO2 para um dado combustível e consumo.

        :param fuel: Tipo de combustível.
        :param consumption: Consumo do combustível.
        :return: Emissões de CO2 calculadas.

        =IF(
        D2="Gasolina Automotiva";
        (H2/1000) * (1-0,27) * (XLOOKUP(D2;Combustão_Móvel!$A$16:$A$20;Combustão_Móvel!$E$16:$E$20)) * (XLOOKUP(D2;Combustão_Móvel!$A$16:$A$20;Combustão_Móvel!$D$16:$D$20));

        IF(D2="Óleo Diesel";(H2/1000)*(1-0,1)*(XLOOKUP(D2;Combustão_Móvel!$A$16:$A$20;Combustão_Móvel!$E$16:$E$20))*(XLOOKUP(D2;Combustão_Móvel!$A$16:$A$20;Combustão_Móvel!$D$16:$D$20))))*1000
        """
        if fuel == "gasolina automotiva":
            co2_factor = self.get_off_road_factors(fuel, "co2_tco2_gj")
            energy_content = self.get_off_road_factors(fuel, "energy_content_gj_m3")
            return (
                (consumption / 1000) * (1 - 0.27) * co2_factor * energy_content * 1000
            )
        elif fuel == "óleo diesel":
            co2_factor = self.get_off_road_factors(fuel, "co2_tco2_gj")
            energy_content = self.get_off_road_factors(fuel, "energy_content_gj_m3")
            return (
                (consumption / 1000) * (1 - 0.1) * (co2_factor * energy_content) * 1000
            )

        return 0

    def calculate_emissions_biogenic_co2(self, fuel, consumption):
        """
        Calcula as emissões de CO2 para um dado combustível e consumo.

        :param fuel: Tipo de combustível.
        :param consumption: Consumo do combustível.
        :return: Emissões de CO2 calculadas.

        =IF(
            D2="Gasolina Automotiva";
                (H2/1000) * (0,27) * (Combustão_Móvel!$D$18) * (Combustão_Móvel!$E$18);

        IF(
            D2="Óleo Diesel";
            (H2/1000) * (0,1) * (Combustão_Móvel!$D$20) * (Combustão_Móvel!$E$20)))

        *1000
        """
        if fuel == "gasolina automotiva":
            co2_factor = self.get_off_road_factors(
                "álcool etílico anidro", "co2_tco2_gj"
            )
            energy_content = self.get_off_road_factors(
                "álcool etílico anidro", "energy_content_gj_m3"
            )
            return (consumption / 1000) * 0.27 * co2_factor * energy_content * 1000
        elif fuel == "óleo diesel":
            co2_factor = self.get_off_road_factors("biodiesel", "co2_tco2_gj")
            energy_content = self.get_off_road_factors(
                "biodiesel", "energy_content_gj_m3"
            )
            return (consumption / 1000) * 0.1 * (co2_factor * energy_content) * 1000

        return 0

    def calculate_emissions_ch4(self, fuel, consumption):
        consumption = np.array(consumption) / 1000

        ch4_factors = np.zeros_like(consumption)
        energy_contents = np.zeros_like(consumption)
        mix_energy_contents = np.zeros_like(consumption)
        mix_factors = np.zeros_like(consumption)

        gasolina_mask = fuel == "gasolina automotiva"
        diesel_mask = fuel == "óleo diesel"

        ch4_factors[gasolina_mask] = self.get_off_road_factors(
            "gasolina automotiva", "ch4_tch4_gj"
        )
        energy_contents[gasolina_mask] = self.get_off_road_factors(
            "gasolina automotiva", "energy_content_gj_m3"
        )
        mix_energy_contents[gasolina_mask] = self.get_off_road_factors(
            "álcool etílico anidro", "energy_content_gj_m3"
        )
        mix_factors[gasolina_mask] = self.get_off_road_factors(
            "álcool etílico anidro", "ch4_tch4_gj"
        )

        ch4_factors[diesel_mask] = self.get_off_road_factors(
            "óleo diesel", "ch4_tch4_gj"
        )
        energy_contents[diesel_mask] = self.get_off_road_factors(
            "óleo diesel", "energy_content_gj_m3"
        )
        mix_energy_contents[diesel_mask] = self.get_off_road_factors(
            "biodiesel", "energy_content_gj_m3"
        )
        mix_factors[diesel_mask] = self.get_off_road_factors("biodiesel", "ch4_tch4_gj")

        etanol_fraction = np.where(gasolina_mask, 0.27, 0.1)

        emissions = (
            consumption
            * (
                (1 - etanol_fraction) * ch4_factors * energy_contents
                + etanol_fraction * mix_factors * mix_energy_contents
            )
            * 1000
        )

        return emissions

    def calculate_emissions_n2o(self, fuel, consumption):
        consumption = np.array(consumption) / 1000

        n2o_factors = np.zeros_like(consumption)
        energy_contents = np.zeros_like(consumption)
        mix_energy_contents = np.zeros_like(consumption)
        mix_factors = np.zeros_like(consumption)

        gasolina_mask = fuel == "gasolina automotiva"
        diesel_mask = fuel == "óleo diesel"

        n2o_factors[gasolina_mask] = self.get_off_road_factors(
            "gasolina automotiva", "n2o_tn2o_gj"
        )
        energy_contents[gasolina_mask] = self.get_off_road_factors(
            "gasolina automotiva", "energy_content_gj_m3"
        )
        mix_energy_contents[gasolina_mask] = self.get_off_road_factors(
            "álcool etílico anidro", "energy_content_gj_m3"
        )
        mix_factors[gasolina_mask] = self.get_off_road_factors(
            "álcool etílico anidro", "n2o_tn2o_gj"
        )

        n2o_factors[diesel_mask] = self.get_off_road_factors(
            "óleo diesel", "n2o_tn2o_gj"
        )
        energy_contents[diesel_mask] = self.get_off_road_factors(
            "óleo diesel", "energy_content_gj_m3"
        )
        mix_energy_contents[diesel_mask] = self.get_off_road_factors(
            "biodiesel", "energy_content_gj_m3"
        )
        mix_factors[diesel_mask] = self.get_off_road_factors("biodiesel", "n2o_tn2o_gj")

        etanol_fraction = np.where(gasolina_mask, 0.27, 0.1)

        emissions = (
            consumption
            * (
                (1 - etanol_fraction) * n2o_factors * energy_contents
                + etanol_fraction * mix_factors * mix_energy_contents
            )
            * 1000
        )

        return emissions

    def calculate_fossil_combustion_emissions_tco2e(self):
        """
        =( J2 + ( L2 * GWP_Quioto!$E$3 ) + ( M2 * GWP_Quioto!$E$6 ) ) / 1000
        """
        gwp_kyoto_factors = pd.read_excel("data/lca/gwp_kyoto.xlsx")
        gwp_ch4_ar6 = gwp_kyoto_factors["ar6"].values[1]
        gwp_n2o_ar6 = gwp_kyoto_factors["ar6"].values[4]

        return (
            self.df["Emissões CO2 (kgCO2)"]
            + (self.df["Emissões CH4 (kgCH4)"] * gwp_ch4_ar6)
            + (self.df["Emissões N2O (kgN2O)"] * gwp_n2o_ar6)
        ) / 1000

    def calculate_combustion_emissions_biogenic_tco2e(self):
        return self.df["Emissões CO2 - biogênico (kgCO2)"] / 1000

    def calculate_consumption_kg(self, row) -> float:
        fuel = row["Combustível (Nomenclatura Inv. GEE)"]

        try:

            if fuel == "gasolina automotiva":
                return (
                    row["Consumo"]
                    * (
                        (self.get_density(fuel, "density") * 0.73)
                        + (self.get_density("álcool etílico anidro", "density") * 0.27)
                    )
                    / 1000
                )
            elif fuel == "óleo diesel":
                return (
                    row["Consumo"]
                    * (
                        (self.get_density(fuel, "density") * 0.9)
                        + (self.get_density("biodiesel", "density") * 0.1)
                    )
                    / 1000
                )
            elif fuel == "acetileno":
                return row["Consumo"]
            else:
                return 0
        except:
            print(f"Emission factor not found for fuel: {fuel}")
            return 0

    def calculate_production_tco2_fossil_co2_emissions(self, row) -> float:
        fuel = row["Combustível (Nomenclatura Pegada de Carbono)"]

        try:
            factor = self.get_emission_factors(
                fuel,
                "fossil_emission_factor",
            )

            return np.divide(np.multiply(row["Consumo (KG)"], factor), 1000)
        except Exception as e:
            print(e)

            print(f"Emission factor not found for fuel: {fuel}")
            return 0

    def calculate_production_tco2_fossil_co2_biogenic_emissions(self, row) -> float:
        fuel = row["Combustível (Nomenclatura Pegada de Carbono)"]

        try:
            factor = self.get_emission_factors(
                fuel,
                "biogenic_emission_factor",
            )

            return np.divide(np.multiply(row["Consumo (KG)"], factor), 1000)
        except Exception as e:
            print(e)

            print(f"Emission factor not found for fuel: {fuel}")
            return 0

    def calculate_emissions_co2_luc_tco2e(self, row) -> float:
        """
        Calculate CO2 LUC emissions for a given fuel type.

        :param fuel: Fuel type for which to calculate emissions.
        :return: CO2 LUC emissions as a single scalar value.
        """

        fuel = row["Combustível (Nomenclatura Pegada de Carbono)"]

        try:
            factor = self.get_emission_factors(
                fuel,
                "luc_emission_factor",
            )

            return np.divide(np.multiply(row["Consumo (KG)"], factor), 1000)
        except Exception as e:
            print(e)

            print(f"Emission factor not found for fuel: {fuel}")
            return 0

    def calculate_total_fossil_emissions_tco2e(self, row):
        return (
            row["Emissões CO2 Fósseis - Produção (tCO2)"]
            + row["Emissões Fósseis Combustão (tCO2e)"]
        )

    def calculate_total_biogenic_emissions(self, row):
        return (
            row["Emissões Biogênicas Combustão (tCO2e)"]
            + row["Emissões CO2 Biogênico - Produção (tCO2)"]
        )

    def get_emissions_co2(self):
        """
        Calcula e adiciona as emissões de CO2 ao DataFrame.
        """
        self.df["Emissões CO2 (kgCO2)"] = self.df.apply(
            lambda row: self.calculate_emissions_co2(
                row["Combustível (Nomenclatura Inv. GEE)"], row["Consumo"]
            ),
            axis=1,
        )

    def get_emissions_biogenic_co2(self):
        """
        Calcula e adiciona as emissões - biogênico de CO2 ao DataFrame.
        """
        self.df["Emissões CO2 - biogênico (kgCO2)"] = self.df.apply(
            lambda row: self.calculate_emissions_biogenic_co2(
                row["Combustível (Nomenclatura Inv. GEE)"], row["Consumo"]
            ),
            axis=1,
        )

    def get_emissions_ch4(self):
        """
        Calcula e adiciona as emissões de CH4 ao DataFrame.
        """
        self.df["Emissões CH4 (kgCH4)"] = self.df.apply(
            lambda row: self.calculate_emissions_ch4(
                row["Combustível (Nomenclatura Inv. GEE)"], row["Consumo"]
            ),
            axis=1,
        )

    def get_emissions_n2o(self):
        """
        Calcula e adiciona as emissões de N2O ao DataFrame.
        """
        self.df["Emissões N2O (kgN2O)"] = self.df.apply(
            lambda row: self.calculate_emissions_n2o(
                row["Combustível (Nomenclatura Inv. GEE)"], row["Consumo"]
            ),
            axis=1,
        )

    def get_fossil_combustion_emissions_tco2e(self):
        """
        Calcula e adiciona as emissões fósseis na combustão em tCO2e ao DataFrame.
        """
        self.df["Emissões Fósseis Combustão (tCO2e)"] = (
            self.calculate_fossil_combustion_emissions_tco2e()
        )

    def get_combustion_emissions_biogenic_tco2e(self):
        """
        Calcula e adiciona as emissões biogênicas combustão em tCO2e ao DataFrame.
        """
        self.df["Emissões Biogênicas Combustão (tCO2e)"] = (
            self.calculate_combustion_emissions_biogenic_tco2e()
        )

    def get_consumption_tco2e(self):
        """
        Calcula e adiciona o Consumo em KG ao DataFrame.
        """
        self.df["Consumo (KG)"] = self.df.apply(
            lambda row: self.calculate_consumption_kg(row), axis=1
        )

    def get_production_tco2_fossil_co2_emissions(self):
        """
        Calcula e adiciona Emissões CO2 Fósseis - Produção (tCO2) ao DataFrame.
        """
        self.df["Emissões CO2 Fósseis - Produção (tCO2)"] = self.df.apply(
            lambda row: self.calculate_production_tco2_fossil_co2_emissions(row),
            axis=1,
        )

    def get_production_tco2_fossil_co2_biogenic_emissions(self):
        """
        Calcula e adiciona Emissões CO2 Biogênico - Produção (tCO2) ao DataFrame.
        """
        self.df["Emissões CO2 Biogênico - Produção (tCO2)"] = self.df.apply(
            lambda row: self.calculate_production_tco2_fossil_co2_biogenic_emissions(
                row
            ),
            axis=1,
        )

    def get_emissions_co2_luc_tco2e(self):
        """
        Calcula e adiciona Emissões CO2 LUC - Produção (tCO2) ao DataFrame.
        """
        self.df["Emissões CO2 LUC - Produção (tCO2)"] = self.df.apply(
            lambda row: self.calculate_emissions_co2_luc_tco2e(row),
            axis=1,
        )

    def get_total_fossil_emissions_tco2e(self):
        self.df["Emissões Fósseis Totais (tCO2e)"] = self.df.apply(
            lambda row: self.calculate_total_fossil_emissions_tco2e(row), axis=1
        )

    def get_total_biogenic_emissions_tco2e(self):
        self.df["Emissões Biogênicas Totais (tCO2e)"] = self.df.apply(
            lambda row: self.calculate_total_biogenic_emissions(row), axis=1
        )

    def preparation(self):
        """
        Prepara o DataFrame inicializando colunas necessárias.
        """
        self.densities["fuel"] = self.densities["fuel"].str.lower()
        self.emission_factors["name"] = self.emission_factors["name"].str.lower()

        self.df["Combustível (Nomenclatura Inv. GEE)"] = self.df[
            "Combustível (Nomenclatura Inv. GEE)"
        ].str.lower()

        self.df["Combustível (Nomenclatura Pegada de Carbono)"] = self.df[
            "Combustível (Nomenclatura Pegada de Carbono)"
        ].str.lower()

        self.df["Fração de Etanol"] = self.df[
            "Combustível (Nomenclatura Inv. GEE)"
        ].apply(lambda x: 0.27 if x == "gasolina automotiva" else 0)

        self.df["Fração de Biodiesel"] = self.df[
            "Combustível (Nomenclatura Inv. GEE)"
        ].apply(lambda x: 0 if x == "óleo diesel" else 1)

        self.get_emissions_co2()
        self.get_emissions_biogenic_co2()
        self.get_emissions_ch4()
        self.get_emissions_n2o()
        self.get_fossil_combustion_emissions_tco2e()
        self.get_combustion_emissions_biogenic_tco2e()
        self.get_consumption_tco2e()
        self.get_production_tco2_fossil_co2_emissions()
        self.get_production_tco2_fossil_co2_biogenic_emissions()
        self.get_emissions_co2_luc_tco2e()
        self.get_total_fossil_emissions_tco2e()
        self.get_total_biogenic_emissions_tco2e()

        # st.toast("Cálculo de emissões de combustíveis concluído com sucesso!")

        return self.df


def test_forestry_fuels():
    file = st.file_uploader("Escolha um arquivo", type=["xlsx"], key="fuels")
    if file is not None:
        df = pd.read_excel(file)
        forestry_fuels = ForestryFuels(df)
        st.dataframe(forestry_fuels.preparation(), hide_index=True)
        st.toast("Processamento concluído com sucesso!")