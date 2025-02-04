import streamlit as st

from processing.forestry.fuels import test_forestry_fuels
from processing.forestry.fertilizers import test_forestry_fertilizers
from processing.forestry.energy import test_forestry_energy
from processing.carbonization import test_carbonization
from processing.industrial import test_industrial
from processing.quartz_mining import test_quartz_mining

st.set_page_config(
    layout="wide",
)

st.title("eACV - Siderurgia")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Florestal (Combustíveis)",
        "Florestal (Fertilizantes)",
        "Florestal (Energia)",
        "Carbonização",
        "Industrial",
        "Mineração de Quartzo",
    ]
)

with tab1:
    test_forestry_fuels()

with tab2:
    test_forestry_fertilizers()

with tab3:
    test_forestry_energy()

with tab4:
    test_carbonization()

with tab5:
    test_industrial()

with tab6:
    test_quartz_mining()
