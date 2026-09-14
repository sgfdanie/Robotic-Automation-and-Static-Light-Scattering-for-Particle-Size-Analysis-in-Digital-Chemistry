# =============================================================================
# QUERY BUILDER PROGRAM
# =============================================================================
# Contains main functions responsible for the logic behind the query builder

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import threading
import time


# -----------------------------------------------------------------------------
# Query Runner
# -----------------------------------------------------------------------------
class QueryRunner:
    """
    Executes and manages scheduled sequences of pump, stirring, and heating 
    operations using background threads and coordinated timing.
    """

    def __init__(
        self,
        start_pump,
        start_pump_dropwise,
        stop_all_pumps,
        hotplate
    ):
        """
        Initializes the query runner with pump and hotplate control functions.

        Sets up query execution state, threading controls, action tracking,
        and timing information used during scheduled operations.
        """

        self.start_pump = start_pump
        self.start_pump_dropwise = start_pump_dropwise
        self.stop_all_pumps = stop_all_pumps
        self.hotplate = hotplate

        self.running = False
        self.stop_event = threading.Event()

        self.thread = None

        self.current_action = 0
        self.total_actions = 0

        self.query_start_time = None

    # -------------------------------------------------------------------------
    # Run Query
    # -------------------------------------------------------------------------
    def run_query(self, actions, global_stirring=None, global_heating=None):
        """
        Starts a configured query in a background thread.

        Validates the query configuration, initializes execution state, and
        launches the query scheduler to process actions sequentially while
        allowing operations within each action to run simultaneously.
        """

        print("========== RUN QUERY CALLED ==========")
        print("GLOBAL STIRRING:", global_stirring)
        print("GLOBAL HEATING:", global_heating)
        print("NUMBER OF ACTIONS:", len(actions))

        if self.running:

            print("!!! QUERY ALREADY RUNNING !!!")

            raise RuntimeError(
                "A query is already running."
            )

        if not actions:
            raise ValueError(
                "No actions have been added."
            )

        self.stop_event.clear()
        self.running = True
        self.current_action = 0
        self.total_actions = len(actions)
        self.query_start_time = time.time()

        self.thread = threading.Thread(
            target=self._run_query,
            args=(
                actions,
                global_stirring,
                global_heating
            ),
            daemon=True
        )

        self.thread.start()

        print("========== QUERY THREAD STARTED ==========")


    # -------------------------------------------------------------------------
    # Query Execution
    # -------------------------------------------------------------------------
    def _run_query(self, actions, global_stirring=None, global_heating=None):
        """
        Executes the query action sequence and coordinates operation timing.

        Applies delays between actions, manages global stirring and heating
        start/stop points, runs operations concurrently within each action,
        and waits for all operations to complete before continuing.
        """

        try:

            for index, action in enumerate(actions):

                if self.stop_event.is_set():
                    break

                self.current_action = index + 1
                action_number = index + 1

                # -------------------------------------------------------------
                # Delay before this action
                #
                # The previous action has already completely finished here
                # -------------------------------------------------------------
                if index > 0:

                    delay = actions[index - 1].get("delay", 0)

                    print(
                        f"[QUERY] Waiting {delay} seconds "
                        f"before action {action_number}"
                    )

                    if delay > 0:
                        if self.stop_event.wait(delay):
                            break

                # -------------------------------------------------------------
                # Global stirring START
                # -------------------------------------------------------------
                if (
                    global_stirring
                    and global_stirring.get("enabled", False)
                    and action_number == global_stirring.get("start_action")
                ):

                    speed = global_stirring.get("speed")

                    print(
                        f"[QUERY] Starting global stirring "
                        f"at Action {action_number}: "
                        f"{speed} RPM"
                    )

                    try:
                        self.hotplate.set_speed(speed)
                        self.hotplate.start_stirring()

                    except Exception as e:
                        print(f"[QUERY] Global stirring start error: {e}")

                # -------------------------------------------------------------
                # Global heating START
                # -------------------------------------------------------------
                if (
                    global_heating
                    and global_heating.get("enabled", False)
                    and action_number == global_heating.get("start_action")
                ):

                    temperature = global_heating.get("temperature")

                    print(
                        f"[QUERY] Starting global heating "
                        f"at Action {action_number}: "
                        f"{temperature} °C"
                    )

                    try:
                        self.hotplate.set_temperature(temperature)
                        self.hotplate.start_heating()

                    except Exception as e:
                        print(f"[QUERY] Global heating start error: {e}")


                # -------------------------------------------------------------
                # Start all operations in this action simultaneously
                # -------------------------------------------------------------
                operations = action.get("operations", [])
                operation_threads = []

                for operation in operations:

                    if self.stop_event.is_set():
                        break

                    thread = threading.Thread(
                        target=self._start_operation,
                        args=(operation,),
                        daemon=True
                    )

                    operation_threads.append(thread)
                    thread.start()


                # -------------------------------------------------------------
                # Wait for every operation in this action to finish
                # -------------------------------------------------------------

                for thread in operation_threads:

                    if self.stop_event.is_set():
                        break

                    thread.join()


                # -------------------------------------------------------------
                # Global stirring STOP
                #
                # This happens AFTER the action is completely finished
                # -------------------------------------------------------------
                if (
                    global_stirring
                    and global_stirring.get("enabled", False)
                    and action_number == global_stirring.get("stop_action")
                ):

                    print(
                        f"[QUERY] Stopping global stirring "
                        f"after Action {action_number}"
                    )

                    try:
                        self.hotplate.stop_stirring()

                    except Exception as e:
                        print(f"[QUERY] Global stirring stop error: {e}")

                # -------------------------------------------------------------
                # Global heating STOP
                #
                # This happens AFTER the action is completely finished
                # -------------------------------------------------------------
                if (
                    global_heating
                    and global_heating.get("enabled", False)
                    and action_number == global_heating.get("stop_action")
                ):

                    print(
                        f"[QUERY] Stopping global heating "
                        f"after Action {action_number}"
                    )

                    try:
                        self.hotplate.stop_heating()

                    except Exception as e:
                        print(f"[QUERY] Global heating stop error: {e}")

        except Exception as e:
            print(f"QUERY ERROR: {e}")


        finally:
            self.running = False
            self.current_action = 0
            self.query_start_time = None

    # -------------------------------------------------------------------------
    # Start Individual Operation
    # -------------------------------------------------------------------------
    def _start_operation(self, operation):
        """
        Executes a single pump, stirring, or heating operation.

        Configures the requested hardware parameters and starts continuous,
        timed, or drop-wise operation as specified by the query.
        """

        operation_type = operation.get("type")

        # ---------------------------------------------------------------------
        # Pump
        # ---------------------------------------------------------------------
        if operation_type == "pump":

            pump = operation.get("pump")
            volume = operation.get("volume")

            direction = operation.get(
                "direction",
                "forward"
            )

            mode = operation.get(
                "mode",
                "continuous"
            )

            if pump is None or volume is None:
                return

            command = (
                "R" + pump
                if direction == "reverse"
                else pump
            )

            if mode == "dropwise":
                self.start_pump_dropwise(
                    command,
                    volume
                )

            else:
                self.start_pump(
                    command,
                    volume
                )


        # ---------------------------------------------------------------------
        # Stirrer
        # ---------------------------------------------------------------------
        elif operation_type == "stirrer":

            speed = operation.get("speed")
            duration = operation.get("duration")

            if speed is None:
                return

            self.hotplate.set_speed(speed)

            if duration is not None and duration > 0:

                self.hotplate.start_timed_stirring(duration)

                # Wait until timed stirring has finished
                while True:

                    if self.stop_event.is_set():
                        return

                    remaining = (self.hotplate.get_stirring_remaining())

                    if remaining is None:
                        break

                    self.stop_event.wait(min(0.1, remaining))
            else:
                self.hotplate.start_stirring()

        # ---------------------------------------------------------------------
        # Heating
        # ---------------------------------------------------------------------
        elif operation_type == "heating":

            temperature = operation.get("temperature")
            duration = operation.get("duration")

            if temperature is None:
                return

            self.hotplate.set_temperature(temperature)

            if duration is not None and duration > 0:

                self.hotplate.start_timed_heating(duration)

                # Wait until timed heating has finished
                while True:

                    if self.stop_event.is_set():
                        return

                    remaining = (self.hotplate.get_heating_remaining())

                    if remaining is None:
                        break

                    self.stop_event.wait(min(0.1, remaining))

            else:
                self.hotplate.start_heating()


    # -------------------------------------------------------------------------
    # Stop Query
    # -------------------------------------------------------------------------
    def stop_query(self):
        """
        Stops the currently running query and all active hardware operations.

        Signals the query thread to stop and safely attempts to stop all pumps,
        stirring, and heating operations.
        """

        if not self.running:
            return

        self.stop_event.set()

        # ---------------------------------------------------------------------
        # Stop all pumps
        # ---------------------------------------------------------------------
        try:
            self.stop_all_pumps()

        except Exception as e:
            print(f"QUERY pump stop error: {e}")

        # ---------------------------------------------------------------------
        # Stop stirring
        # ---------------------------------------------------------------------
        try:
            self.hotplate.stop_stirring()

        except Exception as e:
            print(f"QUERY stirring stop error: {e}")

        # ---------------------------------------------------------------------
        # Stop heating
        # ---------------------------------------------------------------------
        try:
            self.hotplate.stop_heating()

        except Exception as e:
            print(f"QUERY heating stop error: {e}")

        self.running = False

    # -------------------------------------------------------------------------
    # Query Status
    # -------------------------------------------------------------------------
    def get_status(self):
        """
        Returns the current execution status of the query.

        Reports whether the query is running, the current and total action
        counts, and the elapsed execution time.
        """

        if not self.running:
            return {
                "running": False,
                "current_action": 0,
                "total_actions": self.total_actions
            }

        elapsed = 0

        if self.query_start_time is not None:

            elapsed = (time.time() - self.query_start_time)


        return {
            "running": True,
            "current_action": self.current_action,
            "total_actions": self.total_actions,
            "elapsed": elapsed
        }