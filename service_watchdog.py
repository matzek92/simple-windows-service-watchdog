#!/usr/bin/env python3
"""
Windows Service Watchdog

A simple script to monitor Windows services and start them if they are not running.
Uses the sji package for configuration and logging management.
"""

import sys
import win32service
import win32serviceutil
import sji


def get_service_status(service_name):
    """
    Get the status of a Windows service.

    Args:
        service_name: Name of the service to check

    Returns:
        Service status constant or None if service doesn't exist
    """
    try:
        status = win32serviceutil.QueryServiceStatus(service_name)
        return status[1]
    except Exception:
        # Service doesn't exist, access denied, or other error
        # Returning None to indicate failure - caller will log appropriate message
        return None


def start_service(service_name, logger):
    """
    Start a Windows service.

    Args:
        service_name: Name of the service to start
        logger: Logger instance for logging

    Returns:
        True if service was started successfully, False otherwise
    """
    try:
        logger.info(f"Starting service: {service_name}")
        win32serviceutil.StartService(service_name)
        logger.info(f"Service {service_name} started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start service {service_name}: {e}")
        return False


def check_and_start_services(services, logger):
    """
    Check status of services and start them if they are not running.

    Args:
        services: List of service names to monitor
        logger: Logger instance for logging
    """

    all_running = True
    for service_name in services:
        service_name = service_name.strip()
        if not service_name:
            continue

        logger.info(f"Checking service: {service_name}")

        status = get_service_status(service_name)

        if status is None:
            logger.error(f"Service {service_name} does not exist or cannot be accessed")
            continue

        if status == win32service.SERVICE_RUNNING:
            logger.info(f"Service {service_name} is already running")
        else:
            status_name = {
                win32service.SERVICE_STOPPED: "STOPPED",
                win32service.SERVICE_START_PENDING: "START_PENDING",
                win32service.SERVICE_STOP_PENDING: "STOP_PENDING",
                win32service.SERVICE_RUNNING: "RUNNING",
                win32service.SERVICE_CONTINUE_PENDING: "CONTINUE_PENDING",
                win32service.SERVICE_PAUSE_PENDING: "PAUSE_PENDING",
                win32service.SERVICE_PAUSED: "PAUSED"
            }.get(status, f"UNKNOWN({status})")

            logger.warning(f"Service {service_name} is not running (status: {status_name})")
            
            if status == win32service.SERVICE_STOPPED:
                logger.warning(f"Service {service_name} is stopped, trying to start it")
                result = start_service(service_name, logger)
                if not result:
                    logger.error(f"Failed to start service {service_name}")
                    all_running = False
            else:
                logger.error(f"Service {service_name} is in an unknown state ({status_name})")
                all_running = False

    return all_running


def find_services_with_prefixes(prefixes, logger):
    """
    Enumerate local Windows services and return those whose service name starts with any given prefix.

    Args:
        prefixes: List of prefixes to match (case-insensitive)
        logger: Logger for diagnostic output

    Returns:
        List of matching service names
    """
    try:
        scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
        try:
            # Returns list of tuples: (service_name, display_name, service_status)
            listed = win32service.EnumServicesStatus(
                scm,
                win32service.SERVICE_WIN32,
                win32service.SERVICE_STATE_ALL,
            )
        finally:
            win32service.CloseServiceHandle(scm)
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise e

    normalized_prefixes = [p.lower() for p in prefixes if p]
    matched_names = []
    for service_name, _display_name, _status in listed:
        name_lc = service_name.lower()
        if any(name_lc.startswith(p) for p in normalized_prefixes):
            matched_names.append(service_name)

    return matched_names


def main():
    """Main function to run the service watchdog."""
    # Initialize with sji
    job_init = sji.SimpleJobInit(__file__)
    logger = job_init.logger
    config = job_init.config

    logger.info("=" * 60)
    logger.info("Starting Windows Service Watchdog")
    logger.info(f"Script Version: {job_init.get_job_script_version()}")
    logger.info(f"Config File Version: {job_init.get_config_file_version()}")
    logger.info("=" * 60)

    # Read services from config
    if not config.has_section('services'):
        logger.error("Config file is missing [services] section")
        sys.exit(1)

    if not config.has_option('services', 'services_to_monitor'):
        logger.error("Config file is missing 'services_to_monitor' option in [services] section")
        sys.exit(1)

    services_str = config.get('services', 'services_to_monitor')
    services = [s.strip() for s in services_str.split(',') if s.strip()]

    logger.info(f"Loaded {len(services)} service(s) from config: {', '.join(services)}")    

    # Optionally extend with prefixes
    prefixes = []
    if config.has_option('services', 'service_prefixes'):
        prefixes_str = config.get('services', 'service_prefixes')
        prefixes = [p.strip() for p in prefixes_str.split(',') if p.strip()]
        if prefixes:
            logger.info(f"Scanning for services starting with prefixes: {', '.join(prefixes)}")
            prefixed_services = find_services_with_prefixes(prefixes, logger)
            if prefixed_services:
                before_count = len(services)
                # Deduplicate while preserving order: existing + new that are not already present
                for name in prefixed_services:
                    if name not in services:
                        services.append(name)
                added = len(services) - before_count
                logger.info(f"Added {added} service(s) from prefixes")
            else:
                logger.warning("No services matched the configured prefixes")

    logger.info(f"Monitoring {len(services)} service(s): {', '.join(services)}")

    if len(services) == 0:
        logger.error("No services configured to monitor")
        sys.exit(1)

    # Check and start services
    all_running = check_and_start_services(services, logger)
    if not all_running:
        logger.error("Some services failed to start.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Windows Service Watchdog completed successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
