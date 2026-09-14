# =============================================================================
#
# PYSERIAL MAIN CODE
#
# =============================================================================
# Resposnible for the main python side pump operation logic and establishing the 
# serial connection with Arduino. 
# Used by calling on its functions in separate files, including the GUI.


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import serial
import time
import json
import csv
import threading
import shutil
import os
import queue

from datetime import datetime

# -----------------------------------------------------------------------------
# Calibration factors for Volume to runtime conversion
# -----------------------------------------------------------------------------
# These values have been experimentally derived to allow for a volume to runtime conversion

# Initially derived values
# CAL = {"A": 0.00123, "B": 0.00127, "C": 0.00125, "D": 0.00125}

# New calibration values (for water-based solutions)
CAL = {"A": 0.00119895, "B": 0.00125173, "C": 0.00124938, "D": 0.00128198}

# -----------------------------------------------------------------------------
# Drop-wise-dispension stop dictionary
# -----------------------------------------------------------------------------
# The variables stored are threading events used to interrupt dropwise dispensing.
# Each pump has its own Event object so that a single pump can be stopped without affecting the others.

dropwise_stop = {
    "A": threading.Event(),
    "B": threading.Event(),
    "C": threading.Event(),
    "D": threading.Event()
}

# -----------------------------------------------------------------------------
# Connection safeguarding variables
# -----------------------------------------------------------------------------
serial_connected = False
serial_lock = threading.Lock()

# Used to signal that the Arduino connection has been restored
connection_restored = threading.Event()

# -----------------------------------------------------------------------------
# Fake serial connection for testing
# -----------------------------------------------------------------------------
# When lines 64-71 are uncommented, it allows the user to test the code changes remotely

# class FakeSerial:
#     def __init__(self, *args, **kwargs):
#         self.in_waiting = 0
        
#     def write(self, data):
#         print(f"FAKE ARDUINO RECEIVED: {data.decode() if isinstance(data, bytes) else data}")
        
# ser = FakeSerial()

# -----------------------------------------------------------------------------
# Real Arduino connection
# -----------------------------------------------------------------------------

# Safeguarding implemented --------------------------------------------
def pump_connect():
    """
    Establishes a serial connection to the Arduino pump controller.

    Safely closes any existing connection, waits for the Arduino to reset,
    clears the serial buffers, restores the connection state, and starts
    a dedicated serial reader thread. Returns True on success and False
    if the connection fails.
    """

    global ser, serial_thread, serial_connected

    with serial_lock:

        try:
            # Tell the old reader thread to stop
            serial_connected = False

            # Close existing connection if necessary
            if ser is not None and ser.is_open:
                try:
                    ser.close()
                except Exception:
                    pass

            print("Connecting to pump controller...")

            # Open new serial connection
            ser = serial.Serial(
                "COM5",
                9600,
                timeout=1
            )

            # Arduino resets when serial connection is opened
            print("Waiting for Arduino to reset...")
            time.sleep(2)

            # Flush any startup messages
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            serial_connected = True

            # Signal that the connection is available again
            connection_restored.set()

            print("Pump controller connected.")

            # Start a new reader thread
            serial_thread = threading.Thread(
                target=serial_reader,
                daemon=True
            )

            serial_thread.start()

            return True

        except (
            serial.SerialException,
            OSError
        ) as e:

            serial_connected = False

            print(f"Pump connection failed: {e}")

            return False

# -----------------------------------------------------------------------------
# Arduino serial response reader
# -----------------------------------------------------------------------------
# def serial_reader():
#     """Continuously reads Arduino responses and sends DONE messages
#     to the queue belonging to the correct pump."""

#     while ser.is_open:

#         if ser.in_waiting:

#             message = ser.readline().decode().strip()

#             print("Arduino:", message)

#             if message.startswith("DONE,"):

#                 pump = message.split(",", 1)[1]

#                 if pump in done_queues:
#                     done_queues[pump].put(True)

#         else:
#             time.sleep(0.01)

#------------------------------------------------------------------------------

# Diagnostic version of the serial reader
def serial_reader():
    """
    Continuously reads Arduino responses.

    DONE messages are placed into the queue belonging to the
    corresponding pump.

    If the serial connection disappears, serial_connected is
    set to False so that the connection monitor can reconnect.
    """

    global serial_connected

    current_connection = ser

    print("Arduino serial reader started.")

    while serial_connected:

        try:

            # Make sure the connection being monitored is still valid
            if (
                current_connection is None
                or not current_connection.is_open
            ):
                serial_connected = False
                break

            if current_connection.in_waiting:

                message = current_connection.readline().decode(errors="replace").strip()

                if message:
                    print("Arduino:", message)

                # -------------------------------------------------------------
                # Successful pump completion
                # -------------------------------------------------------------

                if message.startswith("DONE,"):

                    pump = message.split(",", 1)[1].strip()

                    if pump in done_queues:

                        done_queues[pump].put(True)

                        print(f"Pump {pump} completion confirmed.")

            else:
                time.sleep(0.01)

        except (
            serial.SerialException,
            OSError
        ) as e:

            print(f"Arduino serial connection lost: {e}")

            serial_connected = False

            # Make sure any code waiting for a connection can react
            connection_restored.clear()

            break

    print("Arduino serial reader stopped.")


# Uncomment when launching the stand-alone system
#pump_connect()

# -----------------------------------------------------------------------------
# Connection monitor
# -----------------------------------------------------------------------------

def serial_connection_monitor():
    """
    Continuously monitors the Arduino connection and handles reconnection.

    Attempts to reconnect whenever the serial connection is unavailable,
    retrying every two seconds until the Arduino connection is restored.
    """
    global serial_connected

    while True:

        if not serial_connected:
            print("\nArduino connection unavailable.")

            print("Attempting to reconnect to Arduino...")

            if pump_connect():
                print("Arduino reconnected successfully.")

                connection_restored.set()

            else:
                print(
                    "Arduino reconnect failed. "
                    "Retrying in 2 seconds..."
                )

                time.sleep(2)

        time.sleep(1)

# -----------------------------------------------------------------------------
# Data saving
# -----------------------------------------------------------------------------
# Storing the information about every pump currently dispensing.
# This data is used to estimate the volume transferred if a pump is stopped before completing its target volume.
active_pumps = {} 

# Serial response queues ------------------------------------------------------
done_queues = {
    "A": queue.Queue(),
    "B": queue.Queue(),
    "C": queue.Queue(),
    "D": queue.Queue()
}

# -----------------------------------------------------------------------------
# Operation Recovery / Checkpointing
# -----------------------------------------------------------------------------

OPERATION_STATE_FILE = "operation_state.json"

operation_state_lock = threading.Lock()


def create_default_operation_state():
    """
    Creates the default state used when no pump operation is active.
    """

    return {
        "running": False,
        "pump": None,
        "command": None,
        "target_volume": None,
        "direction": None,
        "start_time": None,
        "estimated_dispensed": 0.0,
        "remaining_volume": None,
        "completed": False
    }


def save_operation_state(state):
    """
    Saves the current pump operation state to disk.

    A temporary file is used first so that a partially-written JSON
    file is not left behind if Python is interrupted.
    """

    with operation_state_lock:

        temp_file = OPERATION_STATE_FILE + ".tmp"

        with open(temp_file, "w") as file:

            json.dump(
                state,
                file,
                indent=4
            )

        os.replace(
            temp_file,
            OPERATION_STATE_FILE
        )


def load_operation_state():
    """
    Loads the saved operation state.
    """

    try:

        with open(
            OPERATION_STATE_FILE,
            "r"
        ) as file:

            return json.load(file)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return create_default_operation_state()


def clear_operation_state():
    """
    Clears the saved recovery state.
    """

    save_operation_state(
        create_default_operation_state()
    )


def save_current_operation(
    pump,
    command,
    volume,
    direction
):
    """
    Saves the operation before the pump is started.
    """

    state = {

        "running": True,

        "pump": pump,

        "command": command,

        "target_volume": volume,

        "direction": direction,

        "start_time": time.time(),

        "estimated_dispensed": 0.0,

        "remaining_volume": volume,

        "completed": False
    }

    save_operation_state(state)


def update_operation_progress(
    pump,
    estimated_dispensed,
    remaining_volume
):
    """
    Updates the estimated progress of the current operation.
    """

    state = load_operation_state()

    state["estimated_dispensed"] = round(
        estimated_dispensed,
        6
    )

    state["remaining_volume"] = round(
        max(remaining_volume, 0),
        6
    )

    save_operation_state(state)


def mark_operation_complete():
    """
    Clears the recovery state after a pump operation has been successfully confirmed by the Arduino.
    """

    clear_operation_state()

# Connection waiting -----------------------------------------------------------
def wait_for_reconnection():
    """
    Waits until the Arduino serial connection is restored.

    Polls the connection status until the Arduino becomes available,
    then allows a short delay for the controller to finish resetting.
    Returns True once the connection has been restored.
    """

    print("\nWaiting for Arduino connection to be restored...")

    while not serial_connected:

        time.sleep(0.5)

    print("Arduino connection restored.")

    # Give Arduino time to finish resetting
    time.sleep(0.5)

    return True

# Operation recovery ------------------------------------------------------------
def recover_previous_operation():
    """
    Recovers an interrupted pump operation after a connection failure.

    Loads the previously saved operation state, validates the recovery
    information, checks for any remaining volume, waits for the Arduino
    connection to be restored, and resumes the interrupted pump operation.
    Clears the saved state if the operation is invalid or already complete.
    """

    state = load_operation_state()

    if not state.get("running", False):

        print("No interrupted pump operation found.")

        return

    pump = state.get("pump")
    command = state.get("command")
    target_volume = state.get("target_volume")
    remaining_volume = state.get("remaining_volume")

    # -------------------------------------------------------------------------
    # Validate recovery state
    # -------------------------------------------------------------------------

    if (
        pump is None
        or command is None
        or target_volume is None
        or remaining_volume is None
    ):

        print("Invalid recovery state found.")

        clear_operation_state()

        return

    # -------------------------------------------------------------------------
    # Nothing left to dispense
    # -------------------------------------------------------------------------

    if remaining_volume <= 0.001:

        print("Previous operation appears to be complete.")

        clear_operation_state()

        return

    # -------------------------------------------------------------------------
    # Display recovery information
    # -------------------------------------------------------------------------

    print("\n" + "=" * 60)
    print("PREVIOUS INCOMPLETE OPERATION DETECTED")
    print("=" * 60)

    print(
        f"Pump: {pump}"
    )

    print(
        f"Original target: "
        f"{target_volume:.3f} mL"
    )

    print(
        f"Estimated dispensed: "
        f"{state.get('estimated_dispensed', 0):.3f} mL"
    )

    print(
        f"Estimated remaining: "
        f"{remaining_volume:.3f} mL"
    )

    print("=" * 60)

    print("Waiting for Arduino connection...")

    wait_for_reconnection()

    # -------------------------------------------------------------------------
    # start_pump() recognises this as a recovery because the saved state
    # matches the pump and command.
    # -------------------------------------------------------------------------

    start_pump(command, target_volume)

# CSV -------------------------------------------------------------------------

try:
    with open("pump_log.csv", "x", newline="") as file:

        writer = csv.writer(file)

        # Write the column headings
        writer.writerow([
            "timestamp",
            "pump",
            "volume_ml",
            "completed"
        ])

# Do nothing in case the file already exists
except FileExistsError:
    pass

# Saving the file
def save_csv_log(pump, volume, completed):
    """
    Records one dispensing operation in the CSV log.
    Each row contains: a timestamp, pump identifier, 
    transferred volume and information whether dispensing was completed successfully.
        
    Args:
        pump - Identifier of the used pump (A, B, C, D)
        volume - volume transferred
        completed- True if dispensing completed normally, False otherwise
    """

    # Opens the CSV file in append mode
    with open("pump_log.csv", "a", newline="") as file:

        writer = csv.writer(file)

        # Writes one dispensing event
        writer.writerow([datetime.now().isoformat(), pump, round(volume, 2), completed])


# JSON ------------------------------------------------------------------------
def load_JSON_log():
    """ 
    Opens the JSON log file and returns its contents.
    If the file does not exist, a new data structure is created with empty totals and event history.
    """

    try:
        with open("pump_log.json", "r") as file:
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

# Saving the JSON file
def save_JSON_log(data):
    """
    Writes the current transfer statistics and event history to the JSON log file.
    """

    with open("pump_log.json", "w") as file:
        json.dump(data, file, indent=4)

# -----------------------------------------------------------------------------
# Saving and clearing the dispensing tally
# -----------------------------------------------------------------------------
def save_and_clear_logs():
    """
    Archives the current pump log files and resets them for a new run.

    Creates a timestamped archive of the existing JSON and CSV logs,
    then clears both files and initializes them with empty/default
    logging data.
    """
    os.makedirs("Archives", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    shutil.copy(
        "pump_log.json",
        f"Archives/pump_log_{timestamp}.json"
    )

    shutil.copy(
        "pump_log.csv",
        f"Archives/pump_log_{timestamp}.csv"
    )

    # Loading the new, clean JSON file
    save_JSON_log({
        "totals":{
            "A":0,
            "B":0,
            "C":0,
            "D":0
        },
        "total_volume_dispensed":0,
        "events":[]
    })

    # Loading the new, clean csv file
    with open("pump_log.csv","w",newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "timestamp",
            "pump",
            "volume_ml",
            "completed"
        ])

# -----------------------------------------------------------------------------
# Tracking the transfer data
# -----------------------------------------------------------------------------

log_lock = threading.Lock() # Creating a lock object to allow for only one thread writing the log at a time

def log_transfer(pump, volume, completed):
    """
    Updates both the JSON and CSV log files with information about a dispensing operation,
    including the pump totals, overall transferred volume and the transfer history.
    """
    with log_lock:
        # Loading the JSON file
        data = load_JSON_log() # Dictionary containing all of the transfer data

        # Updating the selected pump total
        data["totals"][pump] += volume

        # Updating the overall transferred volume
        data["total_volume_dispensed"] += volume

        # Storing one transfer event
        data["events"].append({
            "timestamp": datetime.now().isoformat(),
            "pump": pump,
            "volume_mL": round(volume, 2),
            "completed": completed,
            "direction": "reverse" if volume < 0 else "forward"
        })

        # Saving the updated JSON file
        save_JSON_log(data)

        # Saving the updated csv file
        save_csv_log(pump, volume, completed)

# -----------------------------------------------------------------------------
# Pump Priming Status Persistence
# -----------------------------------------------------------------------------
def load_pump_status():
    """
    Loads the priming state from pump_status.json.
    Creates default dictionary if file does not exist.
    """
    try:
        with open("pump_status.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"A": "Unprimed", "B": "Unprimed", "C": "Unprimed", "D": "Unprimed"}


def save_pump_status(status_dict):
    """Saves the priming state to pump_status.json."""
    with open("pump_status.json", "w") as file:
        json.dump(status_dict, file, indent=4)

# -----------------------------------------------------------------------------
# CLI Maintenance & Priming (for UR5e / Standalone execution)
# -----------------------------------------------------------------------------

def display_pump_status(status):
    """
    Prints a formatted status box to the terminal.
    """
    print("\n" + "=" * 35)
    print("      CURRENT PUMP STATUSES")
    print("=" * 35)
    for pump, state in status.items():
        symbol = "[X]" if state == "Primed" else "[ ]"
        print(f"  Pump {pump}: {symbol} {state}")
    print("=" * 35)


def run_cli_priming_setup():
    """
    Provides an interactive CLI menu for managing pump priming.

    Allows individual or all pumps to be primed or emptied, displays
    current pump status, prevents unnecessary operations, and saves
    updated pump states before the main script continues.
    """
    status = load_pump_status()
    display_pump_status(status)

    print("\nCOMMANDS:")
    print("  PA, PB, PC, PD  -> Prime individual pump (6.7 mL)")
    print("  EA, EB, EC, ED  -> Empty individual pump (6.7 mL)")
    print("  PALL            -> Prime ALL unprimed pumps")
    print("  EALL            -> Empty ALL primed pumps")
    print("  STATUS          -> Redisplay pump status")
    print("  DONE / EXIT     -> Proceed with execution\n")

    while True:
        cmd = input("Enter maintenance command (or DONE to proceed): ").strip().upper()

        if cmd in ["DONE", "EXIT", "Q", ""]:
            print("Exiting priming setup...\n")
            break

        elif cmd == "STATUS":
            display_pump_status(status)

        elif cmd == "PALL":
            pumps_to_prime = [p for p in ["A", "B", "C", "D"] if status[p] == "Unprimed"]
            if not pumps_to_prime:
                print("All pumps are already primed!")
            else:
                print(f"Priming pumps: {', '.join(pumps_to_prime)}...")
                threads = []
                for p in pumps_to_prime:
                    t = threading.Thread(target=start_pump, args=(p, 6.7), daemon=True)
                    t.start()
                    threads.append(t)
                    status[p] = "Primed"
                for t in threads:
                    t.join()
                save_pump_status(status)
                display_pump_status(status)

        elif cmd == "EALL":
            pumps_to_empty = [p for p in ["A", "B", "C", "D"] if status[p] == "Primed"]
            if not pumps_to_empty:
                print("All pumps are already unprimed!")
            else:
                print(f"Emptying pumps: {', '.join(pumps_to_empty)}...")
                threads = []
                for p in pumps_to_empty:
                    t = threading.Thread(target=start_pump, args=(f"R{p}", 6.7), daemon=True)
                    t.start()
                    threads.append(t)
                    status[p] = "Unprimed"
                for t in threads:
                    t.join()
                save_pump_status(status)
                display_pump_status(status)

        elif len(cmd) == 2 and cmd[0] in ["P", "E"] and cmd[1] in ["A", "B", "C", "D"]:
            action = cmd[0]
            pump = cmd[1]

            if action == "P":
                if status[pump] == "Primed":
                    print(f"Pump {pump} is ALREADY PRIMED! Action skipped.")
                else:
                    print(f"Priming Pump {pump} (6.7 mL)...")
                    start_pump(pump, 6.7)
                    status[pump] = "Primed"
                    save_pump_status(status)
                    display_pump_status(status)

            elif action == "E":
                if status[pump] == "Unprimed":
                    print(f"Pump {pump} is ALREADY EMPTY! Action skipped.")
                else:
                    print(f"Emptying Pump {pump} (6.7 mL)...")
                    start_pump(f"R{pump}", 6.7)
                    status[pump] = "Unprimed"
                    save_pump_status(status)
                    display_pump_status(status)
        else:
            print("Invalid command. Use PA-PD, EA-ED, PALL, EALL, STATUS, or DONE.")

# -----------------------------------------------------------------------------
# UR5e Pump Priming Functions
# -----------------------------------------------------------------------------

def prime_pump(pump, volume=6.7):
    """
    Primes one pump using the specified volume.

    The pump is marked as Primed only after the dispensing operation
    completes successfully.
    """

    status = load_pump_status()

    if status[pump] == "Primed":
        print(f"Pump {pump} is already primed.")
        return

    print(f"Priming Pump {pump}: {volume} mL")

    start_pump(pump, volume)

    status[pump] = "Primed"
    save_pump_status(status)

    print(f"Pump {pump} primed successfully.")


def empty_pump(pump, volume=6.7):
    """
    Empties one pump using reverse dispensing.

    The pump is marked as Unprimed only after the operation completes.
    """

    status = load_pump_status()

    if status[pump] == "Unprimed":
        print(f"Pump {pump} is already empty.")
        return

    print(f"Emptying Pump {pump}: {volume} mL")

    start_pump(f"R{pump}", volume)

    status[pump] = "Unprimed"
    save_pump_status(status)

    print(f"Pump {pump} emptied successfully.")


def prime_all_pumps(volume=6.7):
    """
    Primes all currently unprimed pumps simultaneously.
    """

    status = load_pump_status()

    pumps_to_prime = [
        pump for pump in ["A", "B", "C", "D"]
        if status[pump] == "Unprimed"
    ]

    if not pumps_to_prime:
        print("All pumps are already primed.")
        return

    print(f"Priming pumps: {', '.join(pumps_to_prime)}")

    operations = [
        {
            "pump": pump,
            "volume": volume,
            "mode": "continuous",
            "direction": "forward"
        }
        for pump in pumps_to_prime
    ]

    run_pumps_simultaneously(operations)

    for pump in pumps_to_prime:
        status[pump] = "Primed"

    save_pump_status(status)

    print("All selected pumps primed successfully.")


def empty_all_pumps(volume=6.7):
    """
    Empties all currently primed pumps simultaneously.
    """

    status = load_pump_status()

    pumps_to_empty = [
        pump for pump in ["A", "B", "C", "D"]
        if status[pump] == "Primed"
    ]

    if not pumps_to_empty:
        print("All pumps are already empty.")
        return

    print(f"Emptying pumps: {', '.join(pumps_to_empty)}")

    operations = [
        {
            "pump": pump,
            "volume": volume,
            "mode": "continuous",
            "direction": "reverse"
        }
        for pump in pumps_to_empty
    ]

    run_pumps_simultaneously(operations)

    for pump in pumps_to_empty:
        status[pump] = "Unprimed"

    save_pump_status(status)

    print("All selected pumps emptied successfully.")

# -----------------------------------------------------------------------------
# Starting the pump
# -----------------------------------------------------------------------------

def start_pump(command, volume):
    """
    Starts a pump operation and waits for the Arduino DONE message.

    If the serial connection is lost during dispensing:

        1. The elapsed pump time is calculated.
        2. The estimated dispensed volume is calculated using CAL.
        3. The remaining volume is calculated.
        4. The operation state is saved.
        5. The Arduino is reconnected.
        6. Only the remaining volume is dispensed.

    Example:

        Target volume = 5.0 mL
        Estimated dispensed = 3.0 mL
        Remaining volume = 2.0 mL

    The pump will therefore resume with approximately 2.0 mL.
    """

    # -------------------------------------------------------------------------
    # Determine pump and direction
    # -------------------------------------------------------------------------

    pump = command.removeprefix("R")

    direction = (
        -1 if command.startswith("R")
        else 1
    )

    # -------------------------------------------------------------------------
    # Check whether this is a recovery operation
    # -------------------------------------------------------------------------

    saved_state = load_operation_state()

    recovering = (
        saved_state.get("running", False)
        and saved_state.get("pump") == pump
        and saved_state.get("command") == command
    )

    if recovering:

        remaining_volume = saved_state.get(
            "remaining_volume",
            volume
        )

        print("\n" + "=" * 60)
        print("RECOVERING INTERRUPTED PUMP OPERATION")
        print("=" * 60)

        print(
            f"Pump: {pump}"
        )

        print(
            f"Original target: {volume:.3f} mL"
        )

        print(
            f"Estimated dispensed:  "
            f"{saved_state.get('estimated_dispensed', 0):.3f} mL"
        )

        print(
            f"Estimated remaining:  "
            f"{remaining_volume:.3f} mL"
        )

        print("=" * 60)

        # Nothing left to dispense
        if remaining_volume <= 0.001:

            print(
                "No significant volume remains."
            )

            mark_operation_complete()

            return

        volume = remaining_volume

    else:

        # ---------------------------------------------------------------------
        # New operation
        # ---------------------------------------------------------------------

        save_current_operation(
            pump=pump,
            command=command,
            volume=volume,
            direction=direction
        )

    # -------------------------------------------------------------------------
    # Attempt to perform the operation
    # -------------------------------------------------------------------------

    while True:

        # ---------------------------------------------------------------------
        # Make sure Arduino is connected
        # ---------------------------------------------------------------------

        if not serial_connected:

            wait_for_reconnection()

        # ---------------------------------------------------------------------
        # Clear stale DONE messages
        # ---------------------------------------------------------------------

        clear_done_queue(pump)

        # ---------------------------------------------------------------------
        # Record the start time of THIS dispensing section
        # ---------------------------------------------------------------------

        start_time = time.time()

        # ---------------------------------------------------------------------
        # Save the start time
        # ---------------------------------------------------------------------

        state = load_operation_state()

        state["start_time"] = start_time

        save_operation_state(state)

        # ---------------------------------------------------------------------
        # Create Arduino command
        # ---------------------------------------------------------------------

        serial_command = f"{command},{volume}"

        print(
            f"Sending: {serial_command}"
        )

        try:

            # -------------------------------------------------------------
            # Send command
            # -------------------------------------------------------------

            ser.write(
                (serial_command + "\n").encode()
            )

            # -------------------------------------------------------------
            # Record active pump
            # -------------------------------------------------------------

            active_pumps[pump] = {

                "start_time": start_time,

                "target_volume": volume,

                "direction": direction
            }

        except (
            serial.SerialException,
            OSError
        ):

            print(f"Failed to send command to Pump {pump}.")

            serial_connected = False

            active_pumps.pop(pump, None)

            wait_for_reconnection()

            # Retry the current remaining volume
            continue

        # ---------------------------------------------------------------------
        # Wait for Arduino completion
        # ---------------------------------------------------------------------

        completed = wait_until_done(pump)

        # ---------------------------------------------------------------------
        # Connection lost during dispensing
        # ---------------------------------------------------------------------

        if not completed:

            # -------------------------------------------------------------
            # Calculate how long this dispensing section ran
            # -------------------------------------------------------------

            elapsed_time = (
                time.time() - start_time
            )

            elapsed_ms = elapsed_time * 1000

            # -------------------------------------------------------------
            # Estimate volume dispensed during this section
            # -------------------------------------------------------------

            dispensed_this_section = (
                elapsed_ms * CAL[pump]
            )

            # -------------------------------------------------------------
            # Prevent estimate exceeding requested volume
            # -------------------------------------------------------------

            dispensed_this_section = min(
                dispensed_this_section,
                volume
            )

            # -------------------------------------------------------------
            # Calculate remaining volume
            # -------------------------------------------------------------

            remaining_volume = (
                volume - dispensed_this_section
            )

            # -------------------------------------------------------------
            # Get the original target volume
            # -------------------------------------------------------------

            state = load_operation_state()

            original_target = state.get("target_volume", volume)

            previous_dispensed = state.get("estimated_dispensed", 0.0)

            # -------------------------------------------------------------
            # Add this section's estimated volume
            # -------------------------------------------------------------

            total_dispensed = (previous_dispensed + dispensed_this_section)

            # Never exceed original target
            total_dispensed = min(total_dispensed, original_target)

            # -------------------------------------------------------------
            # Calculate remaining amount against the original target
            # -------------------------------------------------------------

            total_remaining = (original_target - total_dispensed)

            total_remaining = max(total_remaining, 0.0)

            # -------------------------------------------------------------
            # Save recovery information
            # -------------------------------------------------------------

            update_operation_progress(
                pump=pump,
                estimated_dispensed=total_dispensed,
                remaining_volume=total_remaining
            )

            # -------------------------------------------------------------
            # Remove pump from active list
            # -------------------------------------------------------------

            active_pumps.pop(pump,None)

            print("\n" + "=" * 60)

            print("PUMP CONNECTION LOST")

            print("=" * 60)

            print(
                f"Pump: {pump}"
            )

            print(
                f"Original target: "
                f"{original_target:.3f} mL"
            )

            print(
                f"Estimated dispensed: "
                f"{total_dispensed:.3f} mL"
            )

            print(
                f"Estimated remaining: "
                f"{total_remaining:.3f} mL"
            )

            print("=" * 60)

            # -------------------------------------------------------------
            # If essentially everything has been dispensed
            # -------------------------------------------------------------

            if total_remaining <= 0.001:

                print("Estimated target volume already reached.")

                mark_operation_complete()

                return

            # -------------------------------------------------------------
            # Wait for Arduino
            # -------------------------------------------------------------

            wait_for_reconnection()

            # -------------------------------------------------------------
            # Load the saved remaining volume
            # -------------------------------------------------------------

            state = load_operation_state()

            volume = state["remaining_volume"]

            print(
                f"Resuming Pump {pump} with "
                f"{volume:.3f} mL."
            )

            # Loop back and dispense the remaining amount
            continue

        # ---------------------------------------------------------------------
        # DONE received
        # ---------------------------------------------------------------------

        pump_info = active_pumps.pop(pump,None)

        if pump_info is None:

            return

        # ---------------------------------------------------------------------
        # Record successful transfer
        # ---------------------------------------------------------------------

        log_transfer(
            pump,
            volume * direction,
            completed=True
        )

        # ---------------------------------------------------------------------
        # Mark operation complete
        # ---------------------------------------------------------------------

        mark_operation_complete()

        print(f"Pump {pump} operation completed successfully.")

        return

# -----------------------------------------------------------------------------
# Waiting for the Arduino to report a successful transfer
# -----------------------------------------------------------------------------

def wait_until_done(pump):

    """
    Waits until the Arduino reports that the specified pump
    has finished.

    Returns:
        True  - pump completed normally
        False - connection was lost
    """

    while True:

        # -------------------------------------------------------------
        # Pump was stopped manually
        # -------------------------------------------------------------

        if pump not in active_pumps:

            return False

        # -------------------------------------------------------------
        # Connection has disappeared
        # -------------------------------------------------------------

        if not serial_connected:

            print(
                f"Connection lost while Pump {pump} "
                f"was operating."
            )

            return False

        try:

            # Wait for this pump's DONE message
            done_queues[pump].get(
                timeout=0.05
            )

            return True

        except queue.Empty:

            pass

# -----------------------------------------------------------------------------
# General pump operation for UR5e
# -----------------------------------------------------------------------------

def run_pump_operation(pump, volume, mode="continuous", direction="forward"):
    """
    Runs one pump operation.

    Args:
        pump: "A", "B", "C" or "D"
        volume: Volume in mL
        mode: "continuous" or "dropwise"
        direction: "forward" or "reverse"
    """

    # Create the Arduino command
    if direction == "reverse":
        command = "R" + pump
    elif direction == "forward":
        command = pump
    else:
        raise ValueError("Direction must be 'forward' or 'reverse'")

    # Select dispensing mode
    if mode == "continuous":
        start_pump(command, volume)

    elif mode == "dropwise":
        start_pump_dropwise(command, volume)

    else:
        raise ValueError("Mode must be 'continuous' or 'dropwise'")

# -----------------------------------------------------------------------------
# Simultaneous pump operations for UR5e
# -----------------------------------------------------------------------------

def run_pumps_simultaneously(operations):
    """
    Runs multiple pump operations simultaneously.
    Each operation should contain:
        pump
        volume
        mode
        direction

    Example:

        run_pumps_simultaneously([
            {
                "pump": "A",
                "volume": 5.0,
                "mode": "dropwise",
                "direction": "forward"
            },
            {
                "pump": "B",
                "volume": 3.0,
                "mode": "continuous",
                "direction": "reverse"
            }
        ])
    """

    threads = []

    for operation in operations:

        thread = threading.Thread(
            target=run_pump_operation,
            kwargs={
                "pump": operation["pump"],
                "volume": operation["volume"],
                "mode": operation.get("mode", "continuous"),
                "direction": operation.get("direction", "forward")
            }
        )

        threads.append(thread)
        thread.start()

    # Wait until ALL operations have finished
    for thread in threads:
        thread.join()


# -----------------------------------------------------------------------------
# Initialising the drop-wise dispensing
# -----------------------------------------------------------------------------

def start_pump_dropwise(command, total_volume):
    """
    Splits a requested volume into multiple 0.5 mL doses.
    A 30-second delay is inserted between each dose to achieve controlled dropwise dispensing (of an approximate rate of 1 mL/min).
    Dispensing can be interrupted at any time using the corresponding threading Event, 
    with the rate being customisable by varying the break interval time.
    """

    pump = command.removeprefix("R")
    dropwise_stop[pump].clear()

    full_doses = int(total_volume // 0.5) # Number of full 0.5 mL doses
    remainder = round(total_volume % 0.5, 3) # Final volume smaller than 0.5 mL to be dispensed last (in case the selected volume is not divisible by 0.5)

    # Dispensing one complete 0.5 mL dose during each iteration
    for i in range(full_doses):

        # Stop check; exits immediately if a stop request has been received
        if dropwise_stop[pump].is_set():
            return

        # Calling onto the dispension function using a set volume of 0.5 mL
        start_pump(command, 0.5)

        # Wait up to 30 seconds before the next dose
        # The wait ends early if a stop request is received
        if i < full_doses - 1 or remainder > 0:
            if dropwise_stop[pump].wait(30):
                return

    # Stop requested before the remainder
    if dropwise_stop[pump].is_set():
        return

    if remainder > 0:
        start_pump(command, remainder)

# -----------------------------------------------------------------------------
# Individual pump stop
# -----------------------------------------------------------------------------

def stop_pump(pump):
    """
    Stops the selected pump.
    If the pump was dispensing, the elapsed runtime is converted into an estimated transferred volume 
    using the pump calibration factor before logging the event.
    """

    dropwise_stop[pump].set() # Sets the stop event to prevent any further dropwise doses

    # If the pump is currently running, calculate the actual transferred volume
    if pump in active_pumps:

        # Tracking the time in ms for which the pump has been running
        elapsed_time = (time.time() - active_pumps[pump]["start_time"]) * 1000


        # Estimated transferred volume calculated using the runtime and calibration factors
        actual_volume = (elapsed_time * CAL[pump] * active_pumps[pump]["direction"])

        log_transfer(pump, actual_volume, completed=False)

        active_pumps.pop(pump, None) # Clearing the active pumps tracker


    # Sending a signal to Arduino to stop the pump
    ser.write(f"S{pump}\n".encode())

    return elapsed_time

# -----------------------------------------------------------------------------
# Overall pump stop
# -----------------------------------------------------------------------------

def stop_all_pumps():
    """
    Stops all currently active pumps, records their estimated transferred volumes, 
    cancels any active drop-wise dispensing operations and sends the global stop command to the Arduino.
    """

    current_time = time.time()

    # Loop through every running pump
    for pump in list(active_pumps.keys()):

        # Tracking the time in ms for which the pump has been running
        elapsed_time = (current_time - active_pumps[pump]["start_time"]) * 1000

        # Estimated transferred volume calculated using the runtime and calibration factors
        actual_volume = (elapsed_time * CAL[pump] * active_pumps[pump]["direction"])

        log_transfer(pump, actual_volume, completed=False)

    active_pumps.clear() # Clearing the active pumps tracker

    for event in dropwise_stop.values():
        event.set()
    # Sending stop command to Arduino
    ser.write(b"S\n")

# -----------------------------------------------------------------------------
# Communication clean-up
# -----------------------------------------------------------------------------
def clear_done_queue(pump):
    """Removes any old DONE messages for a pump."""

    while not done_queues[pump].empty():

        try:
            done_queues[pump].get_nowait()

        except queue.Empty:
            break

# -----------------------------------------------------------------------------
# Shutting down the controller
# -----------------------------------------------------------------------------

def close():
    """Stops all pumps before closing the serial connection, 
    ensuring that no dispensing operation is left running."""

    stop_all_pumps()
    ser.close()


# -----------------------------------------------------------------------------
# Connecting
# -----------------------------------------------------------------------------
# Uncomment when launching the stand-alone system
#pump_connect()