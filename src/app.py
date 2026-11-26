import io
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from week2 import DEFAULT_PARAMETERS, RESULT_COLUMNS, run_projection

st.set_page_config(page_title="AI workforce replacement cost comparison", layout="wide")
st.title("EVIL CORP — Workforce Cost Comparison")

# inputs
with st.sidebar:
    st.header("Inputs")
    uploaded_json = st.file_uploader("Load parameters (.json)", type=["json"])

    loaded_params = dict(DEFAULT_PARAMETERS)
    if uploaded_json is not None:
        try:
            raw_data = json.load(uploaded_json)
            if not isinstance(raw_data, dict):
                raise ValueError("JSON file must contain an object.")
            unknown = raw_data.keys() - DEFAULT_PARAMETERS.keys()
            if unknown:
                raise ValueError(f"Unknown parameters: {', '.join(sorted(unknown))}")
            for key, val in raw_data.items():
                if key in ("employees", "replaced", "years") and type(val) is not int:
                    raise ValueError(f"Parameter '{key}' must be an integer.")
                if key not in ("employees", "replaced", "years") and type(val) not in (int, float):
                    raise ValueError(f"Parameter '{key}' must be a number.")
            loaded_params.update(raw_data)
        except (ValueError, json.JSONDecodeError) as err:
            st.error(str(err))

    employees = st.number_input(
        "Initial number of employees", min_value=0, value=int(loaded_params["employees"]), step=1
    )
    replaced = st.number_input(
        "Employees replaced",
        min_value=0,
        max_value=int(employees),
        value=min(int(loaded_params["replaced"]), int(employees)),
        step=1,
    )
    annual_employee_cost = st.number_input(
        "Annual cost per employee (RON)",
        min_value=0.0,
        value=float(loaded_params["annual_employee_cost"]),
        step=1000.0,
    )
    annual_ai_cost = st.number_input(
        "Annual AI operating cost (RON)",
        min_value=0.0,
        value=float(loaded_params["annual_ai_cost"]),
        step=5000.0,
    )
    implementation_cost = st.number_input(
        "One-time implementation cost (RON)",
        min_value=0.0,
        value=float(loaded_params["implementation_cost"]),
        step=10000.0,
    )
    years = st.slider("Years to project", min_value=1, max_value=10, value=int(loaded_params["years"]))

# calculate projection
parameters = {
    "employees": int(employees),
    "replaced": int(replaced),
    "annual_employee_cost": float(annual_employee_cost),
    "annual_ai_cost": float(annual_ai_cost),
    "implementation_cost": float(implementation_cost),
    "years": int(years),
}

try:
    rows = run_projection(parameters)
except ValueError as err:
    st.error(str(err))
    st.stop()

df = pd.DataFrame(rows, columns=RESULT_COLUMNS)
first_year = df.iloc[0]
final_year = df.iloc[-1]

# results (text)
col1, col2, col3 = st.columns(3)
col1.metric(
    "First-Year scenario cost",
    f"{first_year['scenario_cost']:,.2f} RON",
    delta=f"{-first_year['savings']:,.2f} RON vs. baseline",
    delta_color="inverse",
)
col2.metric(
    f"{years}-Year cumulative scenario cost",
    f"{final_year['cumul_scenario']:,.2f} RON",
    delta=f"{-final_year['cumul_savings']:,.2f} RON vs. baseline",
    delta_color="inverse",
)
col3.metric(
    f"{years}-Year cumulative savings",
    f"{final_year['cumul_savings']:,.2f} RON",
)

st.markdown(
    f"""
    **Workforce:** {int(employees)} employees before replacement → **{int(employees - replaced)}** employees after replacement  
    **Year 1:** Baseline `{first_year['baseline_cost']:,.2f} RON` vs. AI `{first_year['scenario_cost']:,.2f} RON` (Savings: `{first_year['savings']:,.2f} RON`)  
    **Year {years} Cumulative:** Baseline `{final_year['cumul_baseline']:,.2f} RON` vs. AI `{final_year['cumul_scenario']:,.2f} RON` (Total Savings: `{final_year['cumul_savings']:,.2f} RON`)
    """
)


# charts
def make_overlaid_chart(data, baseline_col, scenario_col, title, y_axis_title):
    fig = go.Figure()
    x_labels = [f"Year {y}" for y in data["year"]]

    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=data[baseline_col],
            name="Before replacement (baseline)",
            mode="lines+markers",
            line=dict(color="#EF553B", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=data[scenario_col],
            name="After replacement (scenario)",
            mode="lines+markers",
            line=dict(color="#00CC96", width=3),
            fill="tonexty",
            fillcolor="rgba(0, 204, 150, 0.18)",
        )
    )

    fig.update_layout(
        title=title,
        yaxis_title=y_axis_title,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        height=380,
    )
    return fig


st.plotly_chart(
    make_overlaid_chart(
        df,
        "baseline_cost",
        "scenario_cost",
        "Annual cost",
        "Cost (RON)",
    ),
    use_container_width=True,
)

st.plotly_chart(
    make_overlaid_chart(
        df,
        "cumul_baseline",
        "cumul_scenario",
        "Cumulative Cost: Before AI vs. After AI (Shaded Area = Cumulative Savings)",
        "Cumulative Cost (RON)",
    ),
    use_container_width=True,
)

with st.expander("View Year-by-Year Table"):
    display_df = df.rename(
        columns={
            "year": "Year",
            "baseline_cost": "Baseline Annual (RON)",
            "scenario_cost": "Scenario Annual (RON)",
            "savings": "Annual Savings (RON)",
            "cumul_baseline": "Cumulative Baseline (RON)",
            "cumul_scenario": "Cumulative Scenario (RON)",
            "cumul_savings": "Cumulative Savings (RON)",
        }
    )
    st.dataframe(
        display_df.style.format("{:,.2f}", subset=[c for c in display_df.columns if c != "Year"]),
        use_container_width=True,
        hide_index=True,
    )

csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False, lineterminator="\n")
st.download_button(
    label="Download results (.csv)",
    data=csv_buffer.getvalue(),
    file_name="results.csv",
    mime="text/csv",
)