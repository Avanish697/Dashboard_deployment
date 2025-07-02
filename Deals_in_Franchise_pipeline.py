import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output
from sqlalchemy import create_engine
import urllib
import datetime
import dash_bootstrap_components as dbc

# ✅ Fetch data from SQL Server
server = 'valentasql.database.windows.net'
database = 'Xero_CRM'
username = 'valdb'
password = 'Valenta@1234'
table_name = 'dbo.DEALS'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

# ✅ Clean and preprocess data
df["Amount"] = df["Amount"].replace({r'\$': '', ',': ''}, regex=True).astype(float)
df["Closing Date"] = pd.to_datetime(df["Closing Date"], errors='coerce')
df["Closing Month"] = df["Closing Date"].dt.strftime("%b-%Y")

# ✅ Time References
current_month = pd.Timestamp.now().strftime("%b-%Y")
next_month = (pd.Timestamp.now() + pd.DateOffset(months=1)).strftime("%b-%Y")

# ✅ Franchise Valid Stages
valid_stages = [
    "New Lead", "Introduction Meeting", "FDD Review",
    "Application Form & Background Verification"
]

# ✅ Filter only active employees once
active_df = df[df["Status"].str.lower() == "active"]

# ✅ Dropdown style
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

# ✅ KPI Card component
def kpi_card(title, value):
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

# ✅ Layout
franchise_layout = html.Div(style={"backgroundColor": "black", "color": "white", "padding": "10px"}, children=[

    html.Div([
        dcc.Dropdown(id="franchise_deal_owner",
                     multi=True,
                     options=[{"label": i, "value": i} for i in sorted(active_df["Deal Owner Name"].dropna().unique())],
                     placeholder="Deal Owner Name",
                     style=dropdown_style),

        dcc.Dropdown(id="franchise_closing_month",
                     multi=True,
                     options=[
                         {"label": "This Month", "value": "this_month"},
                         {"label": "Next Month", "value": "next_month"},
                         {"label": "Other", "value": "other"}
                     ],
                     placeholder="Closing Month",
                     style=dropdown_style),

        dcc.Dropdown(id="franchise_region",
                     multi=True,
                     options=[{"label": "All", "value": "All"}] + (
                         [{"label": i, "value": i} for i in sorted(active_df["Region"].dropna().unique())]
                         if "Region" in active_df.columns else []
                     ),
                     placeholder="Region",
                     style=dropdown_style)
    ], style={"display": "flex", "gap": "10px", "padding": "10px", "marginLeft": "30px"}),

    html.Div(id="franchise_kpi_cards", style={"display": "flex", "justifyContent": "center", "gap": "20px", "padding": "20px"}),

    html.Div(id="franchise_stage_table_div", style={"padding": "10px"}),

    dcc.Graph(id="franchise_bar_chart")
])

# ✅ Callbacks
def register_franchise_callbacks(app):
    @app.callback(
        [Output("franchise_kpi_cards", "children"),
         Output("franchise_stage_table_div", "children"),
         Output("franchise_bar_chart", "figure")],
        [Input("franchise_deal_owner", "value"),
         Input("franchise_closing_month", "value"),
         Input("franchise_region", "value")]
    )
    def update_franchise(deal_owner, closing_month, region):
        filtered_df = active_df[active_df["Stage"].isin(valid_stages)]

        if deal_owner:
            filtered_df = filtered_df[filtered_df["Deal Owner Name"].isin(deal_owner)]

        if closing_month:
            month_filters = []
            if "this_month" in closing_month:
                month_filters.append(filtered_df["Closing Month"] == current_month)
            if "next_month" in closing_month:
                month_filters.append(filtered_df["Closing Month"] == next_month)
            if "other" in closing_month:
                month_filters.append(~filtered_df["Closing Month"].isin([current_month, next_month]))
            if month_filters:
                filtered_df = filtered_df[pd.concat(month_filters, axis=1).any(axis=1)]

        if region:
            if "All" not in region and "Region" in active_df.columns:
                filtered_df = filtered_df[filtered_df["Region"].isin(region)]

        # ✅ KPI Cards
        ongoing_revenue = filtered_df["Amount"].sum() if not filtered_df.empty else 0
        deals_closing = filtered_df.shape[0]

        kpi_cards = [
            kpi_card("Ongoing Revenue", f"${ongoing_revenue:,.2f}"),
            kpi_card("Deals Closing", f"{deals_closing}")
        ]

        # ✅ Table
        if not filtered_df.empty:
            stage_summary = filtered_df.groupby("Stage").size().reset_index(name="Deals_In_Pipeline")
            stage_summary["%GT Deals_In_Pipeline"] = (
                (stage_summary["Deals_In_Pipeline"] / stage_summary["Deals_In_Pipeline"].sum()) * 100
            ).map("{:.2f}%".format)
            stage_summary.loc[len(stage_summary)] = [
                "Total", stage_summary["Deals_In_Pipeline"].sum(), "100.00%"
            ]
        else:
            stage_summary = pd.DataFrame(columns=["Stage", "Deals_In_Pipeline", "%GT Deals_In_Pipeline"])

        # ✅ Build HTML Table
        table_header = html.Thead(html.Tr([
            html.Th(col, style={"border": "1px solid white", "padding": "8px"}) for col in stage_summary.columns
        ]))

        table_rows = [
            html.Tr([
                html.Td(row[col], style={"border": "1px solid white", "padding": "8px"}) for col in stage_summary.columns
            ]) for _, row in stage_summary.iterrows()
        ]

        table = html.Table(
            children=[table_header, html.Tbody(table_rows)],
            style={
                "width": "100%",
                "borderCollapse": "collapse",
                "backgroundColor": "#2d2d2d",
                "color": "white",
                "fontSize": "18px",
                "fontWeight": "bold",
                "border": "1px solid white"
                
        
            }
        )

        # ✅ Bar Chart
        if not filtered_df.empty:
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
                title="Deals in Franchise Pipeline by Deal Owner Name and Stage",
                xaxis_title="Deals in Pipeline",
                yaxis_title="Deal Owner Name",
                plot_bgcolor="black",
                paper_bgcolor="black",
                font=dict(color="white", size=14),
                barmode="stack",
                height=140 + len(sorted_owners) * 70,
                margin=dict(l=180, r=30, t=80, b=40)
            )
        else:
            bar_chart = px.bar(title="No data available for the selected filters")
            bar_chart.update_layout(
                plot_bgcolor="black",
                paper_bgcolor="black",
                font=dict(color="white", size=14)
            )

        return kpi_cards, table, bar_chart
