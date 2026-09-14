# =============================================================
#
# STYLES LIBRARY FOR THE PERISTALTIC PUMP CONTROLLER GUI
#
# =============================================================
# This file stores all of the GUI styles imported into the GUI

# =============================================================
# MAIN CONTROLLER
# =============================================================

# HEADERS -----------------------------------------------------
pump_head_style = {
    "display": "inline-block",
    "width": "150px",
    "fontWeight": "bold"
}

volume_head_style = {
    "display": "inline-block",
    "width": "150px",
    "fontWeight": "bold",
    "marginLeft": "-45px"
}

direction_head_style = {
    "display": "inline-block",
    "width": "150px",
    "fontWeight": "bold",
    "marginLeft": "32px"
}

dispensing_head_style = {
    "display": "inline-block",
    "width": "150px",
    "fontWeight": "bold",
    "marginLeft": "18px"
}

status_head_style = {
    "display": "inline-block", 
    "width": "100px", 
    "fontWeight": "bold", 
    "textAlign": "center",
    "marginLeft": "60px"
}

maintenance_head_style = {
    "display": "inline-block", 
    "width": "150px", 
    "fontWeight": "bold", 
    "textAlign": "center",
    "marginLeft": "24px"
}

# INDIVIDUAL PUMP FUNCTIONS -----------------------------------
pump_selection_style = {
    "display": "inline-block",
    "fontSize": "20px",
    "marginRight": "50px"
}

volume_style = {
    "width": "140px",
    "marginRight": "40px"
}

direction_style = {
    "width": "140px",
    "display": "inline-block",
    "marginRight": "40px"
}

mode_style = {
    "width": "170px",
    "display": "inline-block",
    "marginRight": "40px"
}

prime_status_style = {
    "display": "inline-block", 
    "width": "90px", 
    "padding": "5px", 
    "margin": "0 10px", 
    "border": "1px solid black", 
    "textAlign": "center",
    "marginRight": "40px"
}

prime_button_style = {
    "height": "30px",
    "marginRight": "5px"
}

# DISPENSE BUTTON ---------------------------------------------
dispense_style = {
    "width": "80%",
    "height": "40px",
    "fontSize": "18px",
    "fontWeight": "bold",
    "display": "block",
    "margin": "20px auto"
}

# STOP BUTTONS ------------------------------------------------
stop_button_style = {
    "width": "100px",
    "height": "45px",
    "fontSize": "18px",
    "fontWeight": "bold",
    "marginRight": "20px"
}

stop_all_button_style = {
    "width": "80%",
    "height": "40px",
    "fontSize": "18px",
    "fontWeight": "bold",
    "display": "block",
    "margin": "20px auto"
}

# CLEAR TALLY BUTTON ------------------------------------------
total_clear_style = {
    "width": "80%",
    "height": "40px",
    "fontSize": "18px",
    "fontWeight": "bold",
    "display": "block",
    "margin": "20px auto"
}

# STIRRER-HOTPLATE FUNCTIONS ----------------------------------
hotplate_input_style = {
    "width": "120px",
    "marginRight": "10px"
}

hotplate_button_style = {
    "height": "35px",
    "fontSize": "16px",
    "fontWeight": "bold",
    "marginRight": "10px"
}

ika_status_style = {
    "border": "1px solid black",
    "padding": "10px",
    "minHeight": "30px"
}


# OPEN QUERY BUILDER STYLE ------------------------------------
open_query_builder_style = {
    "width": "100%",
    "height": "50px",
    "fontSize": "20px",
    "fontWeight": "bold"
}

# OVERALL SECTION STYLES --------------------------------------
hotplate_section_style = {
    "border": "1px solid black",
    "padding": "20px",
    "marginTop": "15px"
}

pump_section_style = {
    "border": "1px solid black",
    "padding": "20px",
    "marginTop": "15px"
}

# =============================================================
# QUERY BUILDER
# =============================================================
query_builder_page_style = {
    "width": "1000px",
    "maxWidth": "95%",
    "margin": "auto",
    "fontFamily": "Arial"
}

# HEADERS -----------------------------------------------------
qr_global_controls_head_style = {
    "marginTop": "0",
    "marginBottom": "20px",
    "textAlign": "center"
}

qr_global_IKA_head_style = {
    "marginTop": "0",
    "marginBottom": "15px"
}

qr_action_head_style = {
    "margin": "0"
}

# GLOBAL IKA FUNCTIONS ----------------------------------------
qr_global_IKA_divider = {
    "borderLeft": "2px solid black",
    "height": "280px",
    "margin": "0 20px"
}

qr_global_IKA_action_change_style = {
    "width": "180px", 
    "display": "inline-block", 
    "marginRight": "20px"
}

qr_global_IKA_labels_style = {
    "fontWeight": "bold",
    "marginRight": "10px"
}

qr_global_IKA_alignment = {
    "display": "flex",
    "alignItems": "flex-start",
    "justifyContent": "space-between"
}

qr_global_IKA_box = {
    "border": "2px solid black",
    "padding": "20px",
    "marginBottom": "25px"
}

# OPERATIONS --------------------------------------------------
qr_operation_style = {
    "display": "flex", 
    "gap": "10px", 
    "alignItems": "center", 
    "marginBottom": "10px"
}

qr_close_operation_style = {
    "width": "30px", 
    "height": "30px", 
    "fontSize": "16px", 
    "fontWeight": "bold", 
    "marginLeft": "auto"
}

qr_operation_box_style = {
    "border": "1px solid black",
    "padding": "15px",
    "marginBottom": "15px"
}

qr_IKA_operation_style = {
    "display": "flex", 
    "alignItems": "center", 
    "marginBottom": "10px"
}

# ACTIONS -----------------------------------------------------
qr_new_action_style ={
    "width": "100%",
    "height": "50px",
    "fontSize": "20px",
    "fontWeight": "bold",
    "marginTop": "10px"
}

qr_action_box_style = {
    "border": "2px solid black",
    "padding": "20px",
    "marginBottom": "20px"
}

qr_close_action_allign = {
    "display": "flex",
    "justifyContent": "space-between",
    "alignItems": "center",
    "marginBottom": "15px"
}

qr_close_action_style = {
    "width": "35px",
    "height": "35px",
    "fontSize": "18px",
    "fontWeight": "bold"
}

# MAIN QUERY FUNCTION BUTTONS ---------------------------------
run_query_style = {
    "width": "100%",
    "height": "60px",
    "fontSize": "24px",
    "fontWeight": "bold",
    "marginTop": "30px"
}

stop_query_style = {
    "width": "100%",
    "height": "50px",
    "fontSize": "20px",
    "fontWeight": "bold",
    "marginTop": "15px"
}

qr_back_to_main_style = {
    "width": "100%",
    "height": "45px",
    "fontSize": "18px",
    "fontWeight": "bold",
    "marginTop": "20px"
}

# STATUS STYLE ------------------------------------------------
qr_status_style = {
    "border": "1px solid black",
    "padding": "10px",
    "minHeight": "30px"
}