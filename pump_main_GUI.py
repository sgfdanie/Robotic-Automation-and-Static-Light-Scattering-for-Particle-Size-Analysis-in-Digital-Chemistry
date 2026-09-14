# =============================================================================
#
# MAIN GUI
#
# =============================================================================
# Resposnible for hosting the dashboard.
# It integrates all of the other programs in the directory to allow for a clear 
# user operation of the pumps.


# =============================================================================
# IMPORTS
# =============================================================================
import json
import threading
import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update, ALL
import webbrowser

# =============================================================================
# PUMP CONTROLLER
# =============================================================================
from pyserial_main_code import (
    start_pump,
    start_pump_dropwise,
    stop_pump,
    stop_all_pumps,
    save_and_clear_logs,
    close
)

# =============================================================================
# IKA HOTPLATE
# =============================================================================
from IKA_hotplate import (
    IKAHotplate,
    find_hotplate_port
)

# =============================================================================
# QUERY BUILDER
# =============================================================================
from query_builder_GUI import (
    create_action_ui,
    query_builder_layout
)


# =============================================================================
# OPTIONAL QUERY RUNNER
# =============================================================================
from query_builder import QueryRunner

# =============================================================================
# IKA CONNECTION
# =============================================================================

CONNECT_IKA = False # Set this to False while testing without the IKA connected, True when connected.

hotplate = None

if CONNECT_IKA:

    print("Searching for IKA hotplate")

    try:
        hotplate_port = find_hotplate_port()

        hotplate = IKAHotplate(hotplate_port)

        hotplate.connect()

        print(
            f"IKA hotplate connected on "
            f"{hotplate_port}"
        )


    except Exception as e:
        hotplate = None
        print(f"IKA hotplate connection failed: {e}")

else:
    print("IKA connection disabled for testing.")


# =============================================================================
# QUERY RUNNER
# =============================================================================
# This ensures that the query runner only works when IKA is integrated.
# If the user wants to use the Query builder using the pump system itself, the 
# lines 95-103 should be commented and lines 107-112 uncommented
# =============================================================================

query_runner = None

if hotplate is not None:
    query_runner = QueryRunner(
        start_pump=start_pump,
        start_pump_dropwise=start_pump_dropwise,
        stop_all_pumps=stop_all_pumps,
        hotplate=hotplate
    )


# No hotplate check included --------------------------------------------------
# query_runner = QueryRunner(
#     start_pump=start_pump,
#     start_pump_dropwise=start_pump_dropwise,
#     stop_all_pumps=stop_all_pumps,
#     hotplate=hotplate
# )

# =============================================================================
# STYLES
# =============================================================================
# Importing the styles for each GUI component

from GUI_styles import(
    pump_head_style,
    volume_head_style,
    direction_head_style,
    dispensing_head_style,
    status_head_style,
    maintenance_head_style,
    pump_selection_style,
    volume_style,
    direction_style,
    mode_style,
    prime_status_style,
    prime_button_style,
    dispense_style,
    stop_button_style,
    stop_all_button_style,
    total_clear_style,
    hotplate_input_style,
    hotplate_button_style,
    ika_status_style,
    hotplate_section_style,
    open_query_builder_style,
    pump_section_style
)

# =============================================================================
# JSON LOG
# =============================================================================
# Loads (and creates if non-existant) a json file logging all the pump actions

def load_JSON_log():
    """
    Loads the pump activity log from the JSON file.
    
    Returns the stored pump totals, overall dispensed volume, and eventhistory. 
    If the file does not exist, returns a new log structure with zeroed pump totals and no recorded events.
    """
    try:
        with open(
            "pump_log.json",
            "r"
        ) as file:
            return json.load(file)


    except FileNotFoundError:
        return {
            "totals": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0
            },
            "total_volume_dispensed": 0,
            "events": []
        }

# =============================================================================
# PUMP PRIMING STATUS JSON
# =============================================================================
# Loads (and creates if non-existant) a json file logging the priming status

def load_pump_status():
    """
    Loads the current priming status of all pumps from a JSON file.

    Returns the stored pump statuses or initializes all pumps as unprimed if the status file does not yet exist.
    """
    try:
        with open("pump_status.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # Default state if the file doesn't exist yet
        return {"A": "Unprimed", "B": "Unprimed", "C": "Unprimed", "D": "Unprimed"}

def save_pump_status(status_dict):
    """
    Saves the current pump priming statuses to a JSON file.

    Stores the status of each pump in a formatted JSON file for persistent tracking between program runs.
    """

    with open("pump_status.json", "w") as file:
        json.dump(status_dict, file, indent=4)

# Load the initial status when the app boots up
initial_status = load_pump_status()

# =============================================================================
# MAIN PUMP GUI
# =============================================================================
# Typical Dash component can be built using:
    #
    # dcc.Input(
    #     id=           # Unique identifier used to reference the component
    #     type=         # Type of input, e.g. "number", "text", etc.
    #     min=          # Minimum allowed value
    #     max=          # Maximum allowed value
    #     step=         # Increment between selectable values
    #     placeholder=  # Text displayed when no value has been entered
    #     style=        # Dictionary containing CSS styling properties
    # ),
    #
    # Components can then be grouped together using:
    #
    # html.Div([
    #     component_1,
    #     component_2,
    #     ...
    # ])
    #
    # This allows multiple Dash components to be combined into a single
    # functional block of the GUI.

main_layout = html.Div([
    

    # =========================================================================
    # TITLE
    # =========================================================================
    html.H1("Peristaltic Pump Controller", 
            style={"textAlign": "center"}
    ),

    html.Hr(),

    # =========================================================================
    # MAIN CONTROL AREA
    # =========================================================================
    html.Div([

        # =====================================================================
        # LEFT COLUMN - PUMPS
        # =====================================================================
        html.Div([

            html.H2(
                "Peristaltic Pumps"
            ),

            html.Div([

                # =============================================================
                # HEADERS
                # =============================================================
                html.Div([

                    html.Div(
                        "PUMP",
                        style=pump_head_style
                    ),

                    html.Div(
                        "VOLUME (mL)",
                        style=volume_head_style
                    ),

                    html.Div(
                        "DIRECTION",
                        style=direction_head_style
                    ),

                    html.Div(
                        "DISPENSING TYPE",
                        style=dispensing_head_style
                    ),

                    html.Div(
                        "STATUS", 
                        style=status_head_style
                        ),

                    html.Div(
                        "MAINTENANCE", 
                        style=maintenance_head_style
                        )
                ]),

                html.Hr(),

                # =============================================================
                # PUMP A
                # =============================================================
                html.Div([
                    dcc.Checklist(
                        id="pumpA",
                        options=[
                            {
                                "label": "A",
                                "value": "A"
                            }
                        ],
                        value=[],
                        style=pump_selection_style
                    ),

                    dcc.Input(
                        id="volumeA", # ID of the specific action box
                        type="number", # Type of the specific action box (in this case allows the user to select the volume)
                        min=0,
                        max=None,
                        step=0.1,
                        placeholder="mL",
                        style=volume_style
                    ),

                    dcc.Dropdown(
                        id="directionA",
                        options=[
                            {
                                "label": "Forward",
                                "value": "forward"
                            },

                            {
                                "label": "Reverse",
                                "value": "reverse"
                            }
                        ],
                        value="forward",
                        clearable=False,
                        style=direction_style
                    ),

                    dcc.Dropdown(
                        id="modeA",
                        options=[
                            {
                                "label": "Continuous",
                                "value": "continuous"
                            },

                            {
                                "label": "Drop-wise",
                                "value": "dropwise"
                            }

                        ],
                        value="continuous",
                        clearable=False,
                        style=mode_style
                    ),

                    html.Div(
                        initial_status["A"], # Loads saved state on boot
                        id="status-A",
                        style=prime_status_style
                    ),

                    html.Button(
                        "Prime", 
                        id="prime-A", 
                        style=prime_button_style
                    ),

                    html.Button(
                        "Empty", 
                        id="empty-A",
                        style=prime_button_style
                    )
                ]),


                # =============================================================
                # PUMP B
                # =============================================================
                html.Div([
                    dcc.Checklist(
                        id="pumpB",
                        options=[
                            {
                                "label": "B",
                                "value": "B"
                            }
                        ],
                        value=[],
                        style=pump_selection_style
                    ),


                    dcc.Input(
                        id="volumeB",
                        type="number",
                        min=0,
                        max=None,
                        step=0.1,
                        placeholder="mL",
                        style=volume_style

                    ),


                    dcc.Dropdown(
                        id="directionB",
                        options=[
                            {
                                "label": "Forward",
                                "value": "forward"
                            },

                            {
                                "label": "Reverse",
                                "value": "reverse"
                            }

                        ],
                        value="forward",
                        clearable=False,
                        style=direction_style

                    ),

                    dcc.Dropdown(
                        id="modeB",
                        options=[
                            {
                                "label": "Continuous",
                                "value": "continuous"
                            },

                            {
                                "label": "Drop-wise",
                                "value": "dropwise"
                            }

                        ],

                        value="continuous",
                        clearable=False,
                        style=mode_style
                    ),

                    html.Div(
                        initial_status["B"], # Loads saved state on boot
                        id="status-B",
                        style=prime_status_style
                    ),
                    
                    html.Button(
                        "Prime", 
                        id="prime-B", 
                        style=prime_button_style
                    ),
                    
                    html.Button(
                        "Empty", 
                        id="empty-B",
                        style=prime_button_style
                    )
                ]),


                # =============================================================
                # PUMP C
                # =============================================================
                html.Div([
                    dcc.Checklist(
                        id="pumpC",
                        options=[
                            {
                                "label": "C",
                                "value": "C"
                            }
                        ],
                        value=[],
                        style=pump_selection_style
                    ),

                    dcc.Input(

                        id="volumeC",
                        type="number",
                        min=0,
                        max=None,
                        step=0.1,
                        placeholder="mL",
                        style=volume_style
                    ),

                    dcc.Dropdown(
                        id="directionC",
                        options=[
                            {
                                "label": "Forward",
                                "value": "forward"
                            },

                            {
                                "label": "Reverse",
                                "value": "reverse"
                            }
                        ],
                        value="forward",
                        clearable=False,
                        style=direction_style
                    ),

                    dcc.Dropdown(
                        id="modeC",
                        options=[
                            {
                                "label": "Continuous",
                                "value": "continuous"
                            },

                            {
                                "label": "Drop-wise",
                                "value": "dropwise"
                            }
                        ],
                        value="continuous",
                        clearable=False,
                        style=mode_style
                    ),

                    html.Div(
                        initial_status["C"], # Loads saved state on boot
                        id="status-C",
                        style=prime_status_style
                    ),
                    
                    html.Button(
                        "Prime", 
                        id="prime-C", 
                        style=prime_button_style
                    ),
                    
                    html.Button(
                        "Empty", 
                        id="empty-C",
                        style=prime_button_style
                    )
                    
                ]),

                # =============================================================
                # PUMP D
                # =============================================================
                html.Div([
                    dcc.Checklist(
                        id="pumpD",
                        options=[
                            {
                                "label": "D",
                                "value": "D"
                            }
                        ],
                        value=[],
                        style=pump_selection_style
                    ),

                    dcc.Input(
                        id="volumeD",
                        type="number",
                        min=0,
                        max=None,
                        step=0.1,
                        placeholder="mL",
                        style=volume_style
                    ),

                    dcc.Dropdown(
                        id="directionD",
                        options=[
                            {
                                "label": "Forward",
                                "value": "forward"
                            },

                            {
                                "label": "Reverse",
                                "value": "reverse"
                            }
                        ],
                        value="forward",
                        clearable=False,
                        style=direction_style
                    ),

                    dcc.Dropdown(
                        id="modeD",
                        options=[
                            {
                                "label": "Continuous",
                                "value": "continuous"
                            },

                            {
                                "label": "Drop-wise",
                                "value": "dropwise"
                            }
                        ],
                        value="continuous",
                        clearable=False,
                        style=mode_style
                    ),

                    html.Div(
                        initial_status["D"], # Loads saved state on boot
                        id="status-D",
                        style=prime_status_style
                    ),
                    
                    html.Button(
                        "Prime", 
                        id="prime-D", 
                        style=prime_button_style
                    ),
                    
                    html.Button(
                        "Empty", 
                        id="empty-D",
                        style=prime_button_style
                    )
                ]),

                # =============================================================
                # DISPENSE & GLOBAL MAINTENANCE
                # =============================================================
                html.Div([
                    # Your original Dispense button
                    html.Button(
                        "DISPENSE",
                        id="start-button",
                        style=dispense_style
                    ),
                    
                    html.Button(
                        "Prime All", 
                        id="prime-all", 
                        style={
                            "height": "40px", 
                            "padding": "0 20px", 
                            "marginLeft": "30px",
                            "fontWeight": "bold", 
                            "cursor": "pointer"
                        }
                    ),
                    
                    html.Button(
                        "Empty All", 
                        id="empty-all", 
                        style={
                            "height": "40px", 
                            "padding": "0 20px", 
                            "marginLeft": "10px", 
                            "fontWeight": "bold", 
                            "cursor": "pointer"
                        }
                    )
                ], 
                style={
                    "display": "flex", 
                    "alignItems": "center",
                    "marginBottom": "20px"
                }),

                html.Hr(),


                # =============================================================
                # STOP BUTTONS
                # =============================================================
                html.Div([

                    html.Button(
                        "Stop A",
                        id="stopA",
                        style=stop_button_style
                    ),

                    html.Button(
                        "Stop B",
                        id="stopB",
                        style=stop_button_style
                    ),

                    html.Button(
                        "Stop C",
                        id="stopC",
                        style=stop_button_style
                    ),

                    html.Button(
                        "Stop D",
                        id="stopD",
                        style=stop_button_style
                    )
                ],

                style={
                    "textAlign": "center"
                }),

                html.Button(
                    "STOP ALL",
                    id="stopAll",
                    style=stop_all_button_style
                ),

                html.Hr(),


                # =============================================================
                # TOTALS
                # =============================================================

                html.H2(
                    "Dispensed Volumes"
                ),

                html.Div(
                    id="pump-totals"
                ),

                html.Br(),

                html.Div(
                    id="overall-total"
                ),

                dcc.Interval(
                    id="interval-component", 
                    interval=1000, 
                    n_intervals=0
                    ),

                html.Button(

                    "Save & Clear",
                    id="save-clear",
                    style=total_clear_style

                )
            ],

            style=pump_section_style)
        ],

        style={
            "width": "60%",
            "padding": "20px",
            "boxSizing": "border-box"
        }),


        # =====================================================================
        # RIGHT COLUMN
        # =====================================================================
        html.Div([
            html.H2("IKA Hotplate / Stirrer"),

            # =================================================================
            # HOTPLATE BOX
            # =================================================================
            html.Div([

                # -------------------------------------------------------------
                # TEMPERATURE
                # -------------------------------------------------------------
                html.Div([
                    html.Label(
                        "Temperature (°C): ",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "10px"
                        }
                    ),

                    dcc.Input(

                        id="temperature-input",
                        type="number",
                        min=0,
                        max=310,
                        step=1,
                        placeholder="°C",
                        style=hotplate_input_style
                    ),

                    html.Button(
                        "Set Temperature",
                        id="set-temperature",
                        style=hotplate_button_style
                    ),

                    html.Button(
                        "START HEATING",
                        id="start-heating",
                        style=hotplate_button_style
                    ),

                    html.Button(
                        "STOP HEATING",
                        id="stop-heating",
                        style=hotplate_button_style
                    )

                ],

                style={"marginBottom": "15px"}
                ),


                # -------------------------------------------------------------
                # TIMED HEATING
                # -------------------------------------------------------------
                html.Div([
                    dcc.Checklist(
                        id="timed-heating",
                        options=[
                            {
                                "label": "Timed Heating",
                                "value": "timed"
                            }
                        ],

                        value=[],
                        style={
                            "display": "inline-block",
                            "fontWeight": "bold",
                            "marginRight": "20px"
                        }

                    ),

                    html.Label(
                        "Time (seconds): ",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "10px"
                        }
                    ),

                    dcc.Input(
                        id="heat-time",
                        type="number",
                        min=0,
                        max=None,
                        step=1,
                        placeholder="seconds",
                        disabled=True,
                        style=hotplate_input_style
                    )
                ],

                style={"marginBottom": "15px"}
                ),

                html.Hr(),

                # -------------------------------------------------------------
                # STIRRING
                # -------------------------------------------------------------
                html.Div([

                    html.Label(
                        "Stirring Speed (rpm): ",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "10px"
                        }
                    ),

                    dcc.Input(

                        id="speed-input",
                        type="number",
                        min=50,
                        max=1500,
                        step=1,
                        placeholder="rpm",
                        style=hotplate_input_style

                    ),

                    html.Button(
                        "Set Speed",
                        id="set-speed",
                        style=hotplate_button_style
                    ),

                    html.Button(
                        "START STIRRING",
                        id="start-stirring",
                        style=hotplate_button_style
                    ),

                    html.Button(
                        "STOP STIRRING",
                        id="stop-stirring",
                        style=hotplate_button_style
                    )
                ],

                style={
                    "marginBottom": "15px"
                }),

                # -------------------------------------------------------------
                # TIMED STIRRING
                # -------------------------------------------------------------
                html.Div([
                    dcc.Checklist(
                        id="timed-stirring",
                        options=[
                            {
                                "label": "Timed Stirring",
                                "value": "timed"
                            }
                        ],

                        value=[],
                        style={
                            "display": "inline-block",
                            "fontWeight": "bold",
                            "marginRight": "20px"
                        }
                    ),

                    html.Label(
                        "Time (seconds): ",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "10px"
                        }
                    ),

                    dcc.Input(
                        id="stir-time",
                        type="number",
                        min=0,
                        max=None,
                        step=1,
                        placeholder="seconds",
                        disabled=True,
                        style=hotplate_input_style
                    )
                ],
                style={
                    "marginBottom": "15px"
                }),

                # -------------------------------------------------------------
                # IKA STATUS
                # -------------------------------------------------------------
                html.Br(),

                html.Div(
                    "IKA Status: Disabled for testing.",
                    id="ika-status",
                    style=ika_status_style
                )
            ],

            style=hotplate_section_style
            ),

            # =================================================================
            # QUERY BUILDER BUTTON
            # =================================================================
            html.Div([
                html.H2(
                    "Query Builder"
                ),

                html.Button(
                    "OPEN QUERY BUILDER",
                    id="open-query-builder",
                    style=open_query_builder_style
                )
            ],

            style={
                "border": "1px solid black",
                "padding": "20px",
                "marginTop": "15px"
            })

        ],

        style={
            "width": "50%",
            "padding": "20px",
            "boxSizing": "border-box"
        })

    ],

    style={
        "display": "flex",
        "width": "100%",
        "alignItems": "flex-start"
    }),

    # =========================================================================
    # STATUS
    # =========================================================================
    html.H2(
        "Status"
    ),

    html.Div(
        "Ready",
        id="status-message",
        style={
            "border": "1px solid black",
            "padding": "10px",
            "minHeight": "30px"
        }
    )

],

style={
    "width": "1900px",
    "maxWidth": "95%",
    "margin": "auto",
    "fontFamily": "Arial"
})


# =============================================================================
# QUERY BUILDER PAGE
# =============================================================================
query_layout = query_builder_layout()

# =============================================================================
# APPLICATION
# =============================================================================
app = Dash(
    __name__,
    suppress_callback_exceptions=True
)

app.title = "Peristaltic Pump Controller"

# =============================================================================
# MAIN APP LAYOUT
# =============================================================================
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# =============================================================================
# PRIME & EMPTY MAINTENANCE CALLBACK
# =============================================================================

# DASH CALLBACK STRUCTURE

# A Dash callback links GUI inputs to GUI outputs.
#
# @app.callback(
#
#     Output("component-id", "property"),
#         # Defines what component/property will be updated.
#
#     Input("component-id", "property"),
#         # Defines which user action or component change
#         # triggers the callback.
#
#     prevent_initial_call=True
#         # Prevents the callback from running when the page
#         # first loads.
# )
#
# Multiple Outputs and Inputs can be included in the same
# callback, allowing one user action to update several parts
# of the GUI.
#
# In this example:
#   - Outputs update the status displayed for pumps A-D.
#   - Individual Inputs control the prime/empty actions
#     for each pump.
#   - "All" Inputs allow the same action to be applied to
#     all pumps simultaneously.

@app.callback(
    Output("status-A", "children"),
    Output("status-B", "children"),
    Output("status-C", "children"),
    Output("status-D", "children"),
    
    # Individual inputs
    Input("prime-A", "n_clicks"), Input("empty-A", "n_clicks"),
    Input("prime-B", "n_clicks"), Input("empty-B", "n_clicks"),
    Input("prime-C", "n_clicks"), Input("empty-C", "n_clicks"),
    Input("prime-D", "n_clicks"), Input("empty-D", "n_clicks"),
    
    # "All" inputs
    Input("prime-all", "n_clicks"), 
    Input("empty-all", "n_clicks"),
    
    prevent_initial_call=True
)

def handle_prime_empty(
    pA, eA, pB, eB, pC, eC, pD, eD, pAll, eAll
):
    """
    Handles pump priming and emptying actions from the GUI.

    Determines which prime/empty button was pressed, starts the
    corresponding pump operation in a background thread, updates
    the pump's primed/unprimed state, and saves the updated state.

    Args:
        pX, eX: Click counts for the Prime and Empty buttons for Pump X 
        (where X = A, B , C or D).

        pAll, eAll: Click counts for the Prime All and Empty All buttons.

    Returns:
        The updated priming status for Pumps A, B, C, and D.
    """
    button_id = ctx.triggered_id
    current_status = load_pump_status()
    
    if button_id:
        # ---------------------------------------------------------
        # PRIME ALL LOGIC
        # ---------------------------------------------------------
        if button_id == "prime-all":
            for pump in ["A", "B", "C", "D"]:
                # Only act if the pump is Unprimed
                if current_status[pump] == "Unprimed":
                    threading.Thread(target=start_pump, args=(pump, 6.7), daemon=True).start()
                    current_status[pump] = "Primed"
                    
        # ---------------------------------------------------------
        # EMPTY ALL LOGIC
        # ---------------------------------------------------------
        elif button_id == "empty-all":
            for pump in ["A", "B", "C", "D"]:
                # Only act if the pump is already Primed
                if current_status[pump] == "Primed":
                    command = "R" + pump
                    threading.Thread(target=start_pump, args=(command, 6.7), daemon=True).start()
                    current_status[pump] = "Unprimed"
                    
        # ---------------------------------------------------------
        # INDIVIDUAL BUTTON LOGIC
        # ---------------------------------------------------------
        else:
            action, pump = button_id.split("-")
            
            if action == "prime" and current_status[pump] == "Unprimed":
                threading.Thread(target=start_pump, args=(pump, 6.7), daemon=True).start()
                current_status[pump] = "Primed"
                
            elif action == "empty" and current_status[pump] == "Primed":
                command = "R" + pump
                threading.Thread(target=start_pump, args=(command, 6.7), daemon=True).start()
                current_status[pump] = "Unprimed"
                
        # Save state regardless of which button was clicked
        save_pump_status(current_status)

    return current_status["A"], current_status["B"], current_status["C"], current_status["D"]

# =============================================================================
# PAGE NAVIGATION
# =============================================================================
@app.callback(
    Output("page-content", "children"),

    Input("url", "pathname")
)
def display_page(pathname):
    """
    Displays the appropriate GUI page based on the current URL path.

    Args:
        pathname: The current URL path used to determine which page should be displayed.

    Returns:
        The layout corresponding to the requested page.
    """

    if pathname == "/query-builder":
        return query_layout
    return main_layout


# ----------------------------------------------------------------------------
@app.callback(
    Output("url", "pathname"),

    Input("open-query-builder", "n_clicks"),

    prevent_initial_call=True
)
def navigate_to_query(n_clicks):
    """
    Navigates from the main page to the query-builder page when
    the query-builder button is clicked.

    Args:
        n_clicks: Number of times the query-builder button has been clicked.

    Returns:
        The URL path for the query-builder page, or the main page path if no click has occurred.
    """

    if n_clicks:
        return "/query-builder"
    return "/"

# ----------------------------------------------------------------------------
@app.callback(
    Output("url", "pathname", allow_duplicate=True),

    Input("back-to-main", "n_clicks"),

    prevent_initial_call=True
)
def navigate_to_main(n_clicks):
    """
    Navigates from the query-builder page back to the main page.

    Args:
        n_clicks: Number of times the back button has been clicked.

    Returns:
        The main page URL path when clicked, otherwise no update.
    """

    if n_clicks:
        return "/"

    return dash.no_update

# =============================================================================
# MAIN PUMP / IKA CALLBACK
# =============================================================================
@app.callback(
    Output("status-message","children"),

    Input("start-button","n_clicks"),
    Input("stopA","n_clicks"),
    Input("stopB","n_clicks"),
    Input("stopC","n_clicks"),
    Input("stopD","n_clicks"),
    Input("stopAll","n_clicks"),
    Input("save-clear","n_clicks"),
    Input("set-temperature","n_clicks"),
    Input("start-heating","n_clicks"),
    Input("stop-heating","n_clicks"),
    Input("set-speed","n_clicks"),
    Input("start-stirring","n_clicks"),
    Input("stop-stirring","n_clicks"),

    # -------------------------------------------------------------------------
    # Pump A
    # -------------------------------------------------------------------------
    State("pumpA","value"),
    State("volumeA","value"),
    State("directionA","value"),
    State("modeA","value"),

    # -------------------------------------------------------------------------
    # Pump B
    # -------------------------------------------------------------------------
    State("pumpB","value"),
    State("volumeB","value"),
    State("directionB","value"),
    State("modeB","value"),

    # -------------------------------------------------------------------------
    # Pump C
    # -------------------------------------------------------------------------
    State("pumpC","value"),
    State("volumeC","value"),
    State("directionC","value"),
    State("modeC","value"),

    # -------------------------------------------------------------------------
    # Pump D
    # -------------------------------------------------------------------------
    State("pumpD","value"),
    State("volumeD","value"),
    State("directionD","value"),
    State("modeD","value"),

    # -------------------------------------------------------------------------
    # Hotplate
    # -------------------------------------------------------------------------
    State("temperature-input","value"),
    State("speed-input","value"),
    State("timed-heating","value"),
    State("heat-time","value"),
    State("timed-stirring","value"),
    State("stir-time","value"),

    prevent_initial_call=True

)

def control_callback(

    clicks_start,

    clicks_stopA,
    clicks_stopB,
    clicks_stopC,
    clicks_stopD,

    clicks_stopAll,

    clicks_save_clear,

    clicks_set_temperature,
    clicks_start_heating,
    clicks_stop_heating,

    clicks_set_speed,
    clicks_start_stirring,
    clicks_stop_stirring,

    pumpA,
    volumeA,
    directionA,
    modeA,

    pumpB,
    volumeB,
    directionB,
    modeB,

    pumpC,
    volumeC,
    directionC,
    modeC,

    pumpD,
    volumeD,
    directionD,
    modeD,

    temperature,
    speed,

    timed_heating,
    heat_time,

    timed_stirring,
    stir_time

):
    """
    Controls the main pump and IKA hotplate operations through the GUI.

    Determines which control button triggered the callback and
    performs the corresponding pump, heating, or stirring operation.
    Pump commands are executed in background threads to keep the
    GUI responsive, while status messages are returned to the interface.

    Args:
        clicks_start: Click count for the main pump start button.
        clicks_stopA/B/C/D: Click counts for the individual pump stop buttons.
        clicks_stopAll: Click count for the stop-all button.
        clicks_save_clear: Click count for the save and clear button.
        clicks_set_temperature: Click count for the temperature set button.
        clicks_start_heating: Click count for the heating start button.
        clicks_stop_heating: Click count for the heating stop button.
        clicks_set_speed: Click count for the stirring speed set button.
        clicks_start_stirring: Click count for the stirring start button.
        clicks_stop_stirring: Click count for the stirring stop button.
        pumpA/B/C/D: Pump selection values from the GUI.
        volumeA/B/C/D: Selected pump volumes.
        directionA/B/C/D: Selected pump directions.
        modeA/B/C/D: Selected pump operating modes.
        temperature: Hotplate temperature setpoint.
        speed: Stirring speed setpoint.
        timed_heating: Whether timed heating is enabled.
        heat_time: Heating duration in seconds.
        timed_stirring: Whether timed stirring is enabled.
        stir_time: Stirring duration in seconds.

    Returns:
        A status message describing the result of the selected operation.

    """
    

    button = ctx.triggered_id

    # =========================================================================
    # DISPENSE
    # =========================================================================
    if button == "start-button":
        started = []

        # ---------------------------------------------------------------------
        # Pump A
        # ---------------------------------------------------------------------
        if pumpA and volumeA is not None:

            command = (
                "RA"
                if directionA == "reverse"
                else "A"
            )

            if modeA == "dropwise":
                threading.Thread(
                    target=start_pump_dropwise,
                    args=(
                        command,
                        volumeA
                    ),
                    daemon=True
                ).start()

            else:
                threading.Thread(
                    target=start_pump,
                    args=(
                        command,
                        volumeA
                    ),
                    daemon=True
                ).start()

            started.append("Pump A")


        # ---------------------------------------------------------------------
        # Pump B
        # ---------------------------------------------------------------------
        if pumpB and volumeB is not None:

            command = (
                "RB"
                if directionB == "reverse"
                else "B"

            )

            if modeB == "dropwise":
                threading.Thread(
                    target=start_pump_dropwise,
                    args=(
                        command,
                        volumeB
                    ),
                    daemon=True
                ).start()

            else:
                threading.Thread(
                    target=start_pump,
                    args=(
                        command,
                        volumeB
                    ),
                    daemon=True
                ).start()


            started.append("Pump B")

        # ---------------------------------------------------------------------
        # Pump C
        # ---------------------------------------------------------------------
        if pumpC and volumeC is not None:
            command = (
                "RC"
                if directionC == "reverse"
                else "C"

            )

            if modeC == "dropwise":
                threading.Thread(
                    target=start_pump_dropwise,
                    args=(
                        command,
                        volumeC
                    ),
                    daemon=True
                ).start()

            else:
                threading.Thread(
                    target=start_pump,
                    args=(
                        command,
                        volumeC
                    ),
                    daemon=True
                ).start()

            started.append("Pump C")

        # ---------------------------------------------------------------------
        # Pump D
        # ---------------------------------------------------------------------
        if pumpD and volumeD is not None:
            command = (
                "RD"
                if directionD == "reverse"
                else "D"
            )

            if modeD == "dropwise":
                threading.Thread(
                    target=start_pump_dropwise,
                    args=(
                        command,
                        volumeD
                    ),
                    daemon=True
                ).start()

            else:
                threading.Thread(
                    target=start_pump,
                    args=(
                        command,
                        volumeD
                    ),
                    daemon=True
                ).start()

            started.append("Pump D")

        if not started:
            return "No pumps selected."

        return ("Started: " + ", ".join(started))

    # =========================================================================
    # STOP A
    # =========================================================================
    elif button == "stopA":
        elapsed_time = stop_pump("A")

        if elapsed_time is None:
            return "Pump A was not running."

        return (
            f"Pump A stopped after "
            f"{elapsed_time:.2f} ms."
        )

    # =========================================================================
    # STOP B
    # =========================================================================
    elif button == "stopB":
        elapsed_time = stop_pump("B")

        if elapsed_time is None:
            return "Pump B was not running."

        return (
            f"Pump B stopped after "
            f"{elapsed_time:.2f} ms."
        )

    # =========================================================================
    # STOP C
    # =========================================================================
    elif button == "stopC":
        elapsed_time = stop_pump("C")

        if elapsed_time is None:
            return "Pump C was not running."

        return (
            f"Pump C stopped after "
            f"{elapsed_time:.2f} ms."
        )

    # =========================================================================
    # STOP D
    # =========================================================================
    elif button == "stopD":
        elapsed_time = stop_pump("D")

        if elapsed_time is None:
            return "Pump D was not running."

        return (
            f"Pump D stopped after "
            f"{elapsed_time:.2f} ms."
        )

    # =========================================================================
    # STOP ALL
    # =========================================================================
    elif button == "stopAll":
        stop_all_pumps()
        return "All pumps stopped."


    # =========================================================================
    # SAVE & CLEAR
    # =========================================================================
    elif button == "save-clear":
        save_and_clear_logs()
        return ("Transfer log saved and reset.")

    # =========================================================================
    # IKA SET TEMPERATURE
    # =========================================================================
    elif button == "set-temperature":
        if hotplate is None:
            return ("IKA disabled for testing.")

        if temperature is None:
            return ("Please enter a temperature.")

        try:
            hotplate.set_temperature(temperature)

            return (
                f"Temperature set to "
                f"{temperature} °C."
            )

        except Exception as e:
            return (f"IKA ERROR: {e}")

    # =========================================================================
    # IKA START HEATING
    # =========================================================================
    elif button == "start-heating":
        if hotplate is None:
            return (
                "IKA disabled for testing."
            )

        try:
            if timed_heating:
                if heat_time is None:
                    return ("Please enter a heating time.")

                if heat_time <= 0:
                    return ("Heating time must be greater than 0 seconds.")

                hotplate.start_timed_heating(heat_time)

                return (
                    f"Heating started for "
                    f"{heat_time} seconds."
                )

            else:
                hotplate.start_heating()
                return ("Heating started continuously.")

        except Exception as e:
            return (f"IKA ERROR: {e}")


    # =========================================================================
    # IKA STOP HEATING
    # =========================================================================
    elif button == "stop-heating":

        if hotplate is None:
            return ("IKA disabled for testing.")

        try:
            hotplate.stop_heating()
            return "Heating stopped."
        
        except Exception as e:
            return (f"IKA ERROR: {e}")


    # =========================================================================
    # IKA SET SPEED
    # =========================================================================
    elif button == "set-speed":
        if hotplate is None:
            return ("IKA disabled for testing.")

        if speed is None:
            return ("Please enter a stirring speed.")

        try:
            hotplate.set_speed(speed)

            return (
                f"Stirring speed set to "
                f"{speed} rpm."
            )
        
        except Exception as e:
            return (f"IKA ERROR: {e}")

    # =========================================================================
    # IKA START STIRRING
    # =========================================================================
    elif button == "start-stirring":
        if hotplate is None:
            return ("IKA disabled for testing.")

        try:
            if timed_stirring:
                if stir_time is None:
                    return ("Please enter a stirring time.")

                if stir_time <= 0:
                    return (
                        "Stirring time must be "
                        "greater than 0 seconds."
                    )

                hotplate.start_timed_stirring(stir_time)

                return (
                    f"Stirring started for "
                    f"{stir_time} seconds."
                )

            else:
                hotplate.start_stirring()
                return ("Stirring started continuously.")

        except Exception as e:
            return (f"IKA ERROR: {e}")

    # =========================================================================
    # IKA STOP STIRRING
    # =========================================================================
    elif button == "stop-stirring":
        if hotplate is None:
            return ("IKA disabled for testing.")

        try:
            hotplate.stop_stirring()
            return "Stirring stopped."

        except Exception as e:
            return (f"IKA ERROR: {e}")

    return "Ready"

# =============================================================================
# TIMED HEATING INPUT
# =============================================================================
@app.callback(
    Output("heat-time","disabled"),
    Input("timed-heating","value")

)

def enable_heating_timer(timed_heating):
    """
    Enables or disables the heating-time input based on whether
    timed heating is selected.

    Args:
        timed_heating: Boolean indicating whether timed heating is enabled.

    Returns:
        False to enable the heating-time input, or True to disable it.
    """

    if timed_heating:
        return False

    return True

# =============================================================================
# TIMED STIRRING INPUT
# =============================================================================
@app.callback(
    Output("stir-time","disabled"),
    Input("timed-stirring","value")

)

def enable_stirring_timer(timed_stirring):
    """
    Enables or disables the stirring-time input based on whether
    timed stirring is selected.

    Args:
        timed_stirring: Boolean indicating whether timed stirring is enabled.

    Returns:
        False to enable the stirring-time input, or True to disable it.
    """

    if timed_stirring:
        return False

    return True

# =============================================================================
# QUERY BUILDER - ADD / REMOVE OPERATIONS
# =============================================================================
@app.callback(
    Output("query-actions","children"),
    Output("query-data","data"),

    # New action
    Input("new-action","n_clicks"),

    # Adding a pump operation
    Input(
        {
            "type": "add-pump-operation",
            "action": ALL
        },
        "n_clicks"
    ),

    # Adding a stirrer operation
    Input(
        {
            "type": "add-stirrer-operation",
            "action": ALL
        },
        "n_clicks"
    ),

    # Adding a heating operation
    Input(
        {
            "type": "add-heating-operation",
            "action": ALL
        },
        "n_clicks"
    ),

    # Deleting an operation
    Input(
        {
            "type": "delete-operation",
            "action": ALL,
            "operation": ALL
        },
        "n_clicks"
    ),

    # Deleting an action
    Input(
        {
            "type": "delete-action",
            "action": ALL
        },
        "n_clicks"
    ),

    State("query-data","data"),

    prevent_initial_call=False

)

def update_query_builder(
    new_action_clicks,
    add_pump_clicks,
    add_stirrer_clicks,
    add_heating_clicks,
    delete_operation_clicks,
    delete_action_clicks,
    data
):
    """ 
    Manages the dynamic query builder by adding and removing actions and pump, stirring, and heating operations. 
    Determines which control triggered the callback, updates the stored query data accordingly, and rebuilds the query-builder interface.

    Args: 
        new_action_clicks: Click count for creating a new action. 
        add_pump_clicks: Click counts for adding pump operations. 
        add_stirrer_clicks: Click counts for adding stirring operations. 
        add_heating_clicks: Click counts for adding heating operations. 
        delete_operation_clicks: Click counts for deleting operations. 
        delete_action_clicks: Click counts for deleting complete actions. 
        data: Current query-builder data containing actions and operations. 
        
    Returns: 
        A tuple containing the rebuilt UI components and updated query data. 
    """

    print("========== QUERY CALLBACK STARTED ==========")
    print("TRIGGER:", ctx.triggered_id)
    print("DATA:", data)

    # =========================================================================
    # INITIALISE DATA
    # =========================================================================
    if data is None or len(data) == 0:
        data = [
            {
                "operations": [],
                "delay": 0
            }
        ]

    # =========================================================================
    # IDENTIFY WHAT WAS CLICKED
    # =========================================================================
    button = ctx.triggered_id

    # =========================================================================
    # NEW ACTION
    # =========================================================================
    if button == "new-action":

        data.append({
            "operations": [],
            "delay": 0,
            "global_stir_start": "none",
            "global_stir_stop": "none",
            "global_heat_start": "none",
            "global_heat_stop": "none"
        })

    # =========================================================================
    # ADD PUMP OPERATION
    # =========================================================================
    elif isinstance(button, dict):

        button_type = button.get("type")

        # ---------------------------------------------------------------------
        # ADD PUMP
        # ---------------------------------------------------------------------
        if button_type == "add-pump-operation":
            action_index = button["action"]
            data[action_index]["operations"].append({

                "type": "pump",
                "pump": "A",
                "volume": None,
                "direction": "forward",
                "mode": "continuous"

            })

        # ---------------------------------------------------------------------
        # ADD STIRRER
        # ---------------------------------------------------------------------
        elif button_type == "add-stirrer-operation":
            action_index = button["action"]
            data[action_index]["operations"].append({

                "type": "stirrer",
                "speed": None,
                "duration": None

            })

        # ---------------------------------------------------------------------
        # ADD HEATING
        # ---------------------------------------------------------------------
        elif button_type == "add-heating-operation":
            action_index = button["action"]
            data[action_index]["operations"].append({

                "type": "heating",
                "temperature": None,
                "duration": None
            })

        # ---------------------------------------------------------------------
        # DELETE OPERATION
        # ---------------------------------------------------------------------
        elif button_type == "delete-operation":

            action_index = button["action"]
            operation_index = button["operation"]

            # Verify the indices are still valid
            if (
                0 <= action_index < len(data)
                and
                0 <= operation_index < len(data[action_index]["operations"])
            ):
                del data[action_index]["operations"][operation_index]

        # ---------------------------------------------------------------------
        # DELETE ACTION
        # ---------------------------------------------------------------------
        elif button_type == "delete-action":

            action_index = button["action"]

            # Make sure the index is valid
            if 0 <= action_index < len(data):

                del data[action_index]

            # Keep at least one action available
            if len(data) == 0:

                data.append({
                    "operations": [],
                    "delay": 0,
                    "global_stir_start": "none",
                    "global_stir_stop": "none",
                    "global_heat_start": "none",
                    "global_heat_stop": "none"
                })

    # =========================================================================
    # BUILD UI
    # =========================================================================
    components = []

    for index, action in enumerate(data):

        components.append(
            create_action_ui(
                index,
                action
            )
        )

    return (
        components,
        data
    )


# =============================================================================
# GLOBAL STIRRING ACTION OPTIONS
# =============================================================================
@app.callback(
    Output("global-stirring-start", "options"),
    Output("global-stirring-stop", "options"),
    Output("global-heating-start", "options"),
    Output("global-heating-stop", "options"),
    Input("query-data", "data"),
    prevent_initial_call=False
)
def update_global_stirring_actions(query_data):
    """ 
    Generates the available action options for global stirring and heating controls. 
    Creates a list of action numbers based on the current number of actions in the query builder. 

    Args: 
        query_data: Current query-builder data containing the defined actions. 
        
    Returns: 
        Four identical lists of action options for global stirring start, stirring stop, heating start, and heating stop selections. 
    """
    
    if not query_data:
        return [], [], [], []

    options = [
        {
            "label": f"Action {i + 1}",
            "value": i + 1
        }
        for i in range(len(query_data))
    ]

    return options, options, options, options

# =============================================================================
# GLOBAL STIRRING SETTINGS
# =============================================================================
@app.callback(
    Output("global-stirring-data", "data"),
    Input("global-stirring-enabled","value"),
    Input("global-stirring-speed","value"),
    Input("global-stirring-start","value"),
    Input("global-stirring-stop","value"),

    prevent_initial_call=False
)
def update_global_stirring_data(
    enabled,
    speed,
    start_action,
    stop_action
):
    """ 
    Stores the global stirring settings selected in the query builder. 
    Converts the stirring enable value to a boolean and stores the selected stirring speed and the actions at which stirring should start and stop. 
    
    Args: 
        enabled: Indicates whether global stirring is enabled. 
        speed: Global stirring speed in rpm. 
        start_action: Action number at which stirring should start. 
        stop_action: Action number at which stirring should stop. 
    
    Returns: 
        A dictionary containing the global stirring configuration. 
    """
    return {
        "enabled": bool(enabled),
        "speed": speed,
        "start_action": start_action,
        "stop_action": stop_action
    }

# =============================================================================
# GLOBAL HEATING SETTINGS
# =============================================================================
@app.callback(
    Output("global-heating-data", "data"),
    Input("global-heating-enabled", "value"),
    Input("global-heating-temperature", "value"),
    Input("global-heating-start", "value"),
    Input("global-heating-stop", "value"),
    prevent_initial_call=False
)
def update_global_heating_data(
    enabled, 
    temperature, 
    start_action, 
    stop_action
):
    """ 
    Stores the global heating settings selected in the query builder. 
    Converts the heating enable value to a boolean and stores the selected temperature and the actions at which heating should start and stop. 
    
    Args: 
        enabled: Indicates whether global heating is enabled. 
        temperature: Global heating temperature in °C. 
        start_action: Action number at which heating should start. 
        stop_action: Action number at which heating should stop. 
    
    Returns: 
        A dictionary containing the global heating configuration. 
    """

    
    return {
        "enabled": bool(enabled),
        "temperature": temperature,
        "start_action": start_action,
        "stop_action": stop_action
    }

# =============================================================================
# QUERY STATUS
# =============================================================================
@app.callback(
    Output("query-status","children"),
    Input("run-query","n_clicks"),
    Input("stop-query","n_clicks"),
    State("query-data","data"),
    State("global-stirring-data","data"),
    State("global-heating-data", "data"),

    prevent_initial_call=True

)

def query_control(

    run_clicks,
    stop_clicks,
    data,
    global_stirring,
    global_heating

):
    """ 
    Controls the execution of a configured query from the GUI. 
    Determines whether the user has selected Run or Stop, validates the query configuration, and starts or stops the query runner. 
    Status and error messages are returned to the interface. 
    
    Args: 
        run_clicks: Click count for the Run Query button. 
        stop_clicks: Click count for the Stop Query button. 
        data: Query-builder data containing the configured actions. 
        global_stirring: Global stirring configuration. 
        global_heating: Global heating configuration. 
    
    Returns: 
        A status message describing the current query state or any error. 
    """

    button = ctx.triggered_id

    if button == "run-query":

        if query_runner is None:
            return (
                "Query Runner unavailable."
                "IKA is disabled/not connected."
            )

        if not data:
            return "No query actions have been created."

        try:
            query_runner.run_query(data, global_stirring, global_heating)

            return "Query started."

        except Exception as e:

            return f"Query start error: {e}"

    if button == "stop-query":

        if query_runner is None:
            return "Query Runner unavailable."

        try:
            query_runner.stop_query()

            return "Query stopped."

        except Exception as e:

            return f"Query stop error: {e}"

    return "Query Status: Ready"

# =============================================================================
# SYNC DYNAMIC UI INPUTS TO QUERY-DATA STORE
# =============================================================================
@app.callback(
    Output("query-data", "data", allow_duplicate=True),
    Input({"type": "query-pump", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-volume", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-direction", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-mode", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-speed", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-stir-time", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-temperature", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-heat-time", "action": ALL, "operation": ALL}, "value"),
    Input({"type": "query-delay", "action": ALL}, "value"),
    Input({"type": "global-stir-start", "action": ALL}, "value"),
    Input({"type": "global-stir-stop", "action": ALL}, "value"),
    Input({"type": "global-heat-start", "action": ALL}, "value"),
    Input({"type": "global-heat-stop", "action": ALL}, "value"),
    State("query-data", "data"),

    prevent_initial_call=True
)

def sync_query_inputs_to_store(
    pumps, 
    volumes, 
    directions, 
    modes, 
    speeds, 
    times,
    temperatures,
    heat_times, 
    delays, 
    global_stir_starts, 
    global_stir_stops,
    global_heat_starts,
    global_heat_stops,
    query_data
):

    """ 
    Synchronises dynamically generated query-builder inputs with the stored query data. 
    Identifies the specific GUI input that changed using its pattern- matching component ID and updates the corresponding action, operation, or global setting in the query data. 
    
    Args: 
        pumps: Selected pump values for each pump operation. 
        volumes: Dispensing volumes for pump operations. 
        directions: Pump dispensing directions. 
        modes: Pump operating modes. 
        speeds: Stirring speeds for stirrer operations. 
        times: Stirring durations. 
        temperatures: Heating temperatures. 
        heat_times: Heating durations. 
        delays: Delays between query actions. 
        global_stir_starts: Global stirring start actions. 
        global_stir_stops: Global stirring stop actions. 
        global_heat_starts: Global heating start actions. 
        global_heat_stops: Global heating stop actions. 
        query_data: Current stored query configuration. 
    
    Returns: 
        The updated query data, or no update if the callback was not triggered. 
    """
    ctx = dash.ctx
    
    # If nothing triggered the callback, do not update the store
    if not ctx.triggered:
        return dash.no_update

    # Identify exactly which input was changed and grab its new value
    triggered_id = ctx.triggered_id
    new_value = ctx.triggered[0]["value"]

    action_idx = triggered_id.get("action")
    input_type = triggered_id.get("type")

    # Handle the delay input (which has no operation index)
    if input_type == "query-delay":
        query_data[action_idx]["delay"] = new_value
        return query_data

    # Handle global stirring start
    if input_type == "global-stir-start":
        query_data[action_idx]["global_stir_start"] = new_value
        return query_data

    # Handle global stirring stop
    if input_type == "global-stir-stop":
        query_data[action_idx]["global_stir_stop"] = new_value
        return query_data

    # Handle global heating start
    if input_type == "global-heat-start":
        query_data[action_idx]["global_heat_start"] = new_value
        return query_data

    # Handle global heating stop
    if input_type == "global-heat-stop":
        query_data[action_idx]["global_heat_stop"] = new_value
        return query_data

    # Handle all pump and stirrer operations
    op_idx = triggered_id.get("operation")

    # Map the Dash component ID type to the JSON keys
    key_map = {
        "query-pump": "pump",
        "query-volume": "volume",
        "query-direction": "direction",
        "query-mode": "mode",
        "query-speed": "speed",
        "query-stir-time": "duration",
        "query-temperature": "temperature",
        "query-heat-time": "duration"
    }

    # Update the exact value in the dictionary
    if input_type in key_map:
        json_key = key_map[input_type]
        query_data[action_idx]["operations"][op_idx][json_key] = new_value

    return query_data

# =============================================================================
# LIVE REFRESH CALLBACK (LOGS & TOTALS)
# =============================================================================
@app.callback(
    Output("pump-totals", "children"),
    Output("overall-total", "children"),

    Input("interval-component", "n_intervals")
)

def update_dashboard_logs(n):
    """ 
    Refreshes the dashboard's pump volume totals from the JSON log. 
    Loads the latest dispensing data, calculates the displayed totals for each pump, and updates the overall volume dispensed. 
    
    Args: 
        n: Number of intervals generated by the Dash interval component. Used to trigger periodic dashboard updates. 
    
    Returns: 
        A tuple containing the individual pump totals display and the overall dispensed volume display. 
    """
    log_data = load_JSON_log()

    totals = log_data.get("totals", {"A": 0, "B": 0, "C": 0, "D": 0})
    total_dispensed = log_data.get("total_volume_dispensed", 0)

    # Formatting totals by individual pump
    totals_display = html.Ul([
        html.Li(f"Pump {pump}: {vol:.2f} mL")
        for pump, vol in totals.items()
    ])

    overall_display = html.H4(
        f"Total Volume Dispensed: {total_dispensed:.2f} mL"
    )

    return totals_display, overall_display

# # =============================================================================
# # RUN APPLICATION IN BROWSER
# # =============================================================================

# ---------------------------------------------------------------------------
# Automatically starting the Dash Application in a window
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        webbrowser.open("http://127.0.0.1:8050")
        app.run(
            debug=False
        )

    finally:
        # ---------------------------------------------------------------------
        # Stop pumps
        # ---------------------------------------------------------------------
        try:
            close()

        except Exception:
            pass

        # ---------------------------------------------------------------------
        # Disconnect IKA
        # ---------------------------------------------------------------------
        if hotplate is not None:
            try:
                hotplate.disconnect()

            except Exception:
                pass


# ---------------------------------------------------------------------------
# Starting the Dash Application in the terminal
# ---------------------------------------------------------------------------

# if __name__ == "__main__":

#     try:

#         app.run(
#             debug=False
#         )


#     finally:

#         # Stop the pumps
#         close()


#         # Disconnect the IKA
#         if hotplate is not None:

#             hotplate.disconnect()