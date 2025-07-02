import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
from sqlalchemy import create_engine
import urllib

# SQL Server connection setup
server = 'valentasql.database.windows.net'
database = 'Xero_CRM'
username = 'valdb'
password = 'Valenta@1234'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# Load full views
def load_view(view_name):
    try:
        return pd.read_sql(f"SELECT * FROM {view_name}", engine)
    except Exception as e:
        print(f"Error loading view {view_name}: {e}")
        return pd.DataFrame()

# KPI functions
def get_mp_commission(engine):
    query = """
        SELECT SUM([MP_Commission]) AS total_commission
        FROM [dbo].[MP/MD COMMISSIONS]
        WHERE [Status] = 'PAID'
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0, 0] if not df.empty and pd.notna(df.iloc[0, 0]) else 0

def get_practice_mp_commission(engine):
    query = """
        SELECT SUM([Practice MP Commission]) AS total_commission
        FROM [dbo].[PRACTICE_MP]
        WHERE [Status] = 'PAID'
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0, 0] if not df.empty and pd.notna(df.iloc[0, 0]) else 0

def get_third_party_commission(engine):
    query = """
        SELECT SUM([3rd Party Payout 1]) AS total_commission
        FROM [dbo].[3RD_PARTY COMMISSION]
        WHERE [Status] = 'PAID'
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0, 0] if not df.empty and pd.notna(df.iloc[0, 0]) else 0

def get_mp_as_pm_commission(engine):
    query = """
        SELECT SUM([MP as PM Commission]) AS total_commission
        FROM [dbo].[MP as PM COMMISSION]
        WHERE [Status] = 'PAID'
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0, 0] if not df.empty and pd.notna(df.iloc[0, 0]) else 0

def get_practice_md_commission(engine):
    query = """
        SELECT SUM([Practice MD Commission]) AS total_commission
        FROM [dbo].[PRACTICE_MD]
        WHERE [Status] = 'PAID'
    """
    df = pd.read_sql(query, engine)
    return "${:,.0f}".format(df.iloc[0, 0]) if not df.empty and pd.notna(df.iloc[0, 0]) else "$0"

def get_total_commission(engine):
    mp = get_mp_commission(engine)
    pmp = get_practice_mp_commission(engine)
    tp = get_third_party_commission(engine)
    mp_pm = get_mp_as_pm_commission(engine)
    total = mp + pmp + tp + mp_pm
    return "${:,.0f}".format(total)

def format_dollar(value):
    return "${:,.0f}".format(value) if pd.notna(value) else "$0"

# Load chart data
practice_mp_df = load_view("[dbo].[PRACTICE_MP]")

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Commission Dashboard"

# Base card style
card_base_style = {
    "backgroundColor": "#2c2c2c",
    "borderRadius": "10px",
    "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.8)",
    "padding": "10px 15px",
    "margin": "5px",
    "textAlign": "center",
    "color": "white",
    "border": "1px solid #444",
    "transition": "0.3s",
    "cursor": "pointer"
}

# Layout
app.layout = dbc.Container([
    html.Br(),
    dbc.Row([
        dbc.Col(html.Img(src="assets/valenta_logo.png", height="60px"), width=3),
        dbc.Col(html.H3("Commission Overview", className="text-white"), width=9),
    ], align="center"),

    html.Hr(),

    dbc.Row([
        dbc.Col(html.Div([
            html.H4(format_dollar(get_mp_commission(engine)), style={"color": "#80ff00", "fontWeight": "bold"}),
            html.Div("MP Commission", style={"color": "#80ff00", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 10px #80ff00"}), width=2),

        dbc.Col(html.Div([
            html.H4(format_dollar(get_practice_mp_commission(engine)), style={"color": "#ffff33", "fontWeight": "bold"}),
            html.Div("Practice MP Comm", style={"color": "#ffff33", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 10px #ffff33"}), width=2),

        dbc.Col(html.Div([
            html.H4(format_dollar(get_third_party_commission(engine)), style={"color": "#ffcc00", "fontWeight": "bold"}),
            html.Div("3rd Party Comm", style={"color": "#ffcc00", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 10px #ffcc00"}), width=2),

        dbc.Col(html.Div([
            html.H4(format_dollar(get_mp_as_pm_commission(engine)), style={"color": "#33d1ff", "fontWeight": "bold"}),
            html.Div("MP as PM Comm", style={"color": "#33d1ff", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 10px #33d1ff"}), width=2),

        dbc.Col(html.Div([
            html.H4(get_practice_md_commission(engine), style={"color": "#00ff80", "fontWeight": "bold"}),
            html.Div("Practice MD Comm", style={"color": "#00ff80", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 10px #00ff80"}), width=2),

        dbc.Col(html.Div([
            html.H4(get_total_commission(engine), style={"color": "#ff66cc", "fontWeight": "bold"}),
            html.Div("Total Commission", style={"color": "#ff66cc", "fontSize": "14px", "fontWeight": "bold"})
        ], style={**card_base_style, "boxShadow": "0 0 12px #ff66cc"}), width=2),
    ]),

    html.Br(),

    dbc.Row([
        dbc.Col(dcc.Graph(
            id="bar-chart",
            figure={
                "data": [dict(
                    x=practice_mp_df["Month"] if "Month" in practice_mp_df else [],
                    y=practice_mp_df["Invoice_Amount"] if "Invoice_Amount" in practice_mp_df else [],
                    type="bar",
                    name="Practice MP by Month",
                    marker={"color": "#3399ff"}
                )],
                "layout": {
                    "title": "Practice MP by Month",
                    "plot_bgcolor": "#1e1e1e",
                    "paper_bgcolor": "#1e1e1e",
                    "font": {"color": "white"},
                    "xaxis": {"title": "Month"},
                    "yaxis": {"title": "Invoice Amount"}
                }
            }
        ), width=12)
    ]),
], fluid=True, style={"backgroundColor": "#1e1e1e"})

if __name__ == "__main__":
    app.run(debug=True)
