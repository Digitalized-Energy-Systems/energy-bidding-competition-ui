from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import requests

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(children="Market", style={"textAlign": "center"}),
        html.B([html.Div(id="clearing-time")]),
        dcc.Graph(id="graph-content"),
        html.H1(children="Agents", style={"textAlign": "center"}),
        html.Div(id="agent-graph-container"),
        dcc.Interval(
            id="load_interval",
            n_intervals=0,
            max_intervals=-1,  # <-- only run once
            interval=1000,
        ),
    ]
)


@callback(
    Output("clearing-time", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_graph(value):
    return f'Next clearing in {int(float(requests.get("http://127.0.0.1:8000/market/clearing").text))} seconds!'


@callback(
    Output("graph-content", "figure"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_graph(value):
    price_data = pd.DataFrame(
        requests.get("http://127.0.0.1:8000/market/price").json()["data"]
    )
    if len(price_data) > 0:
        return px.line(price_data, x="time", y="price")
    else:
        return None


@callback(
    Output("agent-graph-container", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_graph(value):
    aid_to_bids = requests.get("http://127.0.0.1:8000/market/bids").json()
    return [
        html.Div(
            [
                html.H2(aid),
                dcc.Graph(figure=px.line(pd.DataFrame(bids), x="interval", y="price")),
            ]
        )
        for (aid, bids) in aid_to_bids.items()
    ]


if __name__ == "__main__":
    app.run(debug=True)
