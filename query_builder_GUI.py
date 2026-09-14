# =============================================================================
#
# QUERY BUILDER GUI
#
# =============================================================================
# Program bridging the Query builder logic from query_bulilder.py and 
# GUI functionality within the main GUI program.
# Called in pump_main_GUI.py


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from dash import html
from dash import dcc

# =============================================================================
# STYLES IMPORTS
# =============================================================================
# Imports all relevant styles from the styles file
from GUI_styles import (
    query_builder_page_style,
    qr_global_controls_head_style,
    qr_global_IKA_head_style,
    qr_action_head_style,
    qr_global_IKA_divider,
    qr_global_IKA_action_change_style,
    qr_global_IKA_labels_style,
    qr_global_IKA_alignment,
    qr_global_IKA_box,
    qr_operation_style,
    qr_close_operation_style,
    qr_operation_box_style,
    qr_IKA_operation_style,
    qr_new_action_style,
    qr_action_box_style,
    qr_close_action_allign,
    qr_close_action_style,
    run_query_style,
    stop_query_style,
    qr_back_to_main_style,
    qr_status_style
)

# =============================================================================
# CREATE ACTION UI
# =============================================================================
def create_action_ui(action_number, action):
    """
    Dynamically builds the GUI for a single query action.

    Creates the action container, displays existing pump, stirring, and
    heating operations, provides controls for adding or deleting operations,
    configures action delays, and manages global stirring and heating changes.
    """

    # Safely handle both Dictionaries AND Lists so Python never throws an AttributeError
    if isinstance(action, dict):
        operations = action.get("operations", [])
    elif isinstance(action, list):
        operations = action
    else:
        operations = []

    operation_components = []


    # =========================================================================
    # EXISTING OPERATIONS
    # =========================================================================
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
    for index, operation in enumerate(operations):
        operation_type = operation.get("type")

        # PUMP OPERATION
        if operation_type == "pump":
            operation_components.append(
                html.Div([
                    html.Div([
                        html.H4(f"Pump Operation {index + 1}"),
                        html.Button(
                            "X",
                            id={"type": "delete-operation", 
                                "action": action_number, 
                                "operation": index},
                            n_clicks=0,
                            style=qr_close_operation_style
                        )
                    ], style=qr_IKA_operation_style
                    ),

                    html.Div([
                        dcc.Dropdown(
                            id={
                                "type": "query-pump", 
                                "action": action_number, 
                                "operation": index},
                            options=[{"label": f"Pump {p}", 
                                      "value": p} for p in ["A", "B", "C", "D"]],
                            value=operation.get("pump", "A"),
                            clearable=False,
                            style={"width": "180px"}
                        ),
                        dcc.Input(
                            id={
                                "type": "query-volume", 
                                "action": action_number, 
                                "operation": index},
                            type="number", 
                            min=0,
                            max=None, 
                            step=0.1,
                            value=operation.get("volume"),
                            placeholder="Volume (mL)",
                            style={"width": "150px"}
                        ),
                        dcc.Dropdown(
                            id={
                                "type": "query-direction", 
                                "action": action_number, 
                                "operation": index},
                            options=[{
                                "label": "Forward", 
                                "value": "forward"
                                },

                                {
                                "label": "Reverse", 
                                "value": "reverse"
                                }],
                            value=operation.get(
                                "direction", 
                                "forward"),
                            clearable=False,
                            style={"width": "150px"}
                        ),
                        dcc.Dropdown(
                            id={
                                "type": "query-mode", 
                                "action": action_number, 
                                "operation": index},
                            options=[{
                                "label": "Continuous", 
                                "value": "continuous"
                                }, 
                                {
                                "label": "Drop-wise", 
                                "value": "dropwise"
                                 }],
                            value=operation.get(
                                "mode", 
                                "continuous"
                                ),
                            clearable=False,
                            style={"width": "170px"}
                        )
                    ], style=qr_operation_style

                    )
                ])
            )

        # STIRRER OPERATION
        elif operation_type == "stirrer":
            operation_components.append(
                html.Div([
                    html.Div([
                        html.H4(f"Stirrer Operation {index + 1}"),
                        html.Button(
                            "X",
                            id={
                                "type": "delete-operation", 
                                "action": action_number, 
                                "operation": index},
                            n_clicks=0,
                            style=qr_close_operation_style
                        )
                    ], style=qr_IKA_operation_style
                    ),

                    html.Div([
                        dcc.Input(
                            id={
                                "type": "query-speed", 
                                "action": action_number, 
                                "operation": index},
                            type="number", 
                            min=50, 
                            max=1500, 
                            step=1,
                            value=operation.get("speed"),
                            placeholder="Speed (rpm)",
                            style={"width": "150px"}
                        ),
                        dcc.Input(
                            id={
                                "type": "query-stir-time", 
                                "action": action_number, 
                                "operation": index},
                            type=
                            "number", 
                            min=0,
                            max=None, 
                            step=1,
                            value=operation.get("duration"),
                            placeholder="Time (s)",
                            style={"width": "150px"}
                        )
                    ], style=qr_operation_style

                    )
                ])
            )

        # HEATING OPERATION
        elif operation_type == "heating":
            operation_components.append(
                html.Div([
                    html.Div([
                        html.H4(f"Heating Operation {index + 1}"),
                        html.Button(
                            "X",
                            id={
                                "type": "delete-operation", 
                                "action": action_number, 
                                "operation": index
                            },
                            n_clicks=0,
                            style=qr_close_operation_style
                        )
                    ], style=qr_IKA_operation_style
                    ),

                    html.Div([
                        dcc.Input(
                            id={
                                "type": "query-temperature", 
                                "action": action_number, 
                                "operation": index
                            },
                            type="number", 
                            min=0, 
                            max=310, 
                            step=1,
                            value=operation.get("temperature"),
                            placeholder="Temp (°C)",
                            style={"width": "150px"}
                        ),
                        dcc.Input(
                            id={
                                "type": "query-heat-time", 
                                "action": action_number, 
                                "operation": index
                            },
                            type="number", 
                            min=0,
                            max=None, 
                            step=1,
                            value=operation.get("duration"),
                            placeholder="Time (s)",
                            style={"width": "150px"}
                        )
                    ], style=qr_operation_style

                    )
                ])
            )

    # =========================================================================
    # ACTION BOX
    # =========================================================================
    return html.Div([
        html.Div([
            html.H2(
                f"ACTION {action_number + 1}",
                style=qr_action_head_style
            ),

            html.Button(
                "X",
                id={
                    "type": "delete-action",
                    "action": action_number
                },
                n_clicks=0,
                style=qr_close_action_style
            )

        ],
        style=qr_close_action_allign
            
        ),

        html.Div(
            operation_components,
            style=qr_operation_box_style
        ),

        # =====================================================================
        # ADD OPERATION BUTTONS
        # =====================================================================
        html.Button(
            "Add Pump Operation",

            id={
                "type": "add-pump-operation",
                "action": action_number
            },

            style={
                "marginRight": "10px",
                "height": "35px"
            }
        ),

        html.Button(
            "Add Stirrer Operation",

            id={
                "type": "add-stirrer-operation",
                "action": action_number
            },

            style={"height": "35px"}
        ),

        html.Button(
            "Add Heating Operation",
            id={
                "type": "add-heating-operation",
                "action": action_number
            },
            style={
                "marginLeft": "10px", 
                "height": "35px"
            }
        ),

        # =====================================================================
        # DELAY
        # =====================================================================
        html.Div([
            html.Label(
                "Delay before next action (seconds): ",
                style={
                    "fontWeight": "bold",
                    "marginRight": "10px"
                }
            ),

            dcc.Input(
                id={
                    "type": "query-delay",
                    "action": action_number
                },
                type="number",
                min=0,
                max=None,
                step=1,
                value=action.get(
                    "delay",
                    0
                ),
                placeholder="seconds",
                style={"width": "120px"}
            )

        ],

        style={
            "marginTop": "20px",
            "marginBottom": "15px"
        }),

        # =====================================================================
        # GLOBAL STIRRING & HEATING
        # =====================================================================
        html.Div([
            html.Label(
                "Global Stirring", 
                style={
                    "fontWeight": "bold", 
                    "marginRight": "10px"
                    }
            ),

            dcc.Dropdown(
                id={
                    "type": "global-stir-start", 
                    "action": action_number
                },
                options=[
                    {
                        "label": "No change", 
                        "value": "none"
                    }, 
                    {
                        "label": "START stirring", 
                        "value": "start"
                    }
                ],
                value=action.get("global_stir_start", "none"),
                clearable=False,
                style=qr_global_IKA_action_change_style
            ),
            dcc.Dropdown(
                id={"type": "global-stir-stop", "action": action_number},

                options=[
                    {
                        "label": "No change", 
                        "value": "none"
                        }, 
                        {
                        "label": "STOP stirring", 
                        "value": "stop"
                        }
                    ],
                value=action.get("global_stir_stop", "none"),
                clearable=False,
                style=qr_global_IKA_action_change_style
            )
        ], style={"marginBottom": "15px"}),

        html.Hr(
            style={"borderTop": "1px solid #ccc"}
        ),

        html.Div([
            html.Label(
                "Global Heating", 
                style={
                    "fontWeight": "bold", 
                    "marginRight": "10px"
                }
            ),
            dcc.Dropdown(
                id={
                    "type": "global-heat-start", 
                    "action": action_number
                },
                options=[
                    {
                        "label": "No change", 
                        "value": "none"
                    }, 
                    {
                        "label": "START heating", 
                        "value": "start"
                    }
                ],
                value=action.get(
                    "global_heat_start", 
                    "none"
                ),
                clearable=False,
                style=qr_global_IKA_action_change_style
            ),
            dcc.Dropdown(
                id={
                    "type": "global-heat-stop", 
                    "action": action_number
                },
                options=[
                    {
                        "label": "No change", 
                        "value": "none"
                    }, 
                    {
                        "label": "STOP heating", 
                        "value": "stop"
                    }
                ],
                value=action.get("global_heat_stop", "none"),
                clearable=False,
                style=qr_global_IKA_action_change_style
            )
        ], style={"marginBottom": "20px"})
    ],
        style=qr_action_box_style
    )


# =============================================================================
# QUERY BUILDER LAYOUT
# =============================================================================
def query_builder_layout():
    """
    Builds the main Query Builder page layout.

    Creates the Dash data stores, global stirring and heating controls,
    dynamic action container, query execution controls, status display,
    and navigation back to the main GUI.
    """
    return html.Div([
        # ---------------------------------------------------------------------
        # Query data store
        # ---------------------------------------------------------------------
        dcc.Store(
            id="query-data",

            data=[
                {
                    "operations": [],
                    "delay": 0,
                    "global_stir_start": "none",
                    "global_stir_stop": "none",
                    "global_heat_start": "none",
                    "global_heat_stop": "none"
                }
            ]
        ),

        # ---------------------------------------------------------------------
        # Global stirring data store
        # ---------------------------------------------------------------------
        dcc.Store(
            id="global-stirring-data",
            data={
                "enabled": False,
                "speed": 300,
                "start_action": None,
                "stop_action": None
            }
        ),

        # ---------------------------------------------------------------------
        # Global heating data store
        # ---------------------------------------------------------------------
        dcc.Store(
            id="global-heating-data",
            data={
                "enabled": False,
                "temperature": 50,
                "start_action": None,
                "stop_action": None
            }
        ),

        # ---------------------------------------------------------------------
        # Title
        # ---------------------------------------------------------------------
        html.H1(
            "Query Builder",

            style={"textAlign": "center"}
        ),

        html.Hr(),

        # ---------------------------------------------------------------------
        # GLOBAL CONTROLS
        # ---------------------------------------------------------------------
        html.Div([

            html.H2(
                "Global Controls",
                style=qr_global_controls_head_style
            ),

            html.Div([

                # =============================================================
                # GLOBAL STIRRING
                # =============================================================
                html.Div([

                    html.H3(
                        "Global Stirring",
                        style=qr_global_IKA_head_style
                    ),

                    # Enable global stirring
                    dcc.Checklist(
                        id="global-stirring-enabled",
                        options=[
                            {
                                "label": " Enable global stirring",
                                "value": "enabled"
                            }
                        ],
                        value=[],
                        style={"marginBottom": "15px"}
                    ),

                    # Stirring speed
                    html.Div([

                        html.Label(
                            "Stirring speed (RPM): ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Input(
                            id="global-stirring-speed",
                            type="number",
                            min=50,
                            max=1500,
                            step=1,
                            value=300,
                            style={"width": "120px"}
                        )

                    ], style={"marginBottom": "15px"}
                    ),

                    # Start action
                    html.Div([

                        html.Label(
                            "Start stirring at: ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Dropdown(
                            id="global-stirring-start",
                            options=[],
                            placeholder="Select start action",
                            clearable=True,
                            style={"width": "250px"}
                        )

                    ], style={"marginBottom": "15px"}
                    ),

                    # Stop action
                    html.Div([

                        html.Label(
                            "Stop stirring after: ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Dropdown(
                            id="global-stirring-stop",
                            options=[],
                            placeholder="Select stop action",
                            clearable=True,
                            style={"width": "250px"}
                        )
                    ])
                ],
                style={"width": "48%"}
                ),


                # =============================================================
                # DIVIDER
                # =============================================================
                html.Div(
                    style=qr_global_IKA_divider
                ),

                # =============================================================
                # GLOBAL HEATING
                # =============================================================
                html.Div([

                    html.H3(
                        "Global Heating",
                        style=qr_global_IKA_head_style
                    ),

                    # Enable global heating
                    dcc.Checklist(
                        id="global-heating-enabled",
                        options=[
                            {
                                "label": " Enable global heating",
                                "value": "enabled"
                            }
                        ],
                        value=[],
                        style={"marginBottom": "15px"}
                    ),

                    # Heating temperature
                    html.Div([

                        html.Label(
                            "Temperature (°C): ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Input(
                            id="global-heating-temperature",
                            type="number",
                            min=0,
                            max=300,
                            step=1,
                            value=50,
                            style={"width": "120px"}
                        )

                    ], style={"marginBottom": "15px"}
                    ),

                    # Start action
                    html.Div([

                        html.Label(
                            "Start heating at: ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Dropdown(
                            id="global-heating-start",
                            options=[],
                            placeholder="Select start action",
                            clearable=True,
                            style={"width": "250px"}
                        )

                    ], style={"marginBottom": "15px"}
                    ),

                    # Stop action
                    html.Div([

                        html.Label(
                            "Stop heating after: ",
                            style=qr_global_IKA_labels_style
                        ),

                        dcc.Dropdown(
                            id="global-heating-stop",
                            options=[],
                            placeholder="Select stop action",
                            clearable=True,
                            style={"width": "250px"}
                        )

                    ])

                ],
                style={"width": "48%"}
                )

            ],
            style=qr_global_IKA_alignment
            )

        ],
        style=qr_global_IKA_box
        ),

        
        # ---------------------------------------------------------------------
        # Actions
        # ---------------------------------------------------------------------
        html.Div(
            id="query-actions"
        ),

        # ---------------------------------------------------------------------
        # New action
        # ---------------------------------------------------------------------
        html.Button(
            "NEW ACTION",
            id="new-action",
            style=qr_new_action_style
        ),

        # ---------------------------------------------------------------------
        # Run query
        # ---------------------------------------------------------------------
        html.Button(
            "RUN QUERY",
            id="run-query",
            style=run_query_style
        ),

        # ---------------------------------------------------------------------
        # Stop query
        # ---------------------------------------------------------------------
        html.Button(
            "STOP QUERY",
            id="stop-query",
            style=stop_query_style
        ),

        # ---------------------------------------------------------------------
        # Query status
        # ---------------------------------------------------------------------
        html.Br(),
        html.Br(),
        html.Div(
            "Query Status: Ready",
            id="query-status",
            style=qr_status_style
        ),

        # ---------------------------------------------------------------------
        # Back button
        # ---------------------------------------------------------------------
        html.Button(
            "BACK TO MAIN",
            id="back-to-main",
            style=qr_back_to_main_style
        )
    ],
    style=query_builder_page_style
    )