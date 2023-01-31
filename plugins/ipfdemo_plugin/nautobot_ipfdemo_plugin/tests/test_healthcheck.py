"""Tests for custom healthcheck functionality."""
import re
from django.conf import settings
from django.test import TestCase
from django.templatetags.static import static
import requests_mock
from nautobot_ipfdemo_plugin.healthcheck import IpFabricCheckBackend


class TestIpFabricHealthCheck(TestCase):
    """Verify IP Fabric Health Checks work correctly."""

    def test_static_file_health(self):
        """Verify static file availability is correctly reported."""
        static_url = static("ipfdemo/statictest.txt")
        if re.match("^/", static_url):
            settings.PLUGINS_CONFIG["nautobot_ipfdemo_plugin"]["static_root_url"] = "http://nautobot.local"
            base_url = settings.PLUGINS_CONFIG["nautobot_ipfdemo_plugin"]["static_root_url"]
            full_url = f"{base_url}{static_url}"
        else:
            full_url = static_url

        # Good Status
        with requests_mock.Mocker() as mocker:
            test_obj = IpFabricCheckBackend()
            mocker.get(full_url, text="OK")
            test_obj.check_status()
            self.assertEqual(len(test_obj.errors), 0)

        # 404
        with requests_mock.Mocker() as mocker:
            test_obj = IpFabricCheckBackend()
            mocker.get(full_url, text="OK", status_code=404)
            test_obj.check_status()
            self.assertEqual(len(test_obj.errors), 1)

        # Wrong Content
        with requests_mock.Mocker() as mocker:
            test_obj = IpFabricCheckBackend()
            mocker.get(full_url, text="BAD")
            test_obj.check_status()
            self.assertEqual(len(test_obj.errors), 1)
