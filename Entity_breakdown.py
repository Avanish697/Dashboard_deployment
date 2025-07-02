import pandas as pd
import urllib
import sqlalchemy
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

# Database configuration
server = 'valentasql.database.windows.net'
database = 'Xero_CRM'
username = 'valdb'
password = 'Valenta@1234'
table_name = 'dbo.INVOICES'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
)
engine = sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Preprocessing
df['Invoice_Date'] = pd.to_datetime(df['Invoice_Date'])
df['Year'] = df['Invoice_Date'].dt.year
df = df[df['Year'] >= 2014]  # ✅ Only include years from 2014
df['Quarter'] = "Q" + df['Invoice_Date'].dt.quarter.astype(str)
df['Month'] = df['Invoice_Date'].dt.month_name()

years = sorted(df['Year'].dropna().unique())
years = [str(int(year)) for year in years]
quarters = ['Q1', 'Q2', 'Q3', 'Q4']
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
months = sorted(df['Month'].dropna().unique(), key=lambda x: month_order.index(x))

# Quarter to months mapping
quarter_to_months = {
    'Q1': ['January', 'February', 'March'],
    'Q2': ['April', 'May', 'June'],
    'Q3': ['July', 'August', 'September'],
    'Q4': ['October', 'November', 'December'],
}

# Styled KPI cards
def styled_card(value, title, color):
    color_codes = {"green": "#00FF00", "red": "#FF0000", "orange": "#FFA500"}
    return dbc.Card(
        dbc.CardBody([
            html.H4(value, className="mb-0", style={"color": color_codes.get(color, "white"), "fontWeight": "bold"}),
            html.P(title, className="mb-0", style={"color": "white", "fontSize": "14px"}),
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
layout = html.Div([  
    dbc.Container([
        html.Div([], className="mb-3 text-center"),

        dbc.Row([
            dbc.Col(dcc.Dropdown(
                options=[{"label": str(y), "value": str(y)} for y in years],
                value=None,
                id="year-dropdown",
                placeholder="Select Year",
                style={"color": "black"},
                multi=True
            ), width=3),
            dbc.Col(dcc.Dropdown(
                options=[{"label": q, "value": q} for q in quarters],
                value=None,
                id="quarter-dropdown",
                placeholder="Select Quarter",
                style={"color": "black"},
                multi=True
            ), width=3),
            dbc.Col(dcc.Dropdown(
                options=[{"label": m, "value": m} for m in months],
                value=None,
                id="month-dropdown",
                placeholder="Select Month",
                style={"color": "black"},
                multi=True
            ), width=3),
        ], className="mb-4 justify-content-center"),

        dbc.Row([
            dbc.Col(html.Div(id="invoice-amount-card", style={"marginRight": "10px"}), xs=6, sm=4, md=2),
            dbc.Col(html.Div(id="paid-amount-card", style={"marginRight": "10px"}), xs=6, sm=4, md=2),
            dbc.Col(html.Div(id="paid-percent-card", style={"marginRight": "10px"}), xs=6, sm=4, md=2),
            dbc.Col(html.Div(id="receivables-card", style={"marginRight": "10px"}), xs=6, sm=4, md=2),
            dbc.Col(html.Div(id="receivables-percent-card", style={"marginRight": "10px"}), xs=6, sm=4, md=2),
        ], className="gx-3 gy-3 mb-5 justify-content-center"), 

        dbc.Row([
            dbc.Col(dcc.Graph(id="entity-table", style={"height": "600px"}, config={"modeBarButtonsToRemove": ["toImage"]}), width=6),
            dbc.Col(dcc.Graph(id="invoice-receivable-chart"), width=6)
        ])
    ], fluid=True)
], style={"backgroundColor": "#000000", "color": "white", "minHeight": "100vh", "padding": "20px"})

# Update Dashboard
def update_dashboard(year, quarter, month, user_data):
    username = user_data.get("username") if user_data else None
    dff = df.copy()

    if username != 'admin' and username is not None:
        dff = dff[dff["Location"] == username]

    if year:
        dff = dff[dff['Year'].isin([int(y) for y in year])]
    
    if quarter:
        if isinstance(quarter, str):
            quarter = [quarter]
        months_from_quarters = sum([quarter_to_months[q] for q in quarter if q in quarter_to_months], [])
        dff = dff[dff['Month'].isin(months_from_quarters)]

    if month:
        dff = dff[dff['Month'].isin(month)]

    total_invoice = dff['Invoice_Amount_USD'].sum()
    paid_amount = dff['Invoice_Amount_USD'] - dff['Quantity']
    total_paid = paid_amount.sum()
    receivables = total_invoice - total_paid

    paid_pct = round((total_paid / total_invoice) * 100, 2) if total_invoice else 0
    recv_pct = round((receivables / total_invoice) * 100, 2) if total_invoice else 0

    by_entity = dff.groupby('Invoice_Entity').agg({
        'Invoice_Amount_USD': 'sum',
        'Quantity': 'sum'
    }).reset_index()

    by_entity['Paid_Amount'] = by_entity['Invoice_Amount_USD'] - by_entity['Quantity']
    by_entity['Paid %'] = (by_entity['Paid_Amount'] / by_entity['Invoice_Amount_USD']) * 100
    by_entity['Receivables'] = by_entity['Quantity']
    by_entity['Receivables %'] = (by_entity['Receivables'] / by_entity['Invoice_Amount_USD']) * 100
    by_entity = by_entity.drop(columns=['Quantity'])

    total_row = pd.DataFrame({
        'Invoice_Entity': ['Total'],
        'Invoice_Amount_USD': [by_entity['Invoice_Amount_USD'].sum()],
        'Paid_Amount': [by_entity['Paid_Amount'].sum()],
        'Paid %': [round((by_entity['Paid_Amount'].sum() / by_entity['Invoice_Amount_USD'].sum()) * 100, 2)],
        'Receivables': [by_entity['Receivables'].sum()],
        'Receivables %': [round((by_entity['Receivables'].sum() / by_entity['Invoice_Amount_USD'].sum()) * 100, 2)]
    })

    by_entity = pd.concat([by_entity, total_row], ignore_index=True)

    for col in ['Invoice_Amount_USD', 'Paid_Amount', 'Receivables']:
        by_entity[col] = by_entity[col].apply(lambda x: f"{x:,.0f}")
    by_entity['Paid %'] = by_entity['Paid %'].apply(lambda x: f"{x:.2f}%")
    by_entity['Receivables %'] = by_entity['Receivables %'].apply(lambda x: f"{x:.2f}%")

    by_entity_fig = go.Figure(data=[go.Table(
        header=dict(values=list(by_entity.columns),
                    fill_color="#2a2a2a",
                    font=dict(color="white", size=18),
                    align="left",
                    height=32),
        cells=dict(values=[by_entity[col] for col in by_entity.columns],
                   fill_color=[
                       ['#1f1f1f'] * (len(by_entity) - 1) + ['#333333']
                       for _ in range(len(by_entity.columns))
                   ],
                   font=dict(color="white", size=15),
                   align="left",
                   height=30)
    )])
    by_entity_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                paper_bgcolor="#000000", plot_bgcolor="#000000")

    by_year = dff.groupby('Year').agg({
        'Invoice_Amount_USD': 'sum',
        'Quantity': 'sum'
    }).reset_index()
    by_year['Receivables'] = by_year['Quantity']

    chart = go.Figure()
    chart.add_trace(go.Bar(x=by_year['Year'], y=by_year['Invoice_Amount_USD'],
                           name='Invoice Amount', marker_color='#00BFFF'))
    chart.add_trace(go.Scatter(x=by_year['Year'], y=by_year['Receivables'],
                               name='Receivables', yaxis='y2', line=dict(color='orange', width=3)))

    chart.update_layout(
        paper_bgcolor="#000000", plot_bgcolor="#000000", font_color="white",
        yaxis=dict(title='Invoice Amount', showgrid=False, zeroline=False),
        yaxis2=dict(title='Receivables', overlaying='y', side='right', showgrid=False, zeroline=False),
        legend=dict(x=0, y=1.2, orientation='h'),
        bargap=0.3, margin=dict(t=20, b=20, l=0, r=0), height=400
    )

    return (
        styled_card(f"${total_invoice:,.0f}", "Invoice Amount", "green"),
        styled_card(f"${total_paid:,.0f}", "Paid Amount", "green"),
        styled_card(f"{paid_pct}%", "Paid %", "green"),
        styled_card(f"${receivables:,.0f}", "Receivables", "red"),
        styled_card(f"{recv_pct}%", "Receivables %", "red"),
        by_entity_fig,
        chart
    )

# Callback Registration
def register_callbacks(app):
    app.callback(
        [Output("invoice-amount-card", "children"),
         Output("paid-amount-card", "children"),
         Output("paid-percent-card", "children"),
         Output("receivables-card", "children"),
         Output("receivables-percent-card", "children"),
         Output("entity-table", "figure"),
         Output("invoice-receivable-chart", "figure")],
        [Input("year-dropdown", "value"),
         Input("quarter-dropdown", "value"),
         Input("month-dropdown", "value"),
         Input("user-store", "data")]
    )(update_dashboard)
