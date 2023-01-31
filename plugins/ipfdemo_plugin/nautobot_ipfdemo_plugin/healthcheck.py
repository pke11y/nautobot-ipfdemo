"""Custom Healthchecks for IP Fabric."""

from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from django.templatetags.static import static
from django.conf import settings
import requests

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG["nautobot_ipfdemo_plugin"]


# https://django-health-check.readthedocs.io/en/latest/readme.html#writing-a-custom-health-check
class IpFabricCheckBackend(BaseHealthCheckBackend):
    """Custom Health Check Class for IP Fabric."""

    critical_service = True

    def check_status(self):
        """Pull a static file to make sure it's good."""
        url = static("ipfdemo/statictest.txt")
        if url.startswith("/"):
            url = f"{PLUGIN_SETTINGS['static_root_url']}{url}"
        response = requests.get(url)
        if not response.status_code == 200:
            self.add_error(ServiceUnavailable(f"Unable to download statictest.txt from {url}"))
        elif "OK" not in response.text:
            self.add_error(ServiceUnavailable(f"Unable to find OK in statictest.txt from {url}"))

    def identifier(self):
        """Set the name in the GUI for healthcheck."""
        return self.__class__.__name__  # Display name on the endpoint.
