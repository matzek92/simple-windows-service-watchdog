# simple-windows-service-watchdog

A simple Python program to run as Windows task that checks a list of services and starts them if they are not running.

## Features

- Monitors multiple Windows services
- Automatically starts stopped services
- Uses `sji` package for configuration and logging
- Minimal boilerplate code
- Easy to configure via INI file
- Comprehensive logging of all actions

## Requirements

- Python 3.6 or higher
- Windows operating system
- Administrator privileges (required to manage Windows services)

## Installation

1. Clone this repository or download the files
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration file:
   ```bash
   copy service_watchdog.config.ini.example service_watchdog.config.ini
   ```

2. Edit `service_watchdog.config.ini` and specify the services you want to monitor.
   You can list explicit service names and/or prefixes to auto-include matching services:
   ```ini
   [services]
   services_to_monitor = Spooler, wuauserv
   service_prefixes = MSSQL, MySvc-
   ```
   The script enumerates local services and adds any whose service name starts with
   one of the values in `service_prefixes` (case-insensitive). The `services_to_monitor`
   option is required; if it is missing, the program exits with code 1.

## Usage

### Manual Execution

Run the script manually (requires Administrator privileges):

```bash
python service_watchdog.py
```

### Windows Task Scheduler

To run this script automatically as a scheduled task:

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Task" (not "Create Basic Task")
3. In the "General" tab:
   - Name: "Service Watchdog"
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges"
4. In the "Triggers" tab:
   - Click "New"
   - Set the schedule (e.g., "On a schedule" - Daily, every 1 hour)
5. In the "Actions" tab:
   - Click "New"
   - Action: "Start a program"
   - Program/script: `python.exe` (or full path: `C:\Python312\python.exe`)
   - Add arguments: `service_watchdog.py`
   - Start in: `C:\path\to\simple-windows-service-watchdog`
6. Configure other settings as needed and click "OK"

## Logging

The script uses the `sji` package for logging. Logs are written to the console and can be redirected to a file if needed. The logger provides detailed information about:

- Service status checks
- Services that are already running
- Services that need to be started
- Any errors encountered

## Example Output

```
============================================================
Starting Windows Service Watchdog
Version: 1a2b3c4d-dirty
============================================================
Monitoring 2 service(s): Spooler, wuauserv
Checking service: Spooler
Service Spooler is already running
Checking service: wuauserv
Service wuauserv is not running (status: STOPPED)
Starting service: wuauserv
Service wuauserv started successfully
============================================================
Windows Service Watchdog completed successfully
============================================================
```

## Exit Codes

- 0: Success (all services were already running or were started)
- 1: Error (missing/invalid config, no services configured, or some services failed to start)

## License

MIT License - See LICENSE file for details 
