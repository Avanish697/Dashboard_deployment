import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
from sqlalchemy import create_engine
import urllib

# --- SQL Server Connection ---
server = 'valentasql.database.windows.net'
database = 'Xero_CRM'
username = 'valdb'
password = 'Valenta@1234'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# --- Helper Functions ---
def format_dollar(value):
    return "${:,.0f}".format(value) if pd.notna(value) else "$0"

def fetch_locations():
    try:
        query = """
            SELECT DISTINCT TRIM([Location]) AS Location FROM (
                SELECT [Location] FROM [dbo].[MP/MD COMMISSIONS]
                UNION
                SELECT [Location] FROM [dbo].[MP as PM COMMISSION]
                UNION
                SELECT [Location] FROM [dbo].[PRACTICE_MP]
                UNION
                SELECT [Location] FROM [dbo].[3RD_PARTY COMMISSION]
                UNION
                SELECT [Location] FROM [dbo].[PRACTICE_MD]
            ) AS AllLocations
            WHERE [Location] IS NOT NULL AND TRIM([Location]) <> ''
        """
        df = pd.read_sql(query, engine)
        df['Location'] = df['Location'].str.strip()
        return [{'label': loc, 'value': loc} for loc in sorted(df['Location'].unique())]
    except Exception as e:
        print("Error fetching locations:", e)
        return []

def fetch_departments():
    try:
        query = """
            SELECT DISTINCT TRIM([Department]) AS Department
            FROM [dbo].[MP/MD COMMISSIONS]
            WHERE [Department] IS NOT NULL AND TRIM([Department]) <> ''
        """
        df = pd.read_sql(query, engine)
        df['Department'] = df['Department'].str.strip()
        return [{'label': dept, 'value': dept} for dept in sorted(df['Department'].unique())]
    except Exception as e:
        print("Error fetching departments:", e)
        return []

def fetch_practice_mps():
    try:
        query = """
            SELECT DISTINCT TRIM([Practice MP Name]) AS PracticeMPName
            FROM [dbo].[PRACTICE_MP]
            WHERE [Practice MP Name] IS NOT NULL AND TRIM([Practice MP Name]) <> ''
        """
        df = pd.read_sql(query, engine)
        df['PracticeMPName'] = df['PracticeMPName'].str.strip()
        return [{'label': mp, 'value': mp} for mp in sorted(df['PracticeMPName'].unique())]
    except Exception as e:
        print("Error fetching Practice MP Names:", e)
        return []

def fetch_practice_mds():
    try:
        query = """
            SELECT DISTINCT TRIM([Practice_MD_Name]) AS PracticeMD
            FROM [dbo].[PRACTICE_MD]
            WHERE [Practice_MD_Name] IS NOT NULL AND TRIM([Practice_MD_Name]) <> ''
        """
        df = pd.read_sql(query, engine)
        df['PracticeMD'] = df['PracticeMD'].str.strip()
        return [{'label': md, 'value': md} for md in sorted(df['PracticeMD'].unique())]
    except Exception as e:
        print("Error fetching Practice MDs:", e)
        return []

def fetch_mp_as_pm():
    try:
        query = """
            SELECT DISTINCT TRIM([MP as PM]) AS MPAsPM
            FROM [dbo].[MP as PM COMMISSION]
            WHERE [MP as PM] IS NOT NULL AND TRIM([MP as PM]) <> ''
        """
        df = pd.read_sql(query, engine)
        df['MPAsPM'] = df['MPAsPM'].str.strip()
        return [{'label': mp, 'value': mp} for mp in sorted(df['MPAsPM'].unique())]
    except Exception as e:
        print("Error fetching MP as PM:", e)
        return []

location_options = fetch_locations()
department_options = fetch_departments()
practice_mp_options = fetch_practice_mps()
practice_md_options = fetch_practice_mds()
mp_as_pm_options = fetch_mp_as_pm()

card_style = {
    "backgroundColor": "#2c2c2c",
    "borderRadius": "10px",
    "padding": "10px 15px",
    "margin": "5px",
    "textAlign": "center",
    "color": "white",
    "fontSize": "18px"
}

layout = html.Div(style={'backgroundColor': '#1e1e1e', 'padding': '20px'}, children=[
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Div([html.H4(id='kpi-mp'), html.Div("MP Commission")], style=card_style), width=2),
                dbc.Col(html.Div([html.H4(id='kpi-md'), html.Div("MD Commission")], style=card_style), width=2),
                dbc.Col(html.Div([html.H4(id='kpi-prac-mp'), html.Div("Practice MP")], style=card_style), width=2),
                dbc.Col(html.Div([html.H4(id='kpi-prac-md'), html.Div("Practice MD")], style=card_style), width=2),
                dbc.Col(html.Div([html.H4(id='kpi-mp-as-pm'), html.Div("MP as PM")], style=card_style), width=2),
                dbc.Col(html.Div([html.H4(id='kpi-3rd-party'), html.Div("3rd Party")], style=card_style), width=2),
            ], justify='start', style={"flexWrap": "nowrap"}),
        ], width=9),

        dbc.Col([
            html.Div([
                html.H3(id='kpi-total', style={'fontSize': '36px', 'margin': '0'}),
                html.Div("Total Commission", style={'fontSize': '24px'})
            ], style=card_style)
        ], width=3, style={'display': 'flex', 'justifyContent': 'flex-end', 'alignItems': 'center'})
    ], align='center', justify='between', style={"marginBottom": "30px"}),

    html.Div([
        dcc.Dropdown(id='year-dropdown', options=[{'label': str(y), 'value': str(y)} for y in range(2022, 2026)],
                     placeholder="Select Year", style={"width": "180px", "marginRight": "20px", "color": "black"}),
        dcc.Dropdown(id='month-dropdown', options=[{'label': m, 'value': i+1} for i, m in enumerate([
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ])], placeholder="Select Month", style={"width": "180px", "marginRight": "20px", "color": "black"}),
    ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '30px'}),

    *[
        html.Div([
            html.H4(title, style={'color': 'white'}),
            html.Label("Department:" if dropdown_id == 'md-dropdown' else "Managing Partner Name:", style={'color': 'white'}),
            dcc.Dropdown(
                id=dropdown_id,
                options=(department_options if dropdown_id == 'md-dropdown' else
                         practice_mp_options if dropdown_id == 'practice-mp-dropdown' else
                         practice_md_options if dropdown_id == 'practice-md-dropdown' else
                         mp_as_pm_options if dropdown_id == 'mp-as-pm-dropdown' else
                         location_options),
                placeholder="Select",
                style={"width": "250px", "color": "black", "marginBottom": "10px"}
            ),
            dash_table.DataTable(id=table_id, columns=columns, style_table={'overflowX': 'auto'},
                                 style_cell={'backgroundColor': '#2b2b2b', 'color': 'white',
                                             'border': '1px solid white', 'textAlign': 'left',
                                             'padding': '5px', 'fontSize': '14px'},
                                 style_header={'backgroundColor': '#444', 'color': 'white', 'fontWeight': 'bold'})
        ])
        for title, dropdown_id, table_id, columns in [
            ("MP Commission Details", 'mp-dropdown', 'mp-table', [
                {'name': 'Managing Partner', 'id': 'Location'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': 'MP Commission', 'id': 'MP_Commission'},
                {'name': 'Account Code', 'id': 'AccountCode'}
            ]),
            ("MD Commission Details", 'md-dropdown', 'md-table', [
                {'name': 'Department', 'id': 'Location'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': 'MD Commission', 'id': 'MD_Commission'},
                {'name': 'Account Code', 'id': 'AccountCode'}
            ]),
            ("Practice MP Commission Details", 'practice-mp-dropdown', 'practice-mp-table', [
                {'name': 'Practice MP', 'id': 'Location'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': 'Practice MP Commission', 'id': 'MP_Commission'}
            ]),
            ("Practice MD Commission Details", 'practice-md-dropdown', 'practice-md-table', [
                {'name': 'Practice MD', 'id': 'PracticeMD'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': 'Practice MD Commission', 'id': 'Practice MD Commission'}
            ]),
            ("MP as PM Commission Details", 'mp-as-pm-dropdown', 'mp-as-pm-table', [
                {'name': 'Managing Partner', 'id': 'Location'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': 'MP as PM Commission', 'id': 'MP as PM Commission'}
            ]),
            ("3rd Party Commission Details", 'third-party-dropdown', 'third-party-table', [
                {'name': 'Managing Partner', 'id': 'Location'},
                {'name': 'Client Name', 'id': 'Client_Name'},
                {'name': 'Description', 'id': 'Invoice_Description'},
                {'name': 'Invoice Date', 'id': 'Invoice_Date'},
                {'name': 'Invoice Amount', 'id': 'Invoice_Amount'},
                {'name': 'Fully Paid On', 'id': 'FullyPaidOnDate'},
                {'name': '3rd Party Commission', 'id': '3rd Party Payout 1'}
            ])
        ]
    ]
])

# --- Callback ---
def register_callbacks(app):
    import dash
    from dash import Input, Output
    import pandas as pd

    # === 1. Dropdown Options Update Callback ===
    @app.callback(
        Output('mp-dropdown', 'options'),
        Output('md-dropdown', 'options'),
        Output('practice-mp-dropdown', 'options'),
        Output('practice-md-dropdown', 'options'),
        Output('mp-as-pm-dropdown', 'options'),
        Output('third-party-dropdown', 'options'),
        Input('user-store', 'data')
    )
    def update_dropdowns(user_data):
        username = user_data.get("username") if user_data else "admin"

        if username == "admin":
            return (
                location_options,
                department_options,
                practice_mp_options,
                practice_md_options,
                mp_as_pm_options,
                location_options
            )
        else:
            filtered_location_options = [opt for opt in location_options if opt['value'] == username]
            filtered_department_options = [opt for opt in department_options if opt['value'] == username]
            filtered_practice_mp_options = [opt for opt in practice_mp_options if opt['value'] == username]
            filtered_practice_md_options = [opt for opt in practice_md_options if opt['value'] == username]
            filtered_mp_as_pm_options = [opt for opt in mp_as_pm_options if opt['value'] == username]
            return (
                filtered_location_options,
                filtered_department_options,
                filtered_practice_mp_options,
                filtered_practice_md_options,
                filtered_mp_as_pm_options,
                filtered_location_options
            )

    # === 2. Main Data Update Callback ===
    @app.callback(
        Output('mp-table', 'data'),
        Output('md-table', 'data'),
        Output('practice-mp-table', 'data'),
        Output('practice-md-table', 'data'),
        Output('mp-as-pm-table', 'data'),
        Output('third-party-table', 'data'),
        Output('kpi-mp', 'children'),
        Output('kpi-md', 'children'),
        Output('kpi-prac-mp', 'children'),
        Output('kpi-prac-md', 'children'),
        Output('kpi-mp-as-pm', 'children'),
        Output('kpi-3rd-party', 'children'),
        Output('kpi-total', 'children'),
        Input('year-dropdown', 'value'),
        Input('month-dropdown', 'value'),
        Input('mp-dropdown', 'value'),
        Input('md-dropdown', 'value'),
        Input('practice-mp-dropdown', 'value'),
        Input('practice-md-dropdown', 'value'),
        Input('mp-as-pm-dropdown', 'value'),
        Input('third-party-dropdown', 'value'),
        Input('user-store', 'data')
    )
    def update_all(year, month, mp_loc, md_dept, practice_mp, practice_md, mp_as_pm, third_party_loc, user_data):
        try:
            if not year or not month:
                return [[] for _ in range(6)] + ["$0"] * 7

            username = user_data.get("username") if user_data else "admin"

            def apply_filter(field, dropdown_val):
                if username != "admin":
                    return f"AND TRIM([{field}]) = '{username}'"
                return f"AND TRIM([{field}]) = '{dropdown_val}'" if dropdown_val else ""

            queries = [
                ("MP_Commission", f"""
                    SELECT TRIM([Location]) AS [Location], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [MP_Commission], [AccountCode]
                    FROM [dbo].[MP/MD COMMISSIONS]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('Location', mp_loc)}
                """),
                ("MD_Commission", f"""
                    SELECT TRIM([Department]) AS [Location], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [MD_Commission], [AccountCode]
                    FROM [dbo].[MP/MD COMMISSIONS]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('Department', md_dept)}
                """),
                ("MP_Commission", f"""
                    SELECT TRIM([Practice MP Name]) AS [Location], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [MP_Commission]
                    FROM [dbo].[PRACTICE_MP]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('Practice MP Name', practice_mp)}
                """),
                ("Practice MD Commission", f"""
                    SELECT TRIM([Practice_MD_Name]) AS [PracticeMD], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [Practice MD Commission]
                    FROM [dbo].[PRACTICE_MD]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('Practice_MD_Name', practice_md)}
                """),
                ("MP as PM Commission", f"""
                    SELECT TRIM([Location]) AS [Location], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [MP as PM Commission]
                    FROM [dbo].[MP as PM COMMISSION]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('MP as PM', mp_as_pm)}
                """),
                ("3rd Party Payout 1", f"""
                    SELECT TRIM([Location]) AS [Location], [Client_Name], [Invoice_Description], [Invoice_Date], [Invoice_Amount],
                           [FullyPaidOnDate], [3rd Party Payout 1]
                    FROM [dbo].[3RD_PARTY COMMISSION]
                    WHERE YEAR([Invoice_Date]) = {year} AND MONTH([Invoice_Date]) = {month}
                    {apply_filter('Location', third_party_loc)}
                """)
            ]

            table_data = []
            kpi_values_raw = []

            for col_name, query in queries:
                df = pd.read_sql(query, engine)
                kpi_sum = df[col_name].sum() if not df.empty else 0
                kpi_values_raw.append(kpi_sum)
                if not df.empty:
                    total_row = {col: '' for col in df.columns}
                    for col in df.select_dtypes(include='number'):
                        total_row[col] = df[col].sum()
                    total_row[df.columns[0]] = 'Total'
                    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
                table_data.append(df.to_dict('records'))

            kpi_values = [format_dollar(val) for val in kpi_values_raw]
            total_kpi = format_dollar(sum(kpi_values_raw))

            return table_data + kpi_values + [total_kpi]

        except Exception as e:
            print("Error:", e)
            return [[] for _ in range(6)] + ["$0"] * 7
