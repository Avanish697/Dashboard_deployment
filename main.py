import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import flask
import dash_auth
from flask import request
import os

# Import layouts and callbacks
from Invoice_details import layout as invoice_layout
from Receivables_details import layout as receivables_layout
from Overview import layout as overview_layout, register_callbacks as register_overview_callbacks
from Entity_breakdown import layout as entity_layout, register_callbacks as register_entity_callbacks
# from Accounts_Score import accounts_layout, register_accounts_callbacks  # 🔴 Commented out
from Deals_in_client_pipeline import client_layout, register_client_callbacks
from Deals_Closing import deals_closing_layout, register_deals_closing_callbacks
from Deals_in_Franchise_pipeline import franchise_layout, register_franchise_callbacks
from Pipeline_by_service_and_lead import graphs_layout, register_graphs_callbacks
from Sales_Cycle import sales_cycle_layout, register_sales_cycle_callbacks


#Commission Details
from Commission_Detail import (
    layout as commission_layout,
    register_callbacks as register_commission_callbacks,
    location_options,
    department_options,
    practice_mp_options,
    practice_md_options,
    mp_as_pm_options
)

# 1. Define username-password pairs
VALID_USERNAME_PASSWORD_PAIRS = {
    #USA MD
    'USA N - AP - Alan Peck': 'Alan@678',
    'USA S - HB - Howard Barouxis' : 'Howard@678',
    'USA W - JS - Jeff Sensmeier': 'Jeff@678',
    # USA MP
    'MEX - MR - Alejandro Garcia Hinojosa' : 'Alejandro@678',
    'USA TT - DDO - David D Oliveira' : 'David@678',
    'USA MA - KS - Richard Pierle' : 'Richard@678',
    'USA N - AP - Amy Calder' : 'Amy@678',
    'USA N - AP - Nathan Morris': 'Nathan@678',
    'USA N - AP - Shan Mukund' : 'Shan@678',
    'USA S - HB - Jake Day' : 'Jake@678',
    'USA S - HB - Matthew Cooper' : 'Matthew@678',
    'USA S - HB - Stephen Rivers' : 'Stephen@678',
    'USA W - JS - Eric Salas' : 'Eric@678',
    'USA W - JS - Josie Van Scholten' : 'Josie@678',

     #AU MP
    'Andrew Mikhail':'Andrew@678',
    'Bill Savellis':'Bill@678',
    'Pia Roy':'Pia@678',
    'Varsha Fleming' :'Varsha@678',
    'Shoban Shingadia' : 'Shoban@678',

    # AU MD
    'JD Waterworth' : 'JD@678',

    #T&T(MP)
    'USA TT - DDO - David D Oliveira' : 'David@678',

    # UK MD US-MS1
    'Michael Sivewright' : 'Michael@678',

    #UK MP
    'Anuradha Sareen' : 'Anuradha@678',
    'Michael Sivewright' : 'Michael@678',
    'Tim Charles' : 'Tim@678',

    #CAN MP
    'Alpesh Patel' : 'Alpesh@678',
    'Mark Hopkins' : 'Mark@678',

    'admin': 'admin123'
}

# 2. Create server and app
server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
app.title = "Valenta Invoice & Sales Dashboard"
app.server.secret_key = '12345678'

# 3. Auth setup
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

# 4. Main content
content = html.Div(
    id="page-content",
    className="p-4",
    style={
        "marginLeft": "16.666667%",
        "backgroundColor": "#121212",
        "width": "83.333333%",
        "minHeight": "100vh",
        "color": "white"
    }
)

# 5. Layout
app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="user-store", storage_type="session"),
    html.Div(id="sidebar-container"),
    content
])

# 6. Sidebar generator
def generate_sidebar(username):
    links = [
        dbc.NavLink("Overview", href="/overview", id="overview-link", active="exact"),
        dbc.NavLink("Entity Breakdown", href="/entity", id="entity-link", active="exact"),
        dbc.NavLink("Invoice Details", href="/invoice", id="invoice-link", active="exact"),
        dbc.NavLink("Receivables Details", href="/receivables", id="receivables-link", active="exact"),
        dbc.NavLink("Deals in Client Pipeline", href="/client", id="client-link", active="exact"),
        dbc.NavLink("Deals in Franchise Pipeline", href="/franchise", id="franchise-link", active="exact"),
        dbc.NavLink("Pipeline by Service and Lead", href="/graphs", id="graphs-link", active="exact"),
        dbc.NavLink("Deals Closing Rate", href="/deals_closing", id="deals-closing-link", active="exact"),
        dbc.NavLink("Sales Cycle", href="/sales_cycle", id="sales-cycle-link", active="exact"),
    ]

    # ✅ Updated to allow all valid commission users (admin or dropdown match)
    valid_commission_users = set(
        opt['value'].strip() for opt in (
            location_options +
            department_options +
            practice_mp_options +
            practice_md_options +
            mp_as_pm_options
        )
    )

    if username == "admin" or username.strip() in valid_commission_users:
        links.append(
            dbc.NavLink("Commission Details", href="/commission_details", id="commission-link", active="exact")
        )

    links.append(
        dbc.NavLink("Logout", href="/logout", id="logout-link", active="exact", style={"color": "red"})
    )

    return html.Div(
        dbc.Nav(
            links,
            vertical=True,
            pills=True,
            className="text-white",
        ),
        style={
            'backgroundColor': 'black',
            'height': '100vh',
            'overflowY': 'auto',
            'padding': '20px',
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '16.666667%'
        }
    )

# 7. Store username in dcc.Store
@app.callback(
    Output("user-store", "data"),
    Input("url", "pathname")
)
def store_user(pathname):
    username = request.authorization.username
    return {"username": username}

# 8. Render sidebar dynamically
@app.callback(
    Output("sidebar-container", "children"),
    Input("user-store", "data")
)
def render_sidebar(user_data):
    username = user_data.get("username") if user_data else ""
    return generate_sidebar(username)

# 9. Page routing
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/logout":
        return html.Div([
            html.H2("Logged Out", style={"color": "red"}),
            html.P("To fully log out, please close this browser tab or clear your browser cache."),
            html.P("Due to HTTP Basic Auth limitations, full logout is handled by the browser.")
        ])
    if pathname in ["/", "/overview"]:
        return overview_layout
    elif pathname == "/entity":
        return entity_layout
    elif pathname == "/invoice":
        return invoice_layout
    elif pathname == "/receivables":
        return receivables_layout
    elif pathname == "/client":
        return client_layout
    elif pathname == "/franchise":
        return franchise_layout
    elif pathname == "/graphs":
        return graphs_layout
    elif pathname == "/deals_closing":
        return deals_closing_layout
    elif pathname == "/sales_cycle":
        return sales_cycle_layout
    elif pathname == "/commission_details":
        return commission_layout
    else:
        return html.H1("404 - Page Not Found", style={"color": "red"})

# 10. Register all callbacks
register_overview_callbacks(app)
register_entity_callbacks(app)
register_client_callbacks(app)
register_franchise_callbacks(app)
register_graphs_callbacks(app)
register_deals_closing_callbacks(app)
register_sales_cycle_callbacks(app)
register_commission_callbacks(app)

# 11. Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
