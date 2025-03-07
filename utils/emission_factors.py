import pandas as pd


def get_emission_factor(factor_name: str, factor_column: str):
    """
    Obtém um fator de emissão com base no nome e tipo.
    """
    factors = pd.read_excel("data/lca/emission_factors.xlsx")

    factor_name = factor_name.lower()
    factors["name"] = factors["name"].str.lower()

    factor = factors[factors["name"] == factor_name]

    if factor.empty and factor_column in factor.columns:
        # raise ValueError(f"Fator de emissão não encontrado para {factor_name}")
        print(f"Fator de emissão não encontrado para {factor_name}")
        return None

    return factor[factor_column].values[0]
