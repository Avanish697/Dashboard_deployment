import pandas as pd
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import urllib
from sqlalchemy import create_engine
from dash.dcc import send_data_frame

# Dropdown style
dropdown_style = {
    "width": "100%",
    "backgroundColor": "white",
    "color": "black",
    "border": "1px",
    "borderRadius": "5px",
    "fontSize": "16px",
    "boxShadow": "none",
    "outline": "none",
    "height": "38px"
}

# Fetch data from SSMS
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

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Clean Status - keep only active deals
df['Status'] = df['Status'].astype(str).str.strip().str.lower()
df = df[df['Status'] == 'active']

# Clean Deal Owner Name
df['Deal Owner Name'] = df['Deal Owner Name'].astype(str).str.strip()
df['Deal Owner Name'] = df['Deal Owner Name'].replace('', 'Unknown').fillna('Unknown')

# Select relevant columns
df = df[["Deal Owner Name", "Deal Name", "Stage", "Closing Date", "Sales Cycle Duration", "Billing Company"]]

# Convert Closing Date, allow NaT for invalid dates
df["Closing Date"] = pd.to_datetime(df["Closing Date"], errors='coerce')

# Dropdown options
years = sorted(df["Closing Date"].dropna().dt.year.unique())
months = [
    {'label': 'January', 'value': 1}, {'label': 'February', 'value': 2},
    {'label': 'March', 'value': 3}, {'label': 'April', 'value': 4},
    {'label': 'May', 'value': 5}, {'label': 'June', 'value': 6},
    {'label': 'July', 'value': 7}, {'label': 'August', 'value': 8},
    {'label': 'September', 'value': 9}, {'label': 'October', 'value': 10},
    {'label': 'November', 'value': 11}, {'label': 'December', 'value': 12}
]
deal_owners = sorted(df["Deal Owner Name"].unique())
billing_companies = sorted(df["Billing Company"].dropna().unique())

# KPI Card function
def kpi_card(title, value, color="white"):
    return dbc.Card(
        dbc.CardBody([
            html.H4(value, className="mb-0", style={"color": "#FFFFFF", "fontWeight": "bold"}),
            html.P(title, className="mb-0", style={"color": "white", "fontSize": "14px"})
        ]),
        className="text-left shadow-sm",
        style={
            "backgroundColor": "#2b2b2b",
            "borderRadius": "10px",
            "padding": "10px",
            "width": "180px",
            "minWidth": "180px",
            "boxShadow": "2px 2px 8px #000"
        }
    )

# Layout
sales_cycle_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='year_filter_sales_cycle',
                options=[{'label': y, 'value': y} for y in years],
                placeholder='Year',
                clearable=True,
                multi=True,
                style=dropdown_style
            )
        ], width=2),

        dbc.Col([
            dcc.Dropdown(
                id='month_filter_sales_cycle',
                options=months,
                placeholder='Month',
                clearable=True,
                multi=True,
                style=dropdown_style
            )
        ], width=2),

        dbc.Col([
            dcc.Dropdown(
                id='deal_owner_filter_sales_cycle',
                options=[{'label': d, 'value': d} for d in deal_owners],
                placeholder='Deal Owner Name',
                clearable=True,
                multi=True,
                style=dropdown_style
            )
        ], width=2),

        dbc.Col([
            dcc.Dropdown(
                id='billing_company_filter_sales_cycle',
                options=[{'label': b, 'value': b} for b in billing_companies],
                placeholder='Billing Company',
                clearable=True,
                multi=True,
                style=dropdown_style
            )
        ], width=2),
    ], className="mb-4", style={"gap": "20px"}),

    dbc.Row([
        dbc.Col(
            html.Div(id='kpi_card_output'),
            width=2
        )
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(
            dash_table.DataTable(
                id='deal_table_sales_cycle',
                columns=[
                    {'name': 'Deal Owner Name', 'id': 'Deal Owner Name'},
                    {'name': 'Deal Name', 'id': 'Deal Name'},
                    {'name': 'Sales Cycle Duration', 'id': 'Sales Cycle Duration'},
                    {'name': 'Stage', 'id': 'Stage'},
                    {'name': 'Billing Company', 'id': 'Billing Company'},
                ],
                data=df.to_dict("records"),
                page_size=15,
                style_table={
                    'width': '100%',
                    'borderCollapse': 'collapse',
                    'overflowX': 'auto',
                    'minHeight': '500px',
                    'backgroundColor': '#2d2d2d',
                    'border': '1px solid white'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'color': 'white',
                    'backgroundColor': '#2d2d2d',
                    'fontSize': '14px',
                    'border': '1px solid white'
                },
                style_header={
                    'backgroundColor': '#2d2d2d',
                    'color': 'white',
                    'fontWeight': 'bold',
                    "fontSize": "18px",
                    'border': '1px solid white'
                    
                },
                style_data={
                    'border': '1px solid white'
                }
            ),
            width=12
        )
    ]),

    dbc.Row([
        dbc.Col([], width=9),
        dbc.Col([
            dbc.Button("Export CSV", id="export_sales_cycle_btn", color="success", className="mt-3"),
            dcc.Download(id="download_sales_cycle_csv")
        ], width=3, style={'textAlign': 'right'})
    ])
], fluid=True)

# Callbacks
def register_sales_cycle_callbacks(app):
    @app.callback(
        [
            Output('deal_table_sales_cycle', 'data'),
            Output('kpi_card_output', 'children')
        ],
        [
            Input('year_filter_sales_cycle', 'value'),
            Input('month_filter_sales_cycle', 'value'),
            Input('deal_owner_filter_sales_cycle', 'value'),
            Input('billing_company_filter_sales_cycle', 'value'),
        ]
    )
    def update_table(year, month, deal_owner, billing_company):
        filtered_df = df.copy()

        if year:
            filtered_df = filtered_df[filtered_df["Closing Date"].notna() & filtered_df["Closing Date"].dt.year.isin(year)]

        if month:
            filtered_df = filtered_df[filtered_df["Closing Date"].notna() & filtered_df["Closing Date"].dt.month.isin(month)]

        if deal_owner:
            filtered_df = filtered_df[filtered_df["Deal Owner Name"].isin(deal_owner)]

        if billing_company:
            filtered_df = filtered_df[filtered_df["Billing Company"].isin(billing_company)]

        avg_cycle = round(filtered_df["Sales Cycle Duration"].dropna().mean(), 2) if not filtered_df.empty else 0
        kpi = kpi_card("Average Sales Cycle", f"{avg_cycle} days", color="white")

        return filtered_df.to_dict("records"), kpi

    @app.callback(
        Output("download_sales_cycle_csv", "data"),
        Input("export_sales_cycle_btn", "n_clicks"),
        State('deal_table_sales_cycle', 'data'),
        prevent_initial_call=True,
    )
    def export_csv(n_clicks, table_data):
        export_df = pd.DataFrame(table_data)
        return send_data_frame(export_df.to_csv, filename="Sales_Cycle_Deals.csv", index=False)
