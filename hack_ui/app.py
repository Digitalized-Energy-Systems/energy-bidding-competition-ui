from dash import Dash, html, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import requests
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
HOST = "192.168.91.84"


def create_card(title, content_id, description):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(title, className="card-title"),
                html.Div(id=content_id, className="card-value"),
                html.P(description, className="card-description"),
            ]
        )
    )


app.layout = html.Div(
    [
        html.H1(children="Market-State", className="section-title"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        create_card(
                            "Next Step",
                            "step-time",
                            "Time in seconds the server will need to process the next step of the simulation",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        create_card(
                            "Time",
                            "current-simulation-time",
                            "Time, which already has been processed (simulation time)",
                        )
                    ]
                ),
            ],
            className="dbc-row",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        create_card(
                            "Auction 4",
                            "auction-4",
                            "The auction which will be processed in the 4 steps",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        create_card(
                            "Auction 3",
                            "auction-3",
                            "The auction which will be processed in the 3 steps",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        create_card(
                            "Auction 2",
                            "auction-2",
                            "The auction which will be processed in the 2 steps",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        create_card(
                            "Auction 1",
                            "auction-1",
                            "The auction which will be processed in the next step",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        create_card(
                            "Last Auction Result",
                            "auction-0",
                            "The auction has been processed in the current step",
                        )
                    ]
                ),
            ],
            className="dbc-row",
        ),
        html.H1(children="Ranking", style={"textAlign": "center"}),
        dbc.Row(
            [
                dbc.Col(
                    [
                        create_card(
                            "Accounts",
                            "balances",
                            "Account owners and their account balance",
                        )
                    ]
                )
            ],
            className="dbc-row",
        ),
        html.H1(children="System", style={"textAlign": "center"}),
        dbc.Row(
            [
                dbc.Col(
                    [
                        create_card(
                            "Demand fulfillment",
                            "demand",
                            "The demand of the system and whether it has been fulfilled",
                        )
                    ]
                )
            ],
            className="dbc-row",
        ),
        dcc.Interval(
            id="load_interval",
            n_intervals=0,
            max_intervals=-1,  # <-- only run once
            interval=1000,
        ),
    ]
)


def format_simulation_time(txt):
    return f"{int(float(txt)) / 3600}h"


@callback(
    Output("step-time", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_step_time(value):
    time_to = int(float(requests.get(f"http://{HOST}:8000/ui/next_step").text))
    if time_to == -1:
        return "Pause"
    return time_to


@callback(
    Output("current-simulation-time", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_cst(value):
    return format_simulation_time(
        requests.get(f"http://{HOST}:8000/ui/current_st").text
    )


def to_participant(actor, mapping):
    new_actor = actor
    for aid, pid in mapping.items():
        new_actor = new_actor.replace(aid, pid[0:-2])
    return new_actor


@callback(
    Output("balances", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_accounts(value):
    balance_dict = requests.get(f"http://{HOST}:8000/account/balances").json()
    tr_list = []
    actor_part_mapping = requests.get(f"http://{HOST}:8000/ui/participant_map").json()
    for actor, balance in sorted(balance_dict.items(), key=lambda x: -x[1]):
        part = to_participant(actor, actor_part_mapping)
        tr_list.append(
            html.Tr([html.Td(part), html.Td(balance, className="balance-value")])
        )

    table_header = [html.Thead(html.Tr([html.Th("Name"), html.Th("Balance")]))]
    table_body = [html.Tbody(tr_list)]
    table = dbc.Table(
        table_header + table_body, bordered=False, class_name="account-table"
    )
    return table


@callback(
    Output("demand", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_demand(value):
    import json

    demand_df = pd.DataFrame.from_dict(
        json.loads(requests.get(f"http://{HOST}:8000/system/demand").json())
    )

    return [
        dcc.Graph(
            figure=px.line(
                demand_df,
                x=demand_df.index,
                y="provided_share_until",
                labels={
                    "index": "time step",
                },
            )
        ),
        dcc.Graph(
            figure=px.line(
                demand_df,
                x=demand_df.index,
                y="tender_amount_kw",
                labels={
                    "index": "time step",
                },
            )
        ),
        dcc.Graph(
            figure=px.line(
                demand_df,
                x=demand_df.index,
                y="provided_amount_kw",
                labels={
                    "index": "time step",
                },
            )
        ),
    ]


def visualize_auction_dict(
    auction_dict,
    is_result=False,
    clearing_price=None,
    awarded_orders=None,
    actor_part_mapping=None,
):
    amount = auction_dict["tender_amount_kw"]
    minimum_order = auction_dict["minimum_order_amount_kw"]
    closure = format_simulation_time(auction_dict["gate_closure_time"])
    supply_start = format_simulation_time(auction_dict["supply_start_time"])

    row1 = html.Tr([html.Td("Amount"), html.Td(amount, className="auction-value")])
    row2 = html.Tr(
        [html.Td("Minimum"), html.Td(minimum_order, className="auction-value")]
    )
    row3 = None
    if is_result:
        row3 = html.Tr(
            [
                html.Td("Clearing Price"),
                html.Td(clearing_price, className="auction-value"),
            ]
        )
    else:
        row3 = html.Tr(
            [html.Td("Closure"), html.Td(closure, className="auction-value")]
        )
    row4 = html.Tr(
        [html.Td("Supply"), html.Td(supply_start, className="auction-value")]
    )
    if is_result:
        awarded_agents = list(
            set(
                [
                    (
                        to_participant(order["agents"][0], actor_part_mapping)
                        if len(order["agents"]) == 1
                        else order["agents"]
                    )
                    for order in awarded_orders
                ]
            )
        )
        row2 = html.Tr(
            [
                html.Td("Awarded"),
                html.Td(str(awarded_agents), className="auction-value"),
            ]
        )
    table_body = [html.Tbody([row1, row2, row3, row4])]

    return dbc.Table(table_body, bordered=False, class_name="auction-table")


@callback(
    Output("auction-1", "children"),
    Output("auction-2", "children"),
    Output("auction-3", "children"),
    Output("auction-4", "children"),
    Output("auction-0", "children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_auction(value):
    actor_part_mapping = requests.get(f"http://{HOST}:8000/ui/participant_map").json()
    current_result_auctions = requests.get(
        f"http://{HOST}:8000/ui/auction/results"
    ).json()["results"]
    current_open_auctions = requests.get(
        f"http://{HOST}:8000/market/auction/open"
    ).json()["auctions"]

    div_list = ["No auction yet"] * 4
    for i, auction in enumerate(current_open_auctions):
        div_list[i] = html.Div(visualize_auction_dict(auction))
        # div_list.append(html.Div(str(auction)))
    if len(current_result_auctions) > 0:
        auction_result_dict = current_result_auctions[-1]
        div_list.append(
            html.Div(
                visualize_auction_dict(
                    auction_result_dict["params"],
                    is_result=True,
                    clearing_price=auction_result_dict["clearing_price"],
                    awarded_orders=auction_result_dict["awarded_orders"],
                    actor_part_mapping=actor_part_mapping,
                )
            )
        )
    else:
        div_list.append("No result yet.")
    return div_list


"""
@callback(
    Output("graph-content", "figure"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def update_graph(value):
    price_data = pd.DataFrame(
        requests.get("http://{HOST}:8000/market/price").json()["data"]
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
    aid_to_bids = requests.get("http://{HOST}:8000/market/bids").json()
    return [
        html.Div(
            [
                html.H2(aid),
                dcc.Graph(figure=px.line(pd.DataFrame(bids), x="interval", y="price")),
            ]
        )
        for (aid, bids) in aid_to_bids.items()
    ]
"""

if __name__ == "__main__":
    app.run(debug=True)
