# Robotic Automation and Static Light Scattering for Particle Size Analysis in Digital Chemistry

## Liquid-Handling System

This repository contains the Python software for a four-channel liquid-handling system and the Arduino firmware used to control its pumps. It forms part of a wider project exploring robotic automation and static light scattering for particle-size analysis in digital chemistry.

The liquid-handling platform is intended to automate liquid dispensing and support repeatable sample-preparation workflows. The Python application provides a graphical interface and workflow/query-building functionality, while an Arduino Uno controls four peristaltic pumps through a four-channel motor driver.

> **Development status:** Review the firmware, configure the hardware, validate pump calibration, and test stop/shutdown behaviour before experimental use. The supplied Arduino sketch has compile-time issues noted below that must be resolved before uploading.

## Hardware

The system is described as comprising:

- **Arduino Uno** — microcontroller for pump control.
- **Four peristaltic pumps** — channels A–D for liquid dispensing.
- **Grove Base Shield** — interface shield for compatible modules.
- **DRI0039 four-channel motor driver** — drives the pump motors.
- **16 × 2 I²C LCD** — displays active pump letters and system-ready status.
- **Computer and USB/serial connection** — runs the Python software and communicates with the Arduino.
- **IKA hotplate/stirrer (optional)** — controlled by a separate Python module when used.
- **UR5e robot and camera (integration work)** — referenced in a template, not a complete verified integration.

Check the motor driver's voltage/current requirements and wiring against the actual hardware. Do not assume that the Grove shield, driver, pumps, or power supply can be connected without checking their electrical compatibility.

## Software Contents

| File | Purpose |
|---|---|
| `pump_main_GUI.py` | Main Plotly Dash graphical interface. |
| `pyserial_main_code.py` | Pump-control functions, serial communication, dispensing logic, calibration values, and logging. |
| `query_builder.py` | Logic for coordinating sequences of operations. |
| `query_builder_GUI.py` | GUI components for configuring operation sequences. |
| `IKA_hotplate.py` | Serial communication and control functions for an IKA hotplate/stirrer. |
| `GUI_styles.py` | Shared GUI styling. |
| `UR5e_integration_template.py` | Starting point for a UR5e/camera workflow; verify its dependencies before use. |
| `Pump_arduno_code.ino` | Receives serial commands, controls pump direction/PWM, times pump runs, and updates the LCD. |


## Requirements

### Python

Python 3.10 or later. The direct external Python packages identified in the supplied files are Dash and PySerial.

Install them from the project directory:

```bash
python -m pip install -r requirements.txt
```

### Arduino IDE and Library

- Arduino IDE with Arduino Uno board support.
- A `LiquidCrystal_I2C` library compatible with the sketch.
- `Wire`, which is included with the Arduino platform.

The sketch configures a 16-column, 2-row I²C LCD at address `0x27`. Change the address if the actual LCD backpack uses a different one.

## Installation and Setup

### 1. Get the Code

```bash
git clone https://github.com/sgfdanie/Robotic-Automation-and-Static-Light-Scattering-for-Particle-Size-Analysis-in-Digital-Chemistry.git
cd Robotic-Automation-and-Static-Light-Scattering-for-Particle-Size-Analysis-in-Digital-Chemistry
git checkout Liquid-handling-system-code
```

### 2. Set Up Python

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Prepare the Arduino

1. Save the firmware as an `.ino` sketch.
2. Install a compatible `LiquidCrystal_I2C` library through the Arduino IDE Library Manager.
3. Select Arduino Uno and the correct serial port.
4. Verify the motor-driver wiring and pin assignments below.
5. Resolve the compile-time issues in **Known Issues and Checks**.
6. Compile and upload only after checking the wiring, power requirements, and safe operating conditions.

### 4. Configure Serial Communication

The supplied Python pump-control code uses serial port `COM5` and baud rate `9600`. Change the port setting to match the computer. The Arduino sketch also uses `Serial.begin(9600)`, so both ends must use the same baud rate.

Close the Arduino Serial Monitor before starting Python if it occupies the same serial port.

### 5. Start the Python Interface

The main interface is defined in `pump_main_GUI.py`. In the supplied snapshot, the application startup block is commented out. Review the startup, hardware initialisation, and shutdown logic, then enable or add an appropriate entry point before running it.

The typical local Dash address is `http://127.0.0.1:8050`, but it will be available only after the application starts successfully.

## Arduino Pump Control

### Pin Assignments

| Pump | PWM pin | Direction pin |
|---|---:|---:|
| A / Motor 1 | D3 | D4 |
| B / Motor 2 | D11 | D12 |
| C / Motor 3 | D5 | D8 |
| D / Motor 4 | D6 | D7 |

Verify these assignments against the actual driver and wiring before powering the system.

### Serial Command Protocol

The sketch reads newline-terminated commands at 9600 baud and converts commands to uppercase.

| Command | Intended action |
|---|---|
| `A,5` | Run pump A forward for a nominal 5 mL. |
| `B,10` | Run pump B forward for a nominal 10 mL. |
| `C,2.5` | Run pump C forward for a nominal 2.5 mL. |
| `RA,5` | Run pump A in reverse for the calculated run time. |
| `RB,10` | Run pump B in reverse for the calculated run time. |
| `S` | Stop all pumps. |
| `SA`, `SB`, `SC`, `SD` | Stop the selected pump. |

Commands must end with a newline (`\n`). The sketch starts pumps at PWM 255 by default and estimates runtime from a calibration factor.

When a timed pump run finishes, the Arduino sends a message such as `DONE,A`. The LCD displays the letters of pumps marked as running and shows `Running...`; when none are running, it shows `System Ready`.

## Pump Calibration

The supplied Arduino sketch defines these water calibration factors, described in the code as mL per millisecond:

| Pump | Calibration factor |
|---|---:|
| A | 0.00119895 |
| B | 0.00125173 |
| C | 0.00124938 |
| D | 0.00128198 |

The firmware estimates run time as:

```text
run time (ms) = requested volume (mL) / calibration factor (mL/ms)
```

Treat these as starting values, not guaranteed accuracy. Recalibrate each pump with the intended liquid, tubing, speed, and setup. Record the method and results. If Python also calculates pump run times, check that its calibration values and units are consistent with the Arduino firmware.

## Typical Operating Procedure

1. Inspect wiring, tubing, reservoirs, waste vessel, and power supplies.
2. Confirm the firmware compiles and is uploaded, and verify the serial port and baud rate.
3. Test one pump at a time with a small volume of a suitable test liquid.
4. Verify flow direction, delivered volume, completion messages, and individual/all-pump stop commands.
5. Configure the intended sequence in the GUI/query builder only after individual functions have been tested.
6. Monitor initial runs, review logs, and shut down pumps and other equipment safely.

Do not run unattended experiments until safe stopping, error handling, calibration, and the full workflow have been validated.

## Known Issues and Checks

- **LCD library compatibility:** Confirm the installed `LiquidCrystal_I2C` library supports `lcd.init()`. Library variants differ.
- **Serial port:** `COM5` is hard-coded in the supplied Python pump-control code; update it for the target computer.
- **Hardware validation:** Verify motor-driver wiring, power/current limits, direction logic, and safe-stop behaviour on the actual system.
- **Calibration:** Validate every pump under actual operating conditions.
- **UR5e template:** The template references `camera.py`; ensure the module and required robot environment are available before using it.
- **Dependencies and testing:** `requirements.txt` lists the direct external Python packages identified in the supplied files. A pinned, tested environment and automated test suite are not currently provided.

## Safety

This software controls physical laboratory equipment. Incorrect wiring, unsuitable power supplies, leaks, unexpected pump direction, or incorrect run times can damage equipment or create hazards. Test in a controlled environment, keep appropriate emergency-stop procedures available, and do not leave heating or dispensing operations unattended unless the complete setup has been assessed for safe autonomous operation.

## Project Context

This liquid-handling system is one part of the wider project on robotic automation and static light scattering for particle-size analysis in digital chemistry. The files described here focus on liquid handling and equipment coordination; they do not alone demonstrate a complete static-light-scattering measurement or particle-size calculation pipeline.

## Repository

[Robotic Automation and Static Light Scattering for Particle Size Analysis in Digital Chemistry](https://github.com/sgfdanie/Robotic-Automation-and-Static-Light-Scattering-for-Particle-Size-Analysis-in-Digital-Chemistry)
