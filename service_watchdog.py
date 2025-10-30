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
            start_service(service_name, logger)


def main():
    """Main function to run the service watchdog."""
    # Initialize with sji
    job_init = sji.SimpleJobInit(__file__)
    logger = job_init.logger
    config = job_init.config

    logger.info("=" * 60)
    logger.info("Starting Windows Service Watchdog")
    logger.info(f"Version: {sji.get_task_version(__file__)}")
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

    if not services:
        logger.warning("No services configured to monitor")
        return

    logger.info(f"Monitoring {len(services)} service(s): {', '.join(services)}")

    # Check and start services
    check_and_start_services(services, logger)

    logger.info("=" * 60)
    logger.info("Windows Service Watchdog completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
