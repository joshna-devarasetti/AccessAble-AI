"""
Accessibility Checker Service
Audits HTML snippets and safely scans URLs for WCAG 2.1 Level A and AA violations.
Features robust SSRF protections, IP blocklists, and redirect validation.
"""

import re
import socket
import ipaddress
import logging
import urllib.parse
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


class SSRFValidationError(Exception):
    """Raised when an external URL targets a private, loopback, or disallowed address."""
    pass


class AccessibilityService:
    DISCLAIMER = (
        "Automated accessibility scans detect key structural, labeling, and semantic issues "
        "(typically 30-40% of WCAG criteria). Automated testing cannot verify human readability, "
        "screen reader pronunciation accuracy, or full manual keyboard flow."
    )

    @classmethod
    def is_safe_ip(cls, ip_str: str) -> bool:
        """
        Check if an IP address is publicly routable and not private/loopback/reserved.
        """
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
            # Carrier-grade NAT (100.64.0.0/10)
            cgnat = ipaddress.ip_network("100.64.0.0/10")
            if ip in cgnat:
                return False
            return True
        except ValueError:
            return False

    from typing import Tuple

    @classmethod
    def validate_and_resolve_url(cls, url: str) -> Tuple[str, str]:
        """
        Validates URL scheme, resolves hostname to IP, and validates safety against SSRF.
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise SSRFValidationError("Only HTTP and HTTPS protocols are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFValidationError("Invalid URL: missing hostname.")

        # Disallow localhost keywords
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise SSRFValidationError("Access to localhost / loopback addresses is prohibited for security.")

        try:
            # Resolve all IPs for the host
            addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            if not addr_info:
                raise SSRFValidationError(f"Unable to resolve host '{hostname}'.")

            # Check all resolved IPs
            for item in addr_info:
                ip_str = item[4][0]
                if not cls.is_safe_ip(ip_str):
                    raise SSRFValidationError(
                        f"Target host '{hostname}' resolved to prohibited or private IP ({ip_str})."
                    )

            target_ip = addr_info[0][4][0]
            return url, target_ip

        except socket.gaierror as e:
            raise SSRFValidationError(f"DNS resolution failed for '{hostname}': {str(e)}")

    @classmethod
    def fetch_url_safely(cls, target_url: str, max_size_bytes: int = 1048576, timeout_sec: int = 10) -> str:
        """
        Fetches web page HTML safely with redirect re-validation, timeouts, and size limits.
        """
        current_url = target_url
        headers = {
            "User-Agent": "AccessAble-AI-Accessibility-Scanner/1.0 (+https://accessable-ai.local)"
        }

        # Follow up to 3 redirects manually to re-validate each destination IP
        for hop in range(4):
            cls.validate_and_resolve_url(current_url)

            try:
                response = requests.get(
                    current_url,
                    headers=headers,
                    timeout=timeout_sec,
                    allow_redirects=False,
                    stream=True
                )
            except Exception as e:
                raise SSRFValidationError(f"Connection to '{current_url}' failed: {str(e)}")

            if response.is_redirect:
                loc = response.headers.get("Location")
                if not loc:
                    raise SSRFValidationError("Redirect response missing Location header.")
                current_url = urllib.parse.urljoin(current_url, loc)
                continue

            if response.status_code != 200:
                raise SSRFValidationError(f"HTTP request returned status code {response.status_code}.")

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                logger.warning("Target URL returned non-HTML Content-Type: %s", content_type)

            # Stream read up to max_size_bytes
            downloaded = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                downloaded.extend(chunk)
                if len(downloaded) > max_size_bytes:
                    raise SSRFValidationError(f"Response size exceeded limit ({max_size_bytes} bytes).")

            return downloaded.decode("utf-8", errors="replace")

        raise SSRFValidationError("Exceeded maximum redirect count (3).")

    @classmethod
    def analyze_html(cls, html_content: str, source_name: str = "Pasted HTML") -> Dict[str, Any]:
        """
        Performs comprehensive WCAG 2.1 checks on HTML content.
        """
        if not html_content or not html_content.strip():
            return {
                "success": False,
                "error": "HTML content is empty.",
                "summary": {},
                "issues": []
            }

        soup = BeautifulSoup(html_content, "html.parser")
        issues: List[Dict[str, Any]] = []

        # 1. Document Language (<html lang="...">)
        html_tag = soup.find("html")
        if not html_tag:
            issues.append({
                "id": "missing-html-tag",
                "name": "Missing <html> Root Element",
                "severity": "Moderate",
                "wcag_sc": "WCAG 2.1 - 3.1.1 Language of Page (Level A)",
                "element": "<html>",
                "description": "The document lacks a standard <html> root tag, preventing screen readers from identifying language and structure.",
                "suggestion": "Wrap your document in an '<html lang=\"en\">' root container."
            })
        elif not html_tag.get("lang") or not html_tag.get("lang").strip():
            issues.append({
                "id": "missing-lang-attr",
                "name": "Missing 'lang' Attribute on <html>",
                "severity": "Serious",
                "wcag_sc": "WCAG 2.1 - 3.1.1 Language of Page (Level A)",
                "element": str(html_tag)[:120],
                "description": "Screen readers need the 'lang' attribute to select the correct speech synthesizer, accent, and pronunciation rules.",
                "suggestion": "Add a valid BCP 47 language code to the <html> tag, e.g. <html lang=\"en\">."
            })

        # 2. Page Title (<title>)
        head_tag = soup.find("head")
        title_tag = soup.find("title")
        if not title_tag or not title_tag.get_text(strip=True):
            issues.append({
                "id": "missing-page-title",
                "name": "Missing or Empty Page <title>",
                "severity": "Serious",
                "wcag_sc": "WCAG 2.1 - 2.4.2 Page Titled (Level A)",
                "element": "<title>...</title>",
                "description": "The <title> element provides users of assistive technology with an immediate context of the webpage purpose.",
                "suggestion": "Include a descriptive <title> in the <head> section, e.g. <title>Dashboard - AccessAble AI</title>."
            })

        # 3. Images Missing Alt Text
        generic_alts = {"image", "photo", "picture", "graphic", "logo", "icon", "banner", "img", "screenshot"}
        for img in soup.find_all("img"):
            snippet = str(img)[:150]
            alt = img.get("alt")
            role = img.get("role")
            aria_hidden = img.get("aria-hidden")

            if aria_hidden == "true" or role == "presentation":
                continue

            if alt is None:
                issues.append({
                    "id": "img-missing-alt",
                    "name": "Image Missing 'alt' Attribute",
                    "severity": "Critical",
                    "wcag_sc": "WCAG 2.1 - 1.1.1 Non-text Content (Level A)",
                    "element": snippet,
                    "description": "Screen readers will read out the file name or URL of images without alt text, confusing non-sighted users.",
                    "suggestion": "Provide a descriptive alt attribute, e.g. alt=\"Student reviewing simplified study notes on a laptop\", or alt=\"\" if decorative."
                })
            elif alt.strip().lower() in generic_alts:
                issues.append({
                    "id": "img-generic-alt",
                    "name": "Image Has Non-Descriptive 'alt' Text",
                    "severity": "Moderate",
                    "wcag_sc": "WCAG 2.1 - 1.1.1 Non-text Content (Level A)",
                    "element": snippet,
                    "description": f"The alt text '{alt}' is generic and does not convey the functional or visual meaning of the image.",
                    "suggestion": "Replace generic terms like 'image' or 'photo' with specific descriptive alt text."
                })

        # 4. Form Controls Without Accessible Labels
        form_elements = soup.find_all(["input", "select", "textarea"])
        for el in form_elements:
            el_type = el.get("type", "").lower()
            if el_type in ("hidden", "submit", "button", "reset", "image"):
                continue

            el_id = el.get("id")
            snippet = str(el)[:150]
            has_label = False

            # Check matching <label for="id">
            if el_id:
                matching_label = soup.find("label", attrs={"for": el_id})
                if matching_label and matching_label.get_text(strip=True):
                    has_label = True

            # Check wrapping <label>
            if not has_label:
                parent_label = el.find_parent("label")
                if parent_label and parent_label.get_text(strip=True):
                    has_label = True

            # Check aria-label or aria-labelledby
            if not has_label:
                if el.get("aria-label", "").strip() or el.get("aria-labelledby", "").strip() or el.get("title", "").strip():
                    has_label = True

            if not has_label:
                issues.append({
                    "id": "form-control-missing-label",
                    "name": f"Form Control <{el.name}> Missing Accessible Label",
                    "severity": "Critical",
                    "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A), 4.1.2 Name, Role, Value",
                    "element": snippet,
                    "description": "Form inputs without accessible labels leave screen reader users unaware of what data is expected.",
                    "suggestion": "Add a visible <label for=\"inputId\">Name</label> or provide an 'aria-label' attribute."
                })

        # 5. Buttons Without Accessible Names
        for btn in soup.find_all("button"):
            btn_text = btn.get_text(strip=True)
            aria_label = btn.get("aria-label", "").strip()
            aria_labelledby = btn.get("aria-labelledby", "").strip()
            btn_title = btn.get("title", "").strip()

            # Check if button contains an image with alt text
            img_in_btn = btn.find("img")
            img_alt = img_in_btn.get("alt", "").strip() if img_in_btn else ""

            if not btn_text and not aria_label and not aria_labelledby and not btn_title and not img_alt:
                issues.append({
                    "id": "button-empty-name",
                    "name": "Button Missing Accessible Text / Name",
                    "severity": "Critical",
                    "wcag_sc": "WCAG 2.1 - 4.1.2 Name, Role, Value (Level A)",
                    "element": str(btn)[:150],
                    "description": "Buttons without text (often icon-only buttons) cannot be identified or spoken by screen readers.",
                    "suggestion": "Add descriptive inner text or 'aria-label=\"Search\"' to the button element."
                })

        # 6. Links Missing Discernible Text or Invalid Targets
        for a_tag in soup.find_all("a"):
            link_text = a_tag.get_text(strip=True)
            aria_label = a_tag.get("aria-label", "").strip()
            aria_labelledby = a_tag.get("aria-labelledby", "").strip()
            img_child = a_tag.find("img")
            img_alt = img_child.get("alt", "").strip() if img_child else ""
            href = a_tag.get("href", "").strip()

            if not link_text and not aria_label and not aria_labelledby and not img_alt:
                issues.append({
                    "id": "link-empty-text",
                    "name": "Link Missing Discernible Text",
                    "severity": "Critical",
                    "wcag_sc": "WCAG 2.1 - 2.4.4 Link Purpose (In Context) (Level A)",
                    "element": str(a_tag)[:150],
                    "description": "Screen readers navigating links by list will announce an empty or unreadable link.",
                    "suggestion": "Provide visible link text or add an aria-label describing the target."
                })
            elif href in ("#", "javascript:void(0)", "javascript:;", "") and not a_tag.get("role"):
                issues.append({
                    "id": "link-fake-button",
                    "name": "Link Used as Action Button (href='#')",
                    "severity": "Moderate",
                    "wcag_sc": "WCAG 2.1 - 4.1.2 Name, Role, Value (Level A)",
                    "element": str(a_tag)[:150],
                    "description": "Using <a> with href='#' causes unexpected focus jumps and confuses assistive tech expecting navigation.",
                    "suggestion": "Use a native <button type=\"button\"> for actions rather than an empty <a> tag."
                })

        # 7. Headings Structure & Hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        h1_tags = soup.find_all("h1")

        if len(h1_tags) == 0:
            issues.append({
                "id": "heading-missing-h1",
                "name": "Document Missing <h1> Heading",
                "severity": "Serious",
                "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A), 2.4.6 Headings and Labels",
                "element": "<body>...</body>",
                "description": "Every accessible document should have a primary <h1> that outlines the main topic of the page.",
                "suggestion": "Add an <h1> heading representing the main page subject."
            })
        elif len(h1_tags) > 1:
            issues.append({
                "id": "heading-multiple-h1",
                "name": "Multiple <h1> Headings Found",
                "severity": "Minor",
                "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A)",
                "element": f"{len(h1_tags)} <h1> elements detected",
                "description": "While HTML5 permits multiple <h1> tags, having a single top-level heading provides clearer page landmark hierarchy.",
                "suggestion": "Consider keeping a single main <h1> and nesting subsections under <h2>."
            })

        # Check for skipped heading levels (e.g. h1 -> h3)
        last_level = 0
        for h in headings:
            level = int(h.name[1])
            if last_level > 0 and level > last_level + 1:
                issues.append({
                    "id": "heading-skipped-level",
                    "name": f"Skipped Heading Level (<h{last_level}> to <h{level}>)",
                    "severity": "Moderate",
                    "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A)",
                    "element": str(h)[:150],
                    "description": f"Heading hierarchy jumped from <h{last_level}> directly to <h{level}> without an intermediate level.",
                    "suggestion": f"Reorganize headings logically using <h{last_level + 1}> before <h{level}>."
                })
            last_level = level

        # 8. Landmark Structure (<main>, <nav>, etc.)
        main_tag = soup.find("main") or soup.find(attrs={"role": "main"})
        if not main_tag:
            issues.append({
                "id": "missing-main-landmark",
                "name": "Missing <main> Landmark Region",
                "severity": "Serious",
                "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A)",
                "element": "<body>...</body>",
                "description": "Screen readers use the <main> landmark to allow users to skip repetitive header navigation.",
                "suggestion": "Wrap the primary page content inside a semantic <main> element."
            })

        # 9. Focus Outline Removal In Inline Styles
        elements_with_style = soup.find_all(style=True)
        for el in elements_with_style:
            style_str = el.get("style", "").lower()
            if "outline:none" in style_str.replace(" ", "") or "outline:0" in style_str.replace(" ", ""):
                issues.append({
                    "id": "removed-focus-outline",
                    "name": "Focus Indicator Removed via Inline 'outline: none'",
                    "severity": "Critical",
                    "wcag_sc": "WCAG 2.1 - 2.4.7 Focus Visible (Level AA)",
                    "element": str(el)[:150],
                    "description": "Removing focus outlines leaves keyboard-only and motor-impaired users unable to see which control has focus.",
                    "suggestion": "Do not remove outline without providing a high-contrast alternative :focus style."
                })

        # 10. Tables Without Headers
        for table in soup.find_all("table"):
            if not table.find("th"):
                issues.append({
                    "id": "table-missing-headers",
                    "name": "Data Table Missing <th> Header Cells",
                    "severity": "Moderate",
                    "wcag_sc": "WCAG 2.1 - 1.3.1 Info and Relationships (Level A)",
                    "element": str(table)[:150],
                    "description": "Data tables without <th> cells prevent screen readers from announcing column or row headers when navigating cells.",
                    "suggestion": "Add <th> elements with 'scope=\"col\"' or 'scope=\"row\"' attributes."
                })

        # 11. Media (video/audio) without captions/tracks
        for video in soup.find_all("video"):
            if not video.find("track"):
                issues.append({
                    "id": "video-missing-captions",
                    "name": "Video Element Missing Captions <track>",
                    "severity": "Serious",
                    "wcag_sc": "WCAG 2.1 - 1.2.2 Captions (Prerecorded) (Level A)",
                    "element": str(video)[:150],
                    "description": "Users who are deaf or hard of hearing require captions to understand spoken dialogue and sound cues.",
                    "suggestion": "Include a '<track kind=\"captions\" src=\"captions.vtt\" srclang=\"en\" label=\"English\">' element."
                })

        # Calculate severity tallies & score
        severity_counts = {
            "Critical": sum(1 for i in issues if i["severity"] == "Critical"),
            "Serious": sum(1 for i in issues if i["severity"] == "Serious"),
            "Moderate": sum(1 for i in issues if i["severity"] == "Moderate"),
            "Minor": sum(1 for i in issues if i["severity"] == "Minor")
        }

        # Weighted score (deductions: Critical: 20, Serious: 10, Moderate: 5, Minor: 2)
        total_deduction = (
            (severity_counts["Critical"] * 20)
            + (severity_counts["Serious"] * 10)
            + (severity_counts["Moderate"] * 5)
            + (severity_counts["Minor"] * 2)
        )
        score = max(0, 100 - total_deduction)

        if score >= 90:
            score_rating = "Excellent Accessibility Foundation"
            score_color = "success"
        elif score >= 75:
            score_rating = "Good (Minor Adjustments Needed)"
            score_color = "info"
        elif score >= 50:
            score_rating = "Needs Improvement (Barriers Detected)"
            score_color = "warning"
        else:
            score_rating = "Significant Barriers Detected"
            score_color = "danger"

        return {
            "success": True,
            "source_name": source_name,
            "score": score,
            "score_rating": score_rating,
            "score_color": score_color,
            "total_issues": len(issues),
            "severity_counts": severity_counts,
            "issues": issues,
            "disclaimer": cls.DISCLAIMER
        }
