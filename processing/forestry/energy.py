from dataclasses import dataclass
import pandas as pd
import numpy as np
import streamlit as st

from utils.emission_factors import get_emission_factor


@dataclass
class GridFactors:
    """Grid emission factors data structure"""

    year: int
    january: float
    february: float
    march: float
    april: float
    may: float
    june: float
    july: float
    august: float
    september: float
    october: float
    november: float
    december: float
    avg_annual_factor_tco2_mwh: float
    avg_annual_factor_tco2_gj: float
    notes: str


class EmissionCalculator:
    def calculate_grid_emission(self, consumption: float, factor: float) -> float:
        return consumption * (factor / 1000)

    def calculate_other_emission(
        self, consumption: float, source: str, gas: str
    ) -> float:
        mapping = {
            "co2": "fossil_emission_factor",
            "co2_biogenic": "biogenic_emission_factor",
        }

        gas_emission_factor = get_emission_factor(source, mapping[gas])

        return consumption * (gas_emission_factor / 1000)


class ForestryEnergy:
    MONTH_MAPPER = {
        "Consumo - Janeiro": "january",
        "Consumo - Fevereiro": "february",
        "Consumo - Março": "march",
        "Consumo - Abril": "april",
        "Consumo - Maio": "may",
        "Consumo - Junho": "june",
        "Consumo - Julho": "july",
        "Consumo - Agosto": "august",
        "Consumo - Setembro": "september",
        "Consumo - Outubro": "october",
        "Consumo - Novembro": "november",
        "Consumo - Dezembro": "december",
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.grid_factors = pd.read_excel("data/lca/factors/grid_factors.xlsx")
        self.calculator = EmissionCalculator()

    def get_grid_factors(self, year: int) -> GridFactors:
        factors = self.grid_factors[self.grid_factors["year"] == year]
        return GridFactors(**factors.iloc[0].to_dict())

    def calculate_monthly_emissions(
        self, row: pd.Series, month: str, factor: float
    ) -> float:
        consumption = row[month]
        source = row["Fonte de Energia"]

        if source == "Grid":
            return (self.calculator.calculate_grid_emission(consumption, factor), 0)
        return (
            self.calculator.calculate_other_emission(consumption, source, "co2"),
            self.calculator.calculate_other_emission(
                consumption, source, "co2_biogenic"
            ),
        )

    def calculate_annual_emissions(self):
        return self.df[
            [
                "Emissões tCO2 - Janeiro",
                "Emissões tCO2 - Fevereiro",
                "Emissões tCO2 - Março",
                "Emissões tCO2 - Abril",
                "Emissões tCO2 - Maio",
                "Emissões tCO2 - Junho",
                "Emissões tCO2 - Julho",
                "Emissões tCO2 - Agosto",
                "Emissões tCO2 - Setembro",
                "Emissões tCO2 - Outubro",
                "Emissões tCO2 - Novembro",
                "Emissões tCO2 - Dezembro",
            ]
        ].sum(axis=1)

    def process(self) -> pd.DataFrame:
        year = self.df["Ano"].values[0]
        grid_factors = self.get_grid_factors(year)

        for month, grid_month in self.MONTH_MAPPER.items():
            factor = getattr(grid_factors, grid_month)
            self.df[month.replace("Consumo", "Emissões tCO2")] = self.df.apply(
                lambda row: self.calculate_monthly_emissions(row, month, factor)[0],
                axis=1,
            )
            self.df[month.replace("Consumo", "Emissões Biogênicas tCO2e")] = (
                self.df.apply(
                    lambda row: self.calculate_monthly_emissions(row, month, factor)[1],
                    axis=1,
                )
            )

        self.df["Emissões totais (tCO2e)"] = self.calculate_annual_emissions()

        return self.df


def test_forestry_energy():
    file = st.file_uploader("Escolha um arquivo", type=["xlsx"], key="energy")
    if file is None:
        return

    df = pd.read_excel(file)
    forestry_energy = ForestryEnergy(df)
    processed = forestry_energy.process()

    result = pd.DataFrame({
        "Consumo": [np.sum(
            processed[
                [
                    "Consumo - Janeiro",
                    "Consumo - Fevereiro",
                    "Consumo - Março",
                    "Consumo - Abril",
                    "Consumo - Maio",
                    "Consumo - Junho",
                    "Consumo - Julho",
                    "Consumo - Agosto",
                    "Consumo - Setembro",
                    "Consumo - Outubro",
                    "Consumo - Novembro",
                    "Consumo - Dezembro",
                ]
            ].sum(axis=1)
        )],
        "Emissões totais (tCO2e)": [processed["Emissões totais (tCO2e)"].sum()],
    })

    st.dataframe(processed, hide_index=True)

    st.title('Resultados')
    st.dataframe(result, hide_index=True, use_container_width=True)