import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx

ALLOWED_SCHEMES = {"http", "https"}

ALLOWED_IMAGE_DOMAINS = {
    "i.imgur.com",
    "imgur.com",
    "images.unsplash.com",
    "res.cloudinary.com",
}

ALLOWED_DOMAIN_PATTERNS = [
    re.compile(r"^.+\.s3\.amazonaws\.com$"),
    re.compile(r"^storage\.googleapis\.com$"),
]

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def _is_domain_allowed(hostname: str) -> bool:
    if hostname in ALLOWED_IMAGE_DOMAINS:
        return True
    return any(pattern.match(hostname) for pattern in ALLOWED_DOMAIN_PATTERNS)


def _is_ip_blocked(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(addr in network for network in BLOCKED_NETWORKS)


def _resolve_hostname(hostname: str) -> list[str]:
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return [result[4][0] for result in results]
    except socket.gaierror:
        return []


async def validate_image_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, f"Scheme '{parsed.scheme}' not allowed. Use http or https."

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL."

    # If the hostname is an IP literal (IPv4 dotted-quad or bracketed IPv6),
    # urlparse strips the brackets and gives us the raw address. Check it
    # against BLOCKED_NETWORKS directly — do not rely on the domain allowlist
    # to incidentally reject it, since the allowlist only covers DNS names
    # and would give a misleading "not in allowlist" reason.
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if _is_ip_blocked(hostname):
            return False, "URL points to a blocked IP address."
        return False, "Direct IP URLs are not allowed; use an allowlisted domain."

    if not _is_domain_allowed(hostname):
        return False, f"Domain '{hostname}' is not in the allowlist."

    resolved_ips = _resolve_hostname(hostname)
    if not resolved_ips:
        return False, "Could not resolve hostname."

    for ip in resolved_ips:
        if _is_ip_blocked(ip):
            return False, "URL resolves to a blocked IP address."

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            response = await client.head(url)

            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_IMAGE_SIZE:
                return False, "Image exceeds maximum size of 10MB."

    except httpx.TimeoutException:
        return False, "URL validation timed out."
    except httpx.RequestError:
        return False, "Could not reach the URL."

    return True, "URL is valid."
