from enum import StrEnum
from typing import Literal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Bond Calculator",
    page_icon="🐖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def pmt(
    rate: float,
    nper: int,
    pv: float,
    fv: float = 0.0,
    t: Literal[0, 1] = 0,
) -> float:
    """The Excel "PMT" function is used to determine the payments owed to a lender by a borrower on a financial
    obligation, such as a loan or bond.

    The payment owed is derived from a constant interest rate, the number of periods (i.e. loan term),
    and the value of the original loan principal.

    The three variables are assumed to remain fixed across the entirety of the borrowing term.

    See [wallstreetprep.com](https://www.wallstreetprep.com/knowledge/pmt-function/) for more

    Args:
        rate (float): The fixed interest rate on the loan as stated in the lending agreement.
            The interest rate must be adjusted to remain consistent with the periodicity of the payment schedule
            (e.g. monthly, quarterly, semi-annual, annual).
        nper (int): The total number of periods in which payments must be issued over the borrowing term of the loan.
            Just like the interest rate, the number of payment periods must also be adjusted,
            or else the payment value will be incorrect.
        pv (float): The present value (PV) is the value of a series of payments based on the current date,
            i.e. the original principal of the loan on the date of issuance.
        fv (float, optional): The future value (FV) is the ending loan balance on the date of maturity.
            If left empty, the remaining principal is assumed to be zero, i.e.
            there is no outstanding balance left at maturity.
        t (Literal[0, 1], optional): The timing of when the payments are assumed to be received.
            "0" = End of Period (EoP)
            "1" = Beginning of Period (BoP)
            If omitted, i.e. left blank, the default setting in Excel is "0".

    Returns:
        float: The payment amount owed to the lender by the borrower on a periodic basis.
    """
    if rate == 0:
        return -(pv + fv) / nper

    r1 = (1 + rate) ** nper
    return -(rate * (pv * r1 + fv)) / ((1 + rate * t) * (r1 - 1))


def generate_amortization_schedule(
    principal: float,
    annual_rate: float,
    nper: int,
    periodicity: int,
) -> pd.DataFrame:
    periodic_rate = annual_rate / periodicity

    payment = -1 * pmt(rate=periodic_rate, nper=nper, pv=principal)

    periods = []
    opening_balances = []
    interest_rates = []
    payment_amounts = []
    interest_portions = []
    capital_portions = []
    closing_balances = []

    balance = principal

    for period in range(1, nper + 1):
        opening_balance = balance
        interest = opening_balance * periodic_rate
        capital = payment - interest
        closing_balance = opening_balance - capital

        if closing_balance < 0:
            capital = opening_balance
            payment = capital + interest
            closing_balance = 0

        periods.append(period)
        opening_balances.append(opening_balance)
        interest_rates.append(annual_rate * 100)  # Convert to percentage
        payment_amounts.append(payment)
        interest_portions.append(interest)
        capital_portions.append(capital)
        closing_balances.append(closing_balance)

        # Update balance for next period
        balance = closing_balance

        if balance <= 0:
            break

    df = pd.DataFrame(
        {
            "Period": periods,
            "Opening Balance": opening_balances,
            "Annual Interest Rate (%)": interest_rates,
            "Payment Amount": payment_amounts,
            "Interest Portion": interest_portions,
            "Capital Portion": capital_portions,
            "Closing Balance": closing_balances,
        }
    )

    return df


class Color(StrEnum):
    RED = "rgb(200, 50, 50)"
    BLUE = "rgb(0, 100, 200)"


def plot_amortization(
    df: pd.DataFrame,
    currency_symbol: str = "R",
) -> go.Figure:
    fig = go.Figure()

    # Add capital portion (stacked area)
    fig.add_trace(
        go.Scatter(
            x=df["Period"],
            y=df["Capital Portion"],
            name="Capital Portion",
            mode="lines",
            line={
                "width": 0.5,
                "color": Color.BLUE,
            },
            stackgroup="one",
            fillcolor=Color.BLUE,
            hovertemplate=(
                f"Period: %{{x}}<br>"  #
                f"Capital: {currency_symbol} %{{y:,.2f}}"
                "<extra></extra>"
            ),
        )
    )

    # Add interest portion (stacked area)
    fig.add_trace(
        go.Scatter(
            x=df["Period"],
            y=df["Interest Portion"],
            name="Interest Portion",
            mode="lines",
            line={
                "width": 0.5,
                "color": Color.RED,
            },
            stackgroup="one",
            fillcolor=Color.RED,
            hovertemplate=(
                f"Period: %{{x}}<br>"  #
                f"Interest: {currency_symbol} %{{y:,.2f}}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="",
        xaxis_title="Payment Period",
        yaxis_title=f"Amount ({currency_symbol})",
        hovermode="x unified",
        height=500,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    return fig


def plot_cumulative_totals(df: pd.DataFrame, currency_symbol: str = "R") -> go.Figure:
    """Create a line chart showing cumulative interest and capital paid.

    Args:
        df (pd.DataFrame): Amortization schedule dataframe
        currency_symbol (str): Currency symbol for formatting

    Returns:
        go.Figure: Plotly figure object
    """
    # Calculate cumulative totals
    cumulative_interest = df["Interest Portion"].cumsum()
    cumulative_capital = df["Capital Portion"].cumsum()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Period"],
            y=cumulative_capital,
            name="Cumulative Capital Paid",
            mode="lines",
            line={
                "width": 4,
                "color": Color.BLUE,
            },
            hovertemplate=(
                f"Period: %{{x}}<br>"  #
                f"Total Capital: {currency_symbol} %{{y:,.2f}}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Period"],
            y=cumulative_interest,
            name="Cumulative Interest Paid",
            mode="lines",
            line={
                "width": 4,
                "color": Color.RED,
            },
            hovertemplate=(
                f"Period: %{{x}}<br>"  #
                f"Total Interest: {currency_symbol} %{{y:,.2f}}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="",
        xaxis_title="Payment Period",
        yaxis_title=f"Cumulative Amount ({currency_symbol})",
        hovermode="x unified",
        height=500,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    return fig


class CalculationType(StrEnum):
    STANDARD_PAYMENT = "Standard Payment"
    DETAILED_PAYMENT = "Loan Amortization"


class SessionKeys(StrEnum):
    CHOSEN_CALCULATION = "chosen_calculation"


periodicity_mapping = {
    "Monthly": 12,
    "Quarterly": 4,
    "Semi-Annual": 2,
    "Annual": 1,
}

if SessionKeys.CHOSEN_CALCULATION not in st.session_state:
    st.session_state[SessionKeys.CHOSEN_CALCULATION] = CalculationType.DETAILED_PAYMENT


chosen_calculation = st.sidebar.selectbox(
    "What calculation would you like to perform?",
    [
        CalculationType.DETAILED_PAYMENT,
        CalculationType.STANDARD_PAYMENT,
    ],
    key=SessionKeys.CHOSEN_CALCULATION.value,
    index=0,
)

st.sidebar.divider()

match chosen_calculation:
    case CalculationType.STANDARD_PAYMENT:
        st.title(f"{chosen_calculation}")
        with st.sidebar:
            st.header("Input Parameters")
            rate = (
                st.number_input(
                    "Interest Rate (annual, %)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.01,
                    format="%.2f",
                    value=10.25,
                )
                / 100
            )
            period = st.selectbox(
                "Payment Periodicity",
                list(periodicity_mapping.keys()),
            )
            nper = st.number_input(
                f"Number of {period.lower()} payments in loan term",
                min_value=1,
                step=1,
                value=periodicity_mapping[period] * 20,
                format="%d",
            )
            pv = st.number_input(
                "Present Value (Principal)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
            )

        monthly_payment = -1 * pmt(
            rate=rate / periodicity_mapping[period],
            nper=nper,
            pv=pv,
        )
        st.metric(
            label="Payment Amount",
            value=f"{monthly_payment:,.2f}",
            delta=None,
            delta_color="normal",
        )

    case CalculationType.DETAILED_PAYMENT:
        st.title(f"{chosen_calculation}")

        with st.sidebar:
            st.header("Input Parameters")
            rate = (
                st.number_input(
                    "Interest Rate (annual, %)",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.01,
                    format="%.2f",
                    value=9.0,
                )
                / 100
            )
            period = st.selectbox(
                "Payment Periodicity",
                list(periodicity_mapping.keys()),
                index=0,
            )
            nper = st.number_input(
                f"Number of {period.lower()} payments in loan term",
                min_value=1,
                step=1,
                value=periodicity_mapping[period] * 20,
                format="%d",
            )
            pv = st.number_input(
                "Present Value (Principal)",
                min_value=0.0,
                step=1000.0,
                format="%.2f",
                value=3_000_000.0,
            )
            currency = st.text_input(
                "Currency Symbol",
                value="R",
                max_chars=3,
            )

        if pv > 0:
            df_schedule = generate_amortization_schedule(
                principal=pv,
                annual_rate=rate,
                nper=nper,
                periodicity=periodicity_mapping[period],
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                payment_amount = df_schedule["Payment Amount"].iloc[0]
                st.metric(
                    "Payment Amount",
                    f"{currency} {payment_amount:,.2f}",
                )

            with col2:
                st.metric(
                    "Total Capital Paid",
                    f"{currency} {df_schedule['Capital Portion'].sum():,.2f}",
                )

            with col3:
                st.metric(
                    "Total Interest Paid",
                    f"{currency} {df_schedule['Interest Portion'].sum():,.2f}",
                )

            with col4:
                st.metric(
                    "Total Amount Paid",
                    f"{currency} {df_schedule['Payment Amount'].sum():,.2f}",
                )

            tab1, tab2, tab3 = st.tabs(
                [
                    "Payment Breakdown",
                    "Cumulative Totals",
                    "Amortization Table",
                ]
            )

            with tab1:
                st.markdown("""
                This chart shows how each payment is split between interest (red) and capital (blue).
                Notice how early payments are mostly interest, while later payments are mostly capital.
                """)
                st.plotly_chart(
                    plot_amortization(df_schedule, currency),
                    use_container_width=True,
                )

            with tab2:
                st.markdown("""
                This chart shows the cumulative totals over time.
                The gap between the lines represents the total interest paid.
                """)
                st.plotly_chart(
                    plot_cumulative_totals(df_schedule, currency),
                    use_container_width=True,
                )

            with tab3:
                df_display = df_schedule.copy()

                # Format currency columns
                currency_cols = [
                    "Opening Balance",
                    "Payment Amount",
                    "Interest Portion",
                    "Capital Portion",
                    "Closing Balance",
                ]
                for col in currency_cols:
                    df_display[col] = df_display[col].apply(lambda x: f"{currency}{x:,.2f}")

                df_display["Annual Interest Rate (%)"] = df_display["Annual Interest Rate (%)"].apply(
                    lambda x: f"{x:.2f}"
                )

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    height=600,
                )

                csv = df_schedule.to_csv(index=False)
                st.download_button(
                    label="Download Amortization Schedule (CSV)",
                    data=csv,
                    file_name="amortization_schedule.csv",
                    mime="text/csv",
                )
        else:
            st.info("Please enter a principal amount greater than 0 to generate the amortization schedule.")
