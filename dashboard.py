import pandas as pd
import streamlit as st
import os

# -------------------------
# 1) File/folder setup
# -------------------------
BASE_FOLDER = "Months"  # adjust path
FILE_OTHER = "Alrode Other Info.xlsx"

# -------------------------
# 2) Helpers
# -------------------------
def get_tenant_recoveries(df, value_col):
    return df.loc[df["TENANT'S NAME"].str.contains("TOTAL", na=False), value_col].sum()

def get_council_value(other_df, var_name, col="Rand"):
    return float(other_df.loc[other_df["Variable"] == var_name, col].values[0])

def fmt(val, money=False):
    """Format with bold, negatives red, positives black"""
    if money:
        text = f"R {val:,.2f}"
    else:
        text = f"{val:,.2f}"

    if val < 0:
        return f":red[**{text}**]"
    else:
        return f"**{text}**"

# -------------------------
# 3) Sidebar inputs
# -------------------------
st.sidebar.title("⚙️ Controls")

# Get month folders
month_folders = [f for f in os.listdir(BASE_FOLDER) if os.path.isdir(os.path.join(BASE_FOLDER, f))]
month = st.sidebar.selectbox("Select Month", month_folders)

# Get building files
folder = os.path.join(BASE_FOLDER, month)
files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]
buildings = [os.path.splitext(f)[0] for f in files]
building = st.sidebar.selectbox("Select Building", buildings)

# -------------------------
# 4) Load data
# -------------------------
other_df = pd.read_excel(FILE_OTHER, sheet_name=month)
file_meters = os.path.join(folder, f"{building}.xlsx")

elec_df = pd.read_excel(file_meters, sheet_name="Elec Excel")
water_df = pd.read_excel(file_meters, sheet_name="Water Excel")
effluent_df = pd.read_excel(file_meters, sheet_name="Effluent Excel")

st.title(f"📊 Utilities Dashboard — {building} ({month})")

# -------------------------
# 5) Level 1: Walk Away (3 columns)
# -------------------------
st.header("📊 Level 1: Walk Away")

col1, col2, col3 = st.columns(3)

for col, (util, df) in zip(
    [col1, col2, col3],
    [("Elec", elec_df), ("Water", water_df), ("Effluent", effluent_df)]
):
    with col:
        if util == "Elec":
            recoveries = {
                "Rand": float(get_tenant_recoveries(df, "COST")),
                "kWh": float(get_tenant_recoveries(df, "CONSUMPTION")),
            }
            council = {
                "Rand": (
                    get_council_value(other_df, "Muni Peak")
                    + get_council_value(other_df, "Muni Standard")
                    + get_council_value(other_df, "Muni OP")
                    + get_council_value(other_df, "Muni Max Demand")
                    + get_council_value(other_df, "Muni Network Access")
                    + get_council_value(other_df, "Muni Fixed Charge")
                ),
                "kWh": (
                    get_council_value(other_df, "Muni Peak", "Value")
                    + get_council_value(other_df, "Muni Standard", "Value")
                    + get_council_value(other_df, "Muni OP", "Value")
                ),
            }
        elif util == "Water":
            recoveries = {
                "Rand": float(get_tenant_recoveries(df, "COST")),
                "kL": float(get_tenant_recoveries(df, "CONSUMPTION")),
            }
            council = {
                "Rand": get_council_value(other_df, "Muni Water"),
                "kL": get_council_value(other_df, "Muni Water", "Value"),
            }
        else:  # Effluent
            recoveries = {
                "Rand": float(get_tenant_recoveries(df, "COST")),
                "kL": float(get_tenant_recoveries(df, "CONSUMPTION")),
            }
            council = {
                "Rand": get_council_value(other_df, "Muni Effluent"),
                "kL": get_council_value(other_df, "Muni Effluent", "Value"),
            }

        walkaway = {k: recoveries[k] - council[k] for k in recoveries}

        st.subheader(util)
        st.markdown("**Recoveries (excl VAT):**")
        for k, v in recoveries.items():
            st.markdown(f"- {k}: {fmt(v, money=(k=='Rand'))}")

        st.markdown("**Council charges (excl VAT):**")
        for k, v in council.items():
            st.markdown(f"- {k}: {fmt(v, money=(k=='Rand'))}")

        st.markdown("**Net Walk Away:**")
        for k, v in walkaway.items():
            st.markdown(f"- {k}: {fmt(v, money=(k=='Rand'))}")

# -------------------------
# 6) Level 2: Solar Savings
# -------------------------
st.header("☀️ Level 2: Solar Savings")

solar_kwh = float(other_df.loc[other_df["Variable"].str.contains("MOL Solar"), "Value"].sum())
solar_rand = float(other_df.loc[other_df["Variable"].str.contains("MOL Solar"), "Rand"].sum())

st.markdown(f"- Solar kWh avoided: {fmt(solar_kwh)}")
st.markdown(f"- Solar Rand Savings (excl VAT): {fmt(solar_rand, money=True)}")

# -------------------------
# 7) Level 3: Council Overcharge Check
# -------------------------
st.header("⚖️ Level 3: Council Overcharge Check")

# Electricity
mol_elec_val = other_df.loc[other_df["Variable"].str.contains("MOL Muni"), "Value"].sum()
mol_elec_rand = other_df.loc[other_df["Variable"].str.contains("MOL Muni"), "Rand"].sum()
muni_elec_val = (
    get_council_value(other_df, "Muni Peak", "Value")
    + get_council_value(other_df, "Muni Standard", "Value")
    + get_council_value(other_df, "Muni OP", "Value")
)
muni_elec_rand = (
    get_council_value(other_df, "Muni Peak")
    + get_council_value(other_df, "Muni Standard")
    + get_council_value(other_df, "Muni OP")
    + get_council_value(other_df, "Muni Max Demand")
    + get_council_value(other_df, "Muni Network Access")
    + get_council_value(other_df, "Muni Fixed Charge")
)
elec_diff = {
    "Consumption Diff": mol_elec_val - muni_elec_val,
    "Rand Diff": mol_elec_rand - muni_elec_rand,
}

# Water
jerry_water_val = water_df.loc[water_df["TENANT'S NAME"].str.contains("COUNCIL", na=False), "CONSUMPTION"].sum()
jerry_water_rand = water_df.loc[water_df["TENANT'S NAME"].str.contains("COUNCIL", na=False), "COST"].sum()
muni_water_val = get_council_value(other_df, "Muni Water", "Value")
muni_water_rand = get_council_value(other_df, "Muni Water")
water_diff = {
    "Consumption Diff": jerry_water_val - muni_water_val,
    "Rand Diff": jerry_water_rand - muni_water_rand,
}

# Effluent
jerry_eff_val = effluent_df.loc[effluent_df["TENANT'S NAME"].str.contains("COUNCIL", na=False), "CONSUMPTION"].sum()
jerry_eff_rand = effluent_df.loc[effluent_df["TENANT'S NAME"].str.contains("COUNCIL", na=False), "COST"].sum()
muni_eff_val = get_council_value(other_df, "Muni Effluent", "Value")
muni_eff_rand = get_council_value(other_df, "Muni Effluent")
eff_diff = {
    "Consumption Diff": jerry_eff_val - muni_eff_val,
    "Rand Diff": jerry_eff_rand - muni_eff_rand,
}

# Show results with bullet points
for util, diffs in [("Electricity", elec_diff), ("Water", water_diff), ("Effluent", eff_diff)]:
    st.subheader(util)
    for k, v in diffs.items():
        st.markdown(f"- {k}: {fmt(v, money=('Rand' in k))}")
