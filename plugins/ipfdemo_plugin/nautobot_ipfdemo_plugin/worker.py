from django.conf import settings
from django_rq import job

from nautobot.dcim.models.device_components import Interface

from nautobot_chatops.workers import subcommand_of, handle_subcommands
from nautobot_chatops_ipfabric.worker import get_user_snapshot, ipf_api_client, ipfabric_logo
from nautobot_chatops_ipfabric.ipfabric_wrapper import IpFabric

CONFIG = settings.PLUGINS_CONFIG.get("nautobot_chatops_ipfabric", {})
BASE_CMD = "ipfabric"
IPFABRIC_LOGO_PATH = "nautobot_ssot_ipfabric/ipfabric_logo.png"
IPFABRIC_LOGO_ALT = "IPFabric Logo"

def prompt_inventory_device(action_id, help_text, dispatcher, filter_key, choices=None):
    """Prompt the user for input inventory search value selection."""
    ipfabric_api = ipf_api_client()
    inventory_data = ipfabric_api.client.inventory.devices.fetch(
        columns=IpFabric.DEVICE_INFO_COLUMNS,
        limit=IpFabric.DEFAULT_PAGE_LIMIT,
        snapshot_id=get_user_snapshot(dispatcher),
    )
    choices = {(device[filter_key], device[filter_key]) for device in inventory_data if device.get(filter_key)}
    dispatcher.prompt_from_menu(action_id, help_text, list(choices))
    return False

@job("default")
def ipfabric(subcommand, **kwargs):
    """Interact with ipfabric plugin."""
    return handle_subcommands("ipfabric", subcommand, **kwargs)

@subcommand_of("ipfabric")
def device_interfaces(dispatcher, hostname=None):
    """Aggregate device interface using the inventory interfaces table & Nautobot SoT."""

    # SET IPFABRIC API VARIABLES
    sub_cmd = "device-interfaces"
    snapshot_id = get_user_snapshot(dispatcher)
    filter_key = "hostname"

    INVENTORY_INTERFACES_COLUMNS = [
        "hostname",
        "intName",
        "siteName",
        "l1",
        "l2",
        "reason",
        "primaryIp",
    ]

    # GET HOSTNAME AS INPUT
    if not hostname:
        prompt_inventory_device(f"{BASE_CMD} {sub_cmd}", "Select device:", dispatcher, filter_key)
        return False

    # GET IPFABRIC & NAUTOBOT DATA
    ## IPFABRIC INTERFACE DATA
    filter_api = {filter_key: [IpFabric.EQ, hostname]}
    ipfabric_api = ipf_api_client()
    ipf_interfaces = ipfabric_api.client.inventory.interfaces.fetch(
        columns=INVENTORY_INTERFACES_COLUMNS,
        filters=filter_api,
        limit=IpFabric.DEFAULT_PAGE_LIMIT,
        snapshot_id=snapshot_id,
    )

    ## NAUTOBOT INTERFACE DATA
    interface_roles = {
        interface.name: interface.cf["interface_role"] for interface in Interface.objects.filter(device__name=hostname)
    }

    # TRANSFORM DATA
    device_interfaces = [{**intf, "role": interface_roles.get(intf["intName"])} for intf in ipf_interfaces]
    INVENTORY_INTERFACES_COLUMNS.append("role")

    # SEND COMMAND RESPONSE HEADER
    dispatcher.send_blocks(
        [
            *dispatcher.command_response_header(
                f"{BASE_CMD}",
                f"{sub_cmd}",
                [("Filter key", filter_key), ("Filter value", hostname)],
                "Inventory Interfaces",
                ipfabric_logo(dispatcher),
            ),
            dispatcher.markdown_block(f"{ipfabric_api.ui_url}inventory/interfaces"),
        ]
    )

    # SEND COMMAND RESPONSE DATA
    dispatcher.send_large_table(
        INVENTORY_INTERFACES_COLUMNS,
        [
            [
                interface.get(INVENTORY_INTERFACES_COLUMNS[i], IpFabric.EMPTY)
                for i in range(len(INVENTORY_INTERFACES_COLUMNS))
            ]
            for interface in device_interfaces
        ],
        title=f"Inventory Interfaces with {filter_key.upper()} {hostname}",
    )
    return True
