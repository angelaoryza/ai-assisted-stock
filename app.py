import math

import pandas as pd
import streamlit as st

from sectors import SectorsError, get_company_overview


def rupiah(amount: float) -> str:
    return f"Rp {amount:,.0f}".replace(",", ".")


@st.cache_data(ttl=3600)
def cached_company_overview(ticker: str) -> dict:
    return get_company_overview(ticker)


st.set_page_config(page_title="Investment Goal Calculator", page_icon="📈")

st.title("Investment Goal Calculator")
st.write("See how your monthly savings could grow over time.")

ticker = st.text_input("IDX ticker", value="BBCA").strip().upper()
company = None
last_close = None
valid_last_close = False

try:
    company = cached_company_overview(ticker)
except SectorsError as error:
    st.warning(str(error))

if company:
    st.subheader(company.get("company_name") or ticker)
    st.write(f"Sector: {company.get('sector') or 'Not available'}")
    st.write(f"Sub-sector: {company.get('sub_sector') or 'Not available'}")

    last_close = company.get("last_close_price")
    valid_last_close = (
        isinstance(last_close, (int, float))
        and math.isfinite(last_close)
        and last_close > 0
    )
    if valid_last_close:
        st.write(f"Last close price: {rupiah(last_close)}")
    else:
        st.warning(
            "Last close price is unavailable, so the lot estimate cannot be calculated."
        )

monthly_saving = st.number_input(
    "Monthly saving (Rp)",
    min_value=0,
    value=1_000_000,
    step=100_000,
)
years = st.number_input(
    "Number of years",
    min_value=1,
    max_value=50,
    value=10,
    step=1,
)
yearly_return = st.number_input(
    "Expected yearly return (%)",
    min_value=-100.0,
    max_value=100.0,
    value=8.0,
    step=0.5,
    help="An estimate for illustration; actual returns can vary.",
)

monthly_return = yearly_return / 100 / 12
balance = 0.0
yearly_totals = []

for year in range(1, years + 1):
    for _ in range(12):
        balance *= 1 + monthly_return
        balance += monthly_saving
    yearly_totals.append({"Year": year, "Total amount": balance})

st.metric("Estimated final amount", rupiah(balance))

if valid_last_close:
    lots = math.floor(monthly_saving / (last_close * 100))
    leftover = monthly_saving - lots * last_close * 100
    st.write(f"Your monthly saving buys **{lots} lots** of this stock.")
    st.write(f"Left over: **{rupiah(leftover)}**")

chart_data = pd.DataFrame(yearly_totals).set_index("Year")
st.line_chart(chart_data, y="Total amount")
st.caption(
    "This estimate assumes savings are added at the end of each month. "
    "It is for illustration only and is not investment advice."
)

with st.expander("Raw company data"):
    if company:
        st.json(company)
    else:
        st.caption("Company data is unavailable until a valid ticker is loaded.")
