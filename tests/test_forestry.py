import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open
from main import ForestryFuels, ForestryFertilizers


@pytest.fixture
def sample_fuels_df():
    return pd.DataFrame(
        {
            "Combustível (Nomenclatura Inv. GEE)": [
                "gasolina automotiva",
                "óleo diesel",
            ],
            "Combustível (Nomenclatura Pegada de Carbono)": [
                "gasolina automotiva",
                "óleo diesel",
            ],
            "Consumo": [100, 200],
        }
    )


@pytest.fixture
def sample_fertilizers_df():
    return pd.DataFrame(
        {
            "Fertilizante": ["Test Fert 1", "Test Fert 2"],
            "Teor de Nitrogênio (%)": [0.1, 0.2],
            "Teor de CaO (%)": [0.3, 0.4],
            "Teor de MgO (%)": [0.5, 0.6],
            "Quantidade utilizada": [1000, 2000],
            "Calcário Calcítico ou Dolomítico": ["Calcítico", "Dolomítico"],
            "Nome no Estudo": ["fert1", "fert2"],
        }
    )


@pytest.fixture
def mock_excel_data():
    return {
        "data/lca/densities.xlsx": pd.DataFrame(
            {"fuel": ["gasolina automotiva", "óleo diesel"], "density": [0.75, 0.85]}
        ),
        "data/lca/emission_factors.xlsx": pd.DataFrame(
            {
                "name": ["gasolina automotiva", "óleo diesel"],
                "fossil_emission_factor": [2.3, 2.6],
                "biogenic_emission_factor": [0.1, 0.2],
                "luc_emission_factor": [0.3, 0.4],
            }
        ),
        "data/lca/mobile_combustion.xlsx": pd.DataFrame(
            {
                "fuel_transportation": ["gasolina automotiva", "óleo diesel"],
                "co2_tco2_gj": [69.3, 74.1],
                "energy_content_gj_m3": [32.5, 35.5],
                "ch4_tch4_gj": [0.003, 0.004],
                "n2o_tn2o_gj": [0.0006, 0.0008],
            }
        ),
        "data/lca/gwp_kyoto.xlsx": pd.DataFrame({"ar6": [1, 27.9, 273]}),
    }


@patch("pandas.read_excel")
def test_forestry_fuels_preparation(mock_read_excel, sample_fuels_df, mock_excel_data):
    def mock_read_excel_func(path, *args, **kwargs):
        return mock_excel_data[path]

    mock_read_excel.side_effect = mock_read_excel_func

    ff = ForestryFuels(sample_fuels_df)
    result = ff.preparation()

    assert "Emissões CO2 (kgCO2)" in result.columns
    assert "Emissões Fósseis Totais (tCO2e)" in result.columns
    assert len(result) == 2


@patch("pandas.read_excel")
def test_calculate_emissions_co2(mock_read_excel, sample_fuels_df, mock_excel_data):
    def mock_read_excel_func(path, *args, **kwargs):
        return mock_excel_data[path]

    mock_read_excel.side_effect = mock_read_excel_func

    ff = ForestryFuels(sample_fuels_df)
    emissions = ff.calculate_emissions_co2("gasolina automotiva", 100)

    assert isinstance(emissions, float)
    assert emissions >= 0


@patch("pandas.read_excel")
def test_forestry_fertilizers_process(
    mock_read_excel, sample_fertilizers_df, mock_excel_data
):
    def mock_read_excel_func(path, *args, **kwargs):
        return mock_excel_data[path]

    mock_read_excel.side_effect = mock_read_excel_func

    ff = ForestryFertilizers(sample_fertilizers_df)
    result = ff.process()

    assert "Emissões totais tCO2e" in result.columns
    assert "Quantidade de N aplicada (kg)" in result.columns
    assert len(result) == 2


def test_invalid_fuel_type(sample_fuels_df):
    ff = ForestryFuels(sample_fuels_df)
    emissions = ff.calculate_emissions_co2("invalid_fuel", 100)
    assert emissions == 0


def test_zero_consumption(sample_fuels_df):
    ff = ForestryFuels(sample_fuels_df)
    emissions = ff.calculate_emissions_co2("gasolina automotiva", 0)
    assert emissions == 0
