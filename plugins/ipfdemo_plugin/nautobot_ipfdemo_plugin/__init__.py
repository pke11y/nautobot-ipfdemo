"""Nautobot plugin for IP Fabric."""
__version__ = "0.1.0"

from nautobot.extras.plugins import PluginConfig
from health_check.plugins import plugin_dir
from .healthcheck import IpFabricCheckBackend


class IpFabricConfig(PluginConfig):
    """Plugin configuration for the nautobot_ipfdemo plugin."""

    name = "nautobot_ipfdemo_plugin"
    verbose_name = "Simple project for IP Fabric"
    version = "0.1.0"
    author = "Network to Code"
    description = ""
    base_url = "ipfdemo"
    required_settings = []
    default_settings = {}
    caching_config = {}

    def ready(self):
        """Adds the IP Fabric Heath Check Backend to the health check registry."""
        plugin_dir.register(IpFabricCheckBackend)


config = IpFabricConfig  # pylint: disable=invalid-name
