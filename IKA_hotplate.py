# =============================================================================
#
# IKA STIRRER/HOTPLATE INTEGRATION
#
# =============================================================================
# Resposnible for the stirrer operations
# Used by calling on its functions in separate files, including the GUI.

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import serial
import serial.tools.list_ports
import sys
import time
import threading


# -----------------------------------------------------------------------------
# Find IKA hotplate port
# -----------------------------------------------------------------------------

def find_hotplate_port():
    """
    Searches for the serial port used by the IKA hotplate.

    Returns:
        The detected serial port, e.g. "COM4".
    """

    ports = serial.tools.list_ports.comports()

    for port in ports:

        # Windows -------------------------------------------------------------

        if sys.platform.startswith("win"):

            if port.device.startswith("COM"):

                if (
                    "IKA" in port.description
                    or "USB" in port.description
                ):

                    print(
                        f"Found IKA device on "
                        f"{port.device} "
                        f"({port.description})"
                    )

                    return port.device


        # Linux ----------------------------------------------------------------

        elif sys.platform.startswith("linux"):

            if (
                port.device.startswith("/dev/ttyUSB")
                or
                port.device.startswith("/dev/ttyACM")
            ):

                print(
                    f"Found IKA device on "
                    f"{port.device} "
                    f"({port.description})"
                )

                return port.device


        # macOS ----------------------------------------------------------------

        elif sys.platform.startswith("darwin"):

            if (
                port.device.startswith("/dev/tty.")
                or
                port.device.startswith("/dev/cu.")
            ):

                if (
                    "USB" in port.description
                    or
                    "IKA" in port.description
                ):

                    print(
                        f"Found IKA device on "
                        f"{port.device} "
                        f"({port.description})"
                    )

                    return port.device


    raise IOError(
        "No IKA hotplate serial port found! "
        "Please check connection."
    )

# -----------------------------------------------------------------------------
# IKA Hotplate Class
# -----------------------------------------------------------------------------
class IKAHotplate:
    """
    Controller for an IKA RCT basic hotplate/stirrer.

    Communication:
        9600 baud
        7 data bits
        Even parity
        1 stop bit
        No flow control
    """

    def __init__(self, port):

        self.port = port
        self.ser = None

        # ---------------------------------------------------------------------
        # Timer control
        # ---------------------------------------------------------------------

        # Events allow a timed operation to be cancelled manually.

        self.stirring_timer_stop = threading.Event()
        self.heating_timer_stop = threading.Event()

        # Store the end time of each timed operation.

        self.stirring_end_time = None
        self.heating_end_time = None

        # ---------------------------------------------------------------------
        # Serial communication lock
        # ---------------------------------------------------------------------
        # The GUI reads the hotplate every second while other commands may also be sent. This prevents two commands using the serial port simultaneously.

        self.serial_lock = threading.Lock()

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------
    def connect(self):
        """Connects to the IKA hotplate."""

        if (self.ser is not None
            and
            self.ser.is_open
        ):

            print("IKA hotplate is already connected.")

            return

        print(
            f"Connecting to IKA RCT basic "
            f"on {self.port}..."
        )

        self.ser = serial.Serial(
            port=self.port,
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=2
        )

        # Give the connection a moment to initialise
        time.sleep(0.5)
        print("IKA hotplate connected.")

    # -------------------------------------------------------------------------
    # Communication
    # -------------------------------------------------------------------------
    def send_command(self, command):
        """
        Sends a command to the IKA and returns its response.
        IKA commands are terminated using CR/LF.
        """

        if (
            self.ser is None
            or
            not self.ser.is_open
        ):

            raise ConnectionError("IKA hotplate is not connected.")


        # Only allow one thread to communicate with the IKA at a time.
        with self.serial_lock:

            # Clear any old data waiting in the receive buffer
            self.ser.reset_input_buffer()


            # Add CR/LF required by the IKA protocol
            message = command + "\r\n"


            print(f"IKA - {command}")

            self.ser.write(message.encode("ascii"))


            # Read the response
            response = (
                self.ser.readline().decode("ascii", errors="replace").strip()
            )

            print(f"IKA - {response}")

            return response

    # -------------------------------------------------------------------------
    # Response handling
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_value(response):
        """
        Extracts the numerical value from an IKA response.
        Example:
            "30.0 2" - 30.0
            "300.0 4" - 300.0
        """

        if not response:
            return None

        try:
            return float(response.split()[0])

        except (
            ValueError,
            IndexError
        ):

            return None

    # -------------------------------------------------------------------------
    # Temperature
    # -------------------------------------------------------------------------
    def set_temperature(self, temperature):
        """
        Sets the desired hotplate temperature in °C.
        """

        return self.send_command(f"OUT_SP_1 {temperature}")


    def get_temperature(self):
        """
        Returns the current measured temperature in °C.
        """

        response = self.send_command("IN_PV_2")

        return self.extract_value(response)


    def get_set_temperature(self):
        """
        Returns the current temperature setpoint in °C.
        """

        response = self.send_command("IN_SP_1")

        return self.extract_value(response)


    def start_heating(self):
        """
        Starts continuous heating.
        Any existing timed heating operation is cancelled.
        """

        self.heating_timer_stop.set()
        self.heating_end_time = None

        return self.send_command("START_1")


    def stop_heating(self):
        """
        Stops heating and cancels any active timed heating operation.
        """

        self.heating_timer_stop.set()
        self.heating_end_time = None

        return self.send_command("STOP_1")

    # -------------------------------------------------------------------------
    # Timed Heating
    # -------------------------------------------------------------------------

    def start_timed_heating(self, duration):
        """
        Starts heating for a specified number of seconds.
        """

        if duration <= 0:

            raise ValueError("Heating time must be greater than 0 seconds.")

        # Cancel any previous timer
        self.heating_timer_stop.set()

        # Create a new event
        self.heating_timer_stop = (threading.Event())

        # Calculate when heating should finish
        self.heating_end_time = (time.time() + duration)

        # Start heating
        self.send_command("START_1")

        # Run timer in background
        threading.Thread(

            target=self._heating_timer,
            daemon=True

        ).start()


    def _heating_timer(self):
        """
        Background thread responsible for timed heating.
        """

        while True:

            # Check whether the timer was manually cancelled
            if self.heating_timer_stop.is_set():
                return

            # Calculate remaining time
            remaining = (self.heating_end_time - time.time())

            # Timer finished
            if remaining <= 0:
                break


            # Check again frequently
            self.heating_timer_stop.wait(min(0.1, remaining))


        # Make sure the timer was not cancelled
        if not self.heating_timer_stop.is_set():
            try:
                self.send_command("STOP_1")

            finally:
                self.heating_end_time = None


    def get_heating_remaining(self):
        """
        Returns the remaining time for timed heating.
        """

        if self.heating_end_time is None:
            return None

        remaining = (self.heating_end_time - time.time())

        if remaining <= 0:
            return None

        return remaining

    # -------------------------------------------------------------------------
    # Stirring
    # -------------------------------------------------------------------------

    def set_speed(self, rpm):
        """
        Sets the desired stirring speed in rpm.
        The IKA RCT basic has a minimum practical speed of 50 rpm.
        """

        return self.send_command(f"OUT_SP_4 {rpm}")


    def get_speed(self):
        """
        Returns the current measured stirring speed in rpm.
        """

        response = self.send_command("IN_PV_4")

        return self.extract_value(response)


    def get_set_speed(self):
        """
        Returns the current stirring speed setpoint in rpm.
        """

        response = self.send_command("IN_SP_4")

        return self.extract_value(response)


    def start_stirring(self):
        """
        Starts continuous stirring.
        Any existing timed stirring operation is cancelled.
        """

        self.stirring_timer_stop.set()
        self.stirring_end_time = None

        return self.send_command("START_4")


    def stop_stirring(self):
        """
        Stops stirring and cancels any active timed stirring operation.
        """

        self.stirring_timer_stop.set()
        self.stirring_end_time = None

        return self.send_command("STOP_4")


    # -------------------------------------------------------------------------
    # Timed Stirring
    # -------------------------------------------------------------------------

    def start_timed_stirring(self, duration):
        """
        Starts stirring for a specified number of seconds.
        """

        if duration <= 0:
            raise ValueError("Stirring time must be greater than 0 seconds.")


        # Cancel any previous timer
        self.stirring_timer_stop.set()


        # Create a new event
        self.stirring_timer_stop = (threading.Event())


        # Calculate when stirring should finish
        self.stirring_end_time = (time.time() + duration)


        # Start stirring
        self.send_command("START_4")


        # Run timer in background
        threading.Thread(
            target=self._stirring_timer,
            daemon=True

        ).start()


    def _stirring_timer(self):
        """
        Background thread responsible for timed stirring.
        """

        while True:

            # Check whether the timer was manually cancelled
            if self.stirring_timer_stop.is_set():
                return


            # Calculate remaining time
            remaining = (self.stirring_end_time - time.time())


            # Timer finished
            if remaining <= 0:
                break


            # Check again frequently
            self.stirring_timer_stop.wait(min(0.1, remaining))


        # Make sure the timer was not cancelled
        if not self.stirring_timer_stop.is_set():

            try:
                self.send_command("STOP_4")

            finally:
                self.stirring_end_time = None


    def get_stirring_remaining(self):
        """
        Returns the remaining time for timed stirring.
        """

        if self.stirring_end_time is None:
            return None

        remaining = (self.stirring_end_time - time.time())

        if remaining <= 0:
            return None

        return remaining

    # -------------------------------------------------------------------------
    # Reset
    # -------------------------------------------------------------------------

    def reset(self):
        """
        Resets the IKA to its normal operating state.
        """

        # Cancel timers
        self.stirring_timer_stop.set()
        self.heating_timer_stop.set()
        self.stirring_end_time = None
        self.heating_end_time = None

        return self.send_command("RESET")

    # -------------------------------------------------------------------------
    # Disconnect
    # -------------------------------------------------------------------------
    def disconnect(self):
        """
        Closes the serial connection to the IKA.
        """

        # Cancel any active timers
        self.stirring_timer_stop.set()
        self.heating_timer_stop.set()
        self.stirring_end_time = None
        self.heating_end_time = None


        if (self.ser is not None and self.ser.is_open):
            self.ser.close()

            print("IKA hotplate disconnected.")


# -----------------------------------------------------------------------------
# Standalone Test
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # Make sure to assign the correct port
    hotplate = IKAHotplate("COM4")


    try:

        # Connect
        hotplate.connect()


        # Read current values
        temperature = (hotplate.get_temperature())

        speed = (hotplate.get_speed())

        print()

        print(
            f"Current temperature: "
            f"{temperature} °C"
        )

        print(
            f"Current stirring speed: "
            f"{speed} rpm"
        )


        # Read current setpoints
        temperature_setpoint = (hotplate.get_set_temperature())
        speed_setpoint = (hotplate.get_set_speed())

        print()

        print(
            f"Temperature setpoint: "
            f"{temperature_setpoint} °C"
        )

        print(
            f"Stirring speed setpoint: "
            f"{speed_setpoint} rpm"
        )

    except Exception as e:

        print(f"ERROR: {e}")

    finally:

        # Always disconnect when the program ends
        hotplate.disconnect()