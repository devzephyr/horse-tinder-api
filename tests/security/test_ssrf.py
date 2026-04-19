"""API7:2023 - Server Side Request Forgery (SSRF)

Tests that the URL validator blocks attempts to access internal resources
via horse photo URLs.
"""

from unittest.mock import patch

import pytest

from app.core.url_validator import validate_image_url


@pytest.mark.asyncio
class TestSSRF:
    async def test_aws_metadata_endpoint_blocked(self):
        """http://169.254.169.254/latest/meta-data/ must be rejected."""
        valid, msg = await validate_image_url(
            "http://169.254.169.254/latest/meta-data/"
        )
        assert not valid

    async def test_localhost_blocked(self):
        """http://127.0.0.1:5432/ must be rejected."""
        valid, msg = await validate_image_url("http://127.0.0.1:5432/")
        assert not valid

    async def test_localhost_hostname_blocked(self):
        """http://localhost/internal must be rejected."""
        valid, msg = await validate_image_url("http://localhost/internal")
        assert not valid

    async def test_private_10_network_blocked(self):
        """http://10.0.0.1/internal must be rejected."""
        valid, msg = await validate_image_url("http://10.0.0.1/internal")
        assert not valid

    async def test_private_172_network_blocked(self):
        """http://172.16.0.1/admin must be rejected."""
        valid, msg = await validate_image_url("http://172.16.0.1/admin")
        assert not valid

    async def test_private_192_network_blocked(self):
        """http://192.168.1.1/config must be rejected."""
        valid, msg = await validate_image_url("http://192.168.1.1/config")
        assert not valid

    async def test_ftp_scheme_blocked(self):
        """ftp://evil.com/img.jpg must be rejected."""
        valid, msg = await validate_image_url("ftp://evil.com/img.jpg")
        assert not valid

    async def test_file_scheme_blocked(self):
        """file:///etc/passwd must be rejected."""
        valid, msg = await validate_image_url("file:///etc/passwd")
        assert not valid

    async def test_data_scheme_blocked(self):
        """data: URIs must be rejected."""
        valid, msg = await validate_image_url("data:text/html,<script>alert(1)</script>")
        assert not valid

    async def test_non_allowlisted_domain_blocked(self):
        """Random domains not in the allowlist must be rejected."""
        valid, msg = await validate_image_url("https://evil.com/malware.jpg")
        assert not valid
        assert "allowlist" in msg

    @patch("app.core.url_validator._resolve_hostname", return_value=["151.101.1.69"])
    @patch("app.core.url_validator.httpx.AsyncClient")
    async def test_valid_imgur_url_accepted(self, mock_client_cls, mock_resolve):
        """A valid imgur URL with public IP should be accepted."""
        mock_client = mock_client_cls.return_value.__aenter__.return_value
        mock_response = type("Response", (), {"headers": {"content-length": "1000"}})()
        mock_client.head.return_value = mock_response

        valid, msg = await validate_image_url("https://i.imgur.com/abc123.jpg")
        assert valid

    @patch("app.core.url_validator._resolve_hostname", return_value=["10.0.0.1"])
    async def test_dns_rebinding_blocked(self, mock_resolve):
        """Allowlisted domain resolving to private IP must be blocked (DNS rebinding)."""
        valid, msg = await validate_image_url("https://i.imgur.com/rebind.jpg")
        assert not valid
        assert "blocked" in msg

    async def test_ipv6_loopback_blocked(self):
        """http://[::1]/admin must be rejected."""
        valid, msg = await validate_image_url("http://[::1]/admin")
        assert not valid

    async def test_zero_ip_blocked(self):
        """http://0.0.0.0/ must be rejected."""
        valid, msg = await validate_image_url("http://0.0.0.0/")
        assert not valid
