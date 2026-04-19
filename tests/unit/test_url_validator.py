from unittest.mock import patch

import pytest

from app.core.url_validator import _is_domain_allowed, _is_ip_blocked, validate_image_url


class TestDomainAllowlist:
    def test_allowed_domain(self):
        assert _is_domain_allowed("i.imgur.com")
        assert _is_domain_allowed("images.unsplash.com")
        assert _is_domain_allowed("res.cloudinary.com")

    def test_s3_pattern(self):
        assert _is_domain_allowed("mybucket.s3.amazonaws.com")

    def test_blocked_domain(self):
        assert not _is_domain_allowed("evil.com")
        assert not _is_domain_allowed("localhost")
        assert not _is_domain_allowed("internal.corp")


class TestIPBlocking:
    def test_private_ips_blocked(self):
        assert _is_ip_blocked("10.0.0.1")
        assert _is_ip_blocked("172.16.0.1")
        assert _is_ip_blocked("192.168.1.1")
        assert _is_ip_blocked("127.0.0.1")

    def test_metadata_ip_blocked(self):
        assert _is_ip_blocked("169.254.169.254")

    def test_loopback_ipv6_blocked(self):
        assert _is_ip_blocked("::1")

    def test_public_ip_allowed(self):
        assert not _is_ip_blocked("8.8.8.8")
        assert not _is_ip_blocked("151.101.1.69")

    def test_zero_network_blocked(self):
        assert _is_ip_blocked("0.0.0.0")


@pytest.mark.asyncio
class TestValidateImageUrl:
    async def test_invalid_scheme(self):
        valid, msg = await validate_image_url("ftp://i.imgur.com/image.jpg")
        assert not valid
        assert "Scheme" in msg

    async def test_file_scheme_blocked(self):
        valid, msg = await validate_image_url("file:///etc/passwd")
        assert not valid

    async def test_no_hostname(self):
        valid, msg = await validate_image_url("http://")
        assert not valid

    async def test_blocked_domain(self):
        valid, msg = await validate_image_url("https://evil.com/image.jpg")
        assert not valid
        assert "allowlist" in msg

    @patch("app.core.url_validator._resolve_hostname", return_value=["127.0.0.1"])
    async def test_resolves_to_private_ip(self, mock_resolve):
        valid, msg = await validate_image_url("https://i.imgur.com/image.jpg")
        assert not valid
        assert "blocked" in msg

    @patch("app.core.url_validator._resolve_hostname", return_value=["169.254.169.254"])
    async def test_aws_metadata_blocked(self, mock_resolve):
        valid, msg = await validate_image_url("https://i.imgur.com/metadata")
        assert not valid

    @patch("app.core.url_validator._resolve_hostname", return_value=[])
    async def test_unresolvable_hostname(self, mock_resolve):
        valid, msg = await validate_image_url("https://i.imgur.com/image.jpg")
        assert not valid
        assert "resolve" in msg
