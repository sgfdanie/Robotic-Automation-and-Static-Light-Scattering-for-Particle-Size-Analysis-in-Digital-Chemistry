# =============================================================================
#
# UR5e PUMP INTEGRATION TEMPLATE
#
# =============================================================================
import time
import threading

from pyserial_main_code_v2 import (
    pump_connect,
    prime_pump,
    empty_pump,
    prime_all_pumps,
    empty_all_pumps,
    run_pump_operation,
    run_pumps_simultaneously,
    stop_pump,
    stop_all_pumps,
    close,
    serial_connection_monitor,
    recover_previous_operation
)

from camera import (
    open_camera,
    show_camera,
    take_snapshot,
    start_recording,
    stop_recording
)

from IKA_hotplate import (
    IKAHotplate,
    find_hotplate_port
)

# =============================================================================
# CONNECT TO PUMPS AND STIRRER
# =============================================================================

if not pump_connect():

    raise RuntimeError(
        "Unable to connect to pump controller."
    )


# Start background connection monitor
threading.Thread(
    target=serial_connection_monitor,
    daemon=True
).start()


# Recover an interrupted pump operation, if one exists --> Comment out if want to start from blank after crash
recover_previous_operation()


# Connect to IKA hotplate
hotplate = IKAHotplate(
    find_hotplate_port()
)

hotplate.connect()

try:

    # =========================================================================
    # RECORDIG START
    # =========================================================================
    # Open camera
    camera = open_camera()

    recording = start_recording(
    camera,
    filename="experiment_001.mp4"
    )

    # =========================================================================
    # PUMP PRIMING
    # =========================================================================

    # Prime one specific pump
    prime_pump("A")

    # Prime another pump
    prime_pump("B")

    # Prime all pumps - primes all the pumps that are NOT currently primed
    prime_all_pumps()

    # Empty one specific pump
    empty_pump("A")

    # Empty all pumps - empties all pumps that are NOT currently empty
    empty_all_pumps()


    # =========================================================================
    # EXAMPLE ROBOT OPERATION
    # =========================================================================

    # Robot movement command HERE

    print("Robot moving to first position...")


    print("Robot is in position.")


    # =========================================================================
    # 1. CONTINUOUS FORWARD
    # =========================================================================

    print("Dispensing 5 mL from Pump A.")

    run_pump_operation(
        pump="A",
        volume=5.0,
        mode="continuous",
        direction="forward"
    )

    print("Pump A finished.")

    # =========================================================================
    # START STIRRING
    # =========================================================================
    hotplate.set_speed(300) # Set stirrnig speed
    hotplate.start_stirring() # Start stirring

    # =========================================================================
    # ROBOT OPERATION
    # =========================================================================

    print("Robot performing next operation...")

    # Robot movement command HERE

    time.sleep(1)


    # =========================================================================
    # 2. CONTINUOUS REVERSE
    # =========================================================================

    print("Reverse dispensing 2 mL from Pump B.")

    run_pump_operation(
        pump="B",
        volume=2.0,
        mode="continuous",
        direction="reverse"
    )

    print("Pump B finished.")


    # =========================================================================
    # ROBOT OPERATION
    # =========================================================================

    

    # =========================================================================
    # 3. DROP-WISE FORWARD
    # =========================================================================

    print("Drop-wise dispensing 3 mL from Pump A.")

    run_pump_operation(
        pump="A",
        volume=3.0,
        mode="dropwise",
        direction="forward"
    )

    print("Pump A drop-wise operation finished.")


    # =========================================================================
    # 4. DROP-WISE REVERSE
    # =========================================================================

    print("Drop-wise reverse dispensing 2 mL from Pump B.")

    run_pump_operation(
        pump="B",
        volume=2.0,
        mode="dropwise",
        direction="reverse"
    )

    print("Pump B drop-wise reverse operation finished.")


    # =========================================================================
    # 5. TWO PUMPS SIMULTANEOUSLY
    # =========================================================================

    print("Starting A and B simultaneously.")

    run_pumps_simultaneously([

        {
            "pump": "A",
            "volume": 5.0,
            "mode": "continuous",
            "direction": "forward"
        },

        {
            "pump": "B",
            "volume": 5.0,
            "mode": "continuous",
            "direction": "forward"
        }

    ])

    print("Both pumps finished.")


    # =========================================================================
    # 6. MIXED MODES SIMULTANEOUSLY
    # =========================================================================

    print("Starting mixed A/B operation.")

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

    print("Mixed A/B operation finished.")


    # =========================================================================
    # 7. THREE PUMPS SIMULTANEOUSLY
    # =========================================================================

    print("Starting three-pump operation.")

    run_pumps_simultaneously([

        {
            "pump": "A",
            "volume": 5.0,
            "mode": "continuous",
            "direction": "forward"
        },

        {
            "pump": "B",
            "volume": 2.0,
            "mode": "dropwise",
            "direction": "forward"
        },

        {
            "pump": "C",
            "volume": 4.0,
            "mode": "continuous",
            "direction": "reverse"
        }

    ])

    print("Three-pump operation finished.")


    # =========================================================================
    # ROBOT CONTINUES
    # =========================================================================

    print("All dispensing complete. Robot continuing.")

    # Robot movement command HERE



except KeyboardInterrupt:

    print("\nEmergency stop requested.")

    stop_all_pumps()


except Exception as e:

    print(f"\nERROR: {e}")

    # Stop pumps if anything goes wrong
    stop_all_pumps()

    # Re-raise the error so you can see what happened
    raise


finally:
    # ------------------------------------------------------------
    # END WORKFLOW RECORDING
    # ------------------------------------------------------------
    
    stop_recording(recording)
    
    
    # Close camera
    camera.release()

    # Always close the pump controller
    close()

    print("Pump controller closed.")