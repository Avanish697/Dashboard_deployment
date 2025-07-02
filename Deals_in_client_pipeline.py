import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import urllib
import sqlalchemy
import warnings
import dash_bootstrap_components as dbc

warnings.simplefilter("ignore")

# SQL Server Connection
server = 'valentasql.database.windows.net'
database = 'Xero_CRM'
username = 'valdb'
password = 'Valenta@1234'
table_name = 'dbo.DEALS'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
)

engine = sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Clean numeric columns
for col in ["Amount", "Consulting Fee"]:
    if col in df.columns and not df[col].isnull().all():
        df[col] = df[col].astype(str).replace({r'[$,]': ''}, regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

df["Closing Date"] = pd.to_datetime(df["Closing Date"], errors='coerce')
df["Closing Month"] = df["Closing Date"].dt.strftime("%b-%Y")

current_month = pd.Timestamp.now().strftime("%b-%Y")
next_month = (pd.Timestamp.now() + pd.DateOffset(months=1)).strftime("%b-%Y")

# Dropdown Style
dropdown_style = {
    "width": "320px",
    "backgroundColor": "white",
    "color": "black",
    "border": "1px",
    "borderRadius": "5px",
    "fontSize": "16px",
    "boxShadow": "none",
    "outline": "none",
    "height": "38px"
}

# KPI Card function
def kpi_card_white(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.H4(value, className="mb-0", style={"color": "white", "fontWeight": "bold", "fontSize": "24px"}),
            html.P(title, className="mb-0", style={"color": "white", "fontSize": "14px"})
        ]),
        className="text-left shadow-sm",
        style={
            "backgroundColor": "#2b2b2b",
            "borderRadius": "10px",
            "padding": "10px",
            "minWidth": "200px",
            "boxShadow": "2px 2px 8px #000"
        }
    )

# Layout
client_layout = html.Div(style={"backgroundColor": "black", "color": "white", "padding": "20px"}, children=[
    html.Div([
        dcc.Dropdown(
            id="deal_owner",
            multi=True,
            placeholder="Select Deal Owner",
            style=dropdown_style
        ),
        dcc.Dropdown(
            id="closing_month",
            multi=True,
            options=[
                {"label": "This Month", "value": "this_month"},
                {"label": "Next Month", "value": "next_month"},
                {"label": "Other", "value": "other"}
            ],
            placeholder="Select Closing Month",
            style=dropdown_style
        )
    ], style={
        "display": "flex",
        "gap": "15px",
        "padding": "10px",
        "borderRadius": "8px",
        "justifyContent": "center",
        "marginBottom": "25px"
    }),

    html.Div(id="kpi_cards", style={"display": "flex", "justifyContent": "center", "gap": "20px", "marginBottom": "30px"}),

    html.Div(id="custom_stage_table", style={"padding": "10px"}),

    dcc.Graph(id="bar_chart", config={"displayModeBar": False})
])

# Callback
def register_client_callbacks(app):
    @app.callback(
        [Output("deal_owner", "options"),
         Output("kpi_cards", "children"),
         Output("custom_stage_table", "children"),
         Output("bar_chart", "figure")],
        [Input("deal_owner", "value"),
         Input("closing_month", "value")]
    )
    def update_dashboard(deal_owner, closing_month):
        # ✅ Only consider ACTIVE employees
        active_df = df[df["Status"].str.lower() == "active"]

        # Filter by allowed stages
        filtered_df = active_df[active_df["Stage"].isin([
            "Agreement Signed", "Awareness", "Closed (Future prospect)", "Closed (Lost)", "Did Not Proceed",
            "Discovery", "Engagement Completed", "Implementation", "Issue Agreement", "Needs Identified",
            "Ongoing Services", "Prospect"
        ])]

        if deal_owner:
            filtered_df = filtered_df[filtered_df["Deal Owner Name"].isin(deal_owner)]

        if closing_month:
            filters = []
            if "this_month" in closing_month:
                filters.append(filtered_df["Closing Month"] == current_month)
            if "next_month" in closing_month:
                filters.append(filtered_df["Closing Month"] == next_month)
            if "other" in closing_month:
                filters.append(~filtered_df["Closing Month"].isin([current_month, next_month]))
            if filters:
                filtered_df = filtered_df[pd.concat(filters, axis=1).any(axis=1)]

        # ✅ Dropdown options from ACTIVE employees only
        deal_owner_options = [{"label": owner, "value": owner} for owner in sorted(active_df["Deal Owner Name"].dropna().unique())]

        # KPI Cards
        ongoing_revenue = filtered_df["Amount"].sum()
        onetime_revenue = filtered_df["Consulting Fee"].sum()
        deals_closing = filtered_df.shape[0]

        kpi_cards = [
            kpi_card_white("Ongoing Revenue", f"${ongoing_revenue:,.2f}"),
            kpi_card_white("One-Time Revenue", f"${onetime_revenue:,.2f}"),
            kpi_card_white("Deals Closing", f"{deals_closing}")
        ]

        # Stage Summary Table
        stage_summary = filtered_df.groupby("Stage").size().reset_index(name="Deals_In_Pipeline")
        stage_summary["%GT Deals_In_Pipeline"] = (
            (stage_summary["Deals_In_Pipeline"] / stage_summary["Deals_In_Pipeline"].sum()) * 100
        ).round(2).astype(str) + "%"

        stage_summary.loc[len(stage_summary)] = [
            "Total",
            stage_summary["Deals_In_Pipeline"].sum(),
            "100.00%"
        ]

        table_header = html.Thead([
            html.Tr([
                html.Th(col, style={"border": "1px solid white", "padding": "8px", "textAlign": "center", "fontWeight": "bold",
        "fontSize": "18px",})
                for col in stage_summary.columns
            ])
        ])

        table_rows = []
        for _, row in stage_summary.iterrows():
            table_rows.append(
                html.Tr([
                    html.Td(row[col], style={"border": "1px solid white", "padding": "8px", "textAlign": "center"})
                    for col in stage_summary.columns
                ])
            )

        custom_table = html.Table(
            children=[table_header, html.Tbody(table_rows)],
            style={
                "width": "100%",
                "borderCollapse": "collapse",
                "backgroundColor": "#2d2d2d",
                "color": "white",
                "fontSize": "14px",
                "border": "1px solid white"
            }
        )

        # Bar Chart
        df_grouped = filtered_df.groupby(["Deal Owner Name", "Stage"]).size().reset_index(name="Deals_In_Pipeline")
        df_grouped["Label"] = df_grouped["Deals_In_Pipeline"].astype(str)

        total_deals_per_owner = df_grouped.groupby("Deal Owner Name")["Deals_In_Pipeline"].sum().reset_index()
        sorted_owners = total_deals_per_owner.sort_values(by="Deals_In_Pipeline", ascending=False)["Deal Owner Name"]

        bar_chart = px.bar(
            df_grouped,
            x="Deals_In_Pipeline",
            y="Deal Owner Name",
            color="Stage",
            text="Label",
            category_orders={"Deal Owner Name": sorted_owners.tolist()},
            orientation="h"
        )

        bar_chart.update_layout(
            title="Deals in Pipeline by Deal Owner Name and Stage",
            xaxis_title="Deals in Pipeline",
            yaxis_title="",
            plot_bgcolor="black",
            paper_bgcolor="black",
            font=dict(color="white", size=14),
            barmode="stack",
            height=100 + len(sorted_owners) * 70,
            margin=dict(l=220, r=40, t=60, b=60),
            legend_title_text="Stage",
            bargap=0.1,
            bargroupgap=0.05
        )

        bar_chart.update_traces(
            textposition="inside",
            textfont=dict(size=12, color="white"),
            marker_line=dict(width=1, color="black")
        )

        return deal_owner_options, kpi_cards, custom_table, bar_chart
