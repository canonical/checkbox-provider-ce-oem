#!/usr/bin/env python3
import json
import logging
import argparse
from checkbox_support.snap_utils.snapd import Snapd
from checkbox_support.snap_utils.system import get_gadget_snap

CONFIG_FILE = {
    "test-strict-confinement": {
        "channel": "edge",
        "plugs": {
            "jace-bt-led": {
                "gadget": "bt-led",
            },
            "jace-hb-led": {
                "gadget": "hb-led",
            },
            "jace-shutdown-led": {
                "gadget": "shutdown-led",
            },
            "jace-status-led": {
                "gadget": "status-led",
            },
            "jace-wifi-grn-led": {
                "gadget": "wifi-grn-led",
            },
            "jace-wifi-yel-led": {
                "gadget": "wifi-yel-led",
            },
            "thermal": {
                "snapd": "hardware-observe",
            },
            "button": {
                "snapd": "device-buttons",
            },
            "time": {
                "snapd": "time-control",
            },
            "serial": {
                "snapd": "raw-usb",
            },
            "media-card": {
                "snapd": "removable-media",
            },
            "power-management": {
                "snapd": "shutdown",
            },
        },
    },
}


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


def get_snap_plugs(snapd, snap):
    """
    Get the list of plugs associated with a specific snap.

    Parameters:
        - snapd (Snapd): An instance of the Snapd class for interacting
                         with Snapd.
        - snap (str): The name of the snap for which plugs are to be retrieved.

    Returns:
        List[str]: A list of plugs associated with the specified snap.
    """
    snap_plugs = []
    for x in snapd.interfaces()["plugs"]:
        if x["snap"] == snap:
            snap_plugs.append(x["plug"])
    return snap_plugs


def get_config(config_file, config_path):
    """
    Load and retrieve the configuration from a JSON file.

    Parameters:
        - config_file (dict): The default configuration dictionary.
        - config_path (str): The path to the JSON configuration file.

    Returns:
        dict: The loaded configuration dictionary. Return default
              config file if not found additional one.
    """
    if config_path:
        try:
            config_file = json.load(open(config_path))
            return config_file
        except FileNotFoundError:
            logging.warning("Config file {} not found".format(config_path))
            logging.info("Using default config.")
            return config_file
    else:
        return config_file


def connect_interfaces(snapd,
                       plug_snap,
                       expect_plugs,
                       snap_plugs):
    """
    Connect expected plugs to a specific snap.

    Parameters:
        - snapd (Snapd): An instance of the Snapd class for interacting
                         with Snapd.
        - plug_snap (str): The name of the snap to which plugs are to
                           be connected.
        - expect_plugs (dict): A dictionary specifying expected plugs
                               and their corresponding slots.
        - snap_plugs (list): A list of plugs associated with the
                             specified snap.

    Returns:
        bool: True if all plugs are successfully connected, False otherwise.
    """
    status = True
    for plug in expect_plugs.keys():
        if plug in snap_plugs:
            (slot_snap, slot_plug), = expect_plugs[plug].items()
            if slot_snap == 'gadget':
                slot_snap = get_gadget_snap()
            try:
                logging.info("Attempting to connect interface "
                             "\"{}:{}\" \"{}:{}\""
                             .format(plug_snap,
                                     plug,
                                     slot_snap,
                                     slot_plug))
                snapd.connect(slot_snap,
                              slot_plug,
                              plug_snap,
                              plug)
            except Exception as err:
                status = False
                logging.error("Not able to connect plug \"{}:{}\" "
                              "to slot \"{}:{}\"."
                              .format(plug_snap,
                                      plug,
                                      slot_snap,
                                      slot_plug))
                logging.error(err)
        else:
            logging.error("Expect plug \"{}\" not in the snap \"{}\"."
                          .format(plug, plug_snap))
            status = False
    return status


def main():
    """
    This script facilitates the installation and connection of interfaces for
    a test snap.

    Usage:
        python script_name.py [--file CONFIG_FILE]

    Options:
        --file CONFIG_FILE  Path to the configuration file (JSON format)
                            specifying the target snap, its channel, and
                            the expected plugs to connect.

    Configuration File Format (JSON):
        The configuration file should follow the JSON format and contain
        a dictionary with snap names as keys and their respective
        configurations as values.

    Example Configuration:
        {
            "test-strict-confinement": {
                "channel": "edge",
                "plugs": {
                    "jace-bt-led": {"gadget": "bt-led"},
                    "jace-hb-led": {"gadget": "hb-led"},
                    ...
                }
            },
            ...
        }
    """
    parser = argparse.ArgumentParser(
        description="This is a script to install and connect expected plugs "
                    "for target snanp.")
    parser.add_argument('--file',
                        default=None,
                        help="The path with file name of the config file")
    args = parser.parse_args()
    status = True
    snapd = Snapd()
    config_file = get_config(CONFIG_FILE, args.file)
    for plug_snap in config_file.keys():
        logging.info("Attempting to install {}".format(plug_snap))
        if not snapd.list(plug_snap):
            try:
                snapd.install(plug_snap,
                              channel=config_file[plug_snap]['channel'])
            except Exception as err:
                logging.error(err)
                status = False
                continue
        else:
            logging.info("{} is already installed."
                         .format(plug_snap))
        snap_plugs = get_snap_plugs(snapd, plug_snap)
        expect_plugs = config_file[plug_snap]['plugs']
        status = connect_interfaces(snapd,
                                    plug_snap,
                                    expect_plugs,
                                    snap_plugs)
    if status:
        logging.info("Environment setup finished.")
    else:
        logging.error(
            "Environment setup finished with some error. "
            "Please check it and try it again."
        )
        raise SystemExit("Fail to setup environment!")


if __name__ == "__main__":
    main()
