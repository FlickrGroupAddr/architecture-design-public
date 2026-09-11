from __future__ import annotations

import base64
import subprocess
import sys
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

from defusedxml import ElementTree

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DIAGRAM_DIRECTORY = REPOSITORY_ROOT / "docs" / "diagrams"
P1_GOOGLE_LOGIN_ENDPOINT_VISIBLE_CENTER_X_FRACTION = 19 / 34
P1_GOOGLE_REFRESH_TARGET_X_FRACTION = 38 / 35
P1_JWKS_REFRESH_WORKER_LEFT_X_FRACTION = 41 / 420
P1_JWKS_REFRESH_WORKER_RIGHT_X_FRACTION = 88 / 105
P1_GOOGLE_LOGIN_LABEL_WIDTH = 108.890625
P1_JWKS_REFRESH_WORKER_LABEL_WIDTH = 152.953125
P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION = 101 / 180
P2_PLUGIN_CODE_API_VISIBLE_RIGHT_X_FRACTION = 43 / 45


class CleanRoomAuthDiagramTests(unittest.TestCase):
    def test_generated_files_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/build_clean_room_auth_diagram.py", "--check"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_drawio_sources_are_uncompressed_and_have_expected_sheets(self) -> None:
        expected = {
            "clean-room-authentication-legal.drawio": ("1400", "850"),
            "clean-room-authentication-4k.drawio": ("3840", "2160"),
        }
        expected_tabs = {
            "browser-session": "1 · Browser Session",
            "plugin-code-transfer": "2 · Plugin Code Generation",
            "publish-png-groups": "3 · Publish PNG + Groups",
        }
        for filename, (width, height) in expected.items():
            root = ElementTree.parse(DIAGRAM_DIRECTORY / filename).getroot()
            self.assertIsNotNone(root)
            assert root is not None
            self.assertEqual(root.tag, "mxfile")
            self.assertEqual(root.attrib.get("compressed"), "false")
            diagrams = root.findall("diagram")
            self.assertEqual(len(diagrams), 3)
            for page_id, tab_name in expected_tabs.items():
                diagram = next(
                    page for page in diagrams if f"-{page_id}-" in page.attrib.get("id", "")
                )
                self.assertEqual(diagram.attrib.get("name"), tab_name)
                model = diagram.find("mxGraphModel")
                self.assertIsNotNone(model)
                assert model is not None
                self.assertEqual(model.attrib.get("pageWidth"), width)
                self.assertEqual(model.attrib.get("pageHeight"), height)

                cells = model.findall("./root/mxCell")
                cell_ids = {cell.attrib["id"] for cell in cells}
                self.assertEqual(len(cell_ids), len(cells))
                for cell in cells:
                    if cell.attrib.get("edge") != "1":
                        continue
                    self.assertIn(cell.attrib["source"], cell_ids)
                    self.assertIn(cell.attrib["target"], cell_ids)

    def test_clean_sheet_contains_only_the_accepted_steps(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        self.assertIsNotNone(root)
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        self.assertIsNotNone(diagram)
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}
        values = "\n".join(cell.attrib.get("value", "") for cell in cells.values())
        self.assertEqual(
            cells["browser-session-title"].attrib.get("value"),
            "FlickrGroupAddr Browser Auth w/ Backend",
        )
        self.assertEqual(cells["browser-session-date"].attrib.get("value"), "2026-08-30")
        for required in (
            "Authority: Normative happy-path interaction map (ADR 0039, ADR 0041)",
            "User",
            "Browser",
            "FGA Backend Hosting Platform",
            "Provider Undecided",
            "FGA.com Authoritative",
            "CDN Provider",
            "FGA User UI",
            "JAMstack Static Frontend",
            "HTML · CSS · JS · Images · Etc.",
            "Authentication Flow",
            "User opens FGA.com",
            "Browser resolves FGA.com.",
            "Browser retrieves landing",
            "User clicks Login.",
            "sign-in redirect.",
            "FGA Google Login",
            "FGA Google JWKS",
            "FGA JWKS Refresh Worker",
            "Maximum 6h",
            "FGA Session Database",
            "Key: SHA2-256(token)",
            "Value: FGA Session Record",
            "Login Endpoint verifies CSRF:",
            "POST-cookie g_csrf_token ==",
            "request-body g_csrf_token.",
            "Login Endpoint reads current",
            "current Google-required",
            "validation: trusted alg/key,",
            "signature, iss, aud, and",
            "time claims.",
            "256-bit opaque token with",
            "Endpoint maps (iss, sub) to",
            "fgaUserId; atomically stores",
            "SHA2-256(token) session +",
            "sanitized login audit.",
            "__Host-… cookie: Secure,",
            "HttpOnly, Path=/,",
            "SameSite=Strict, no Domain,",
            "Max-Age=86400.",
            "omitted failure/lifecycle/provider detail stays with controlling sources",
            "failed logins are audited when possible",
            "proactive JWKS refresh is outside the numbered login sequence",
        ):
            self.assertIn(required, values)

        self.assertEqual(cells["dns"].attrib.get("parent"), "hosting-boundary")
        for backend_component in (
            "google-login-endpoint",
            "google-jwks-cache",
            "google-jwks-refresh-worker",
            "session-database",
        ):
            self.assertEqual(cells[backend_component].attrib.get("parent"), "hosting-boundary")
        self.assertEqual(cells["frontend"].attrib.get("parent"), "cdn-boundary")
        hosting_geometry = cells["hosting-boundary"].find("mxGeometry")
        cdn_geometry = cells["cdn-boundary"].find("mxGeometry")
        legend_geometry = cells["browser-session-flow"].find("mxGeometry")
        self.assertIsNotNone(hosting_geometry)
        self.assertIsNotNone(cdn_geometry)
        self.assertIsNotNone(legend_geometry)
        assert hosting_geometry is not None
        assert cdn_geometry is not None
        assert legend_geometry is not None
        self.assertEqual(
            (
                hosting_geometry.attrib.get("x"),
                hosting_geometry.attrib.get("y"),
                hosting_geometry.attrib.get("width"),
                hosting_geometry.attrib.get("height"),
            ),
            ("487.414", "90", "592.586", "690"),
        )
        self.assertEqual(
            (
                cdn_geometry.attrib.get("x"),
                cdn_geometry.attrib.get("y"),
                cdn_geometry.attrib.get("width"),
                cdn_geometry.attrib.get("height"),
            ),
            ("212.414", "90", "245", "258"),
        )
        self.assertEqual(
            (
                legend_geometry.attrib.get("x"),
                legend_geometry.attrib.get("y"),
                legend_geometry.attrib.get("width"),
                legend_geometry.attrib.get("height"),
            ),
            ("1110", "90", "259", "690"),
        )
        self.assertEqual(cells["google"].attrib.get("parent"), "1")
        google_style = cells["google"].attrib["style"]
        google_data_uri = google_style.split("image=", maxsplit=1)[1].split(
            ";fontSize", maxsplit=1
        )[0]
        google_svg = base64.b64decode(google_data_uri.partition(",")[2]).decode()
        self.assertIn('aria-label="Google"', google_svg)
        for edge_id in (
            "user-browser",
            "browser-dns",
            "browser-frontend",
            "browser-google",
            "browser-google-login",
            "login-jwks-cache",
            "login-session-database",
            "jwks-worker-google",
        ):
            edge = cells[edge_id]
            self.assertEqual(edge.attrib.get("edge"), "1")
            self.assertIn("startArrow=block", edge.attrib["style"])
            self.assertIn("endArrow=block", edge.attrib["style"])

        worker_cache_edge = cells["jwks-worker-cache"]
        self.assertEqual(worker_cache_edge.attrib.get("edge"), "1")
        self.assertIn("startArrow=none", worker_cache_edge.attrib["style"])
        self.assertIn("endArrow=block", worker_cache_edge.attrib["style"])

        legend = cells["browser-session-flow"]
        self.assertIn("strokeColor=#003087", legend.attrib["style"])
        self.assertIn("spacingLeft=10", legend.attrib["style"])
        self.assertIn("spacingRight=10", legend.attrib["style"])
        self.assertIn("font-size:14px", legend.attrib["value"])
        for number in range(1, 13):
            badge = cells[f"step-{number}"]
            self.assertEqual(badge.attrib.get("value"), str(number))
            self.assertIn("ellipse", badge.attrib["style"])
            self.assertIn("fillColor=#003087", badge.attrib["style"])

        for obsolete in (
            "Auth0",
            "Flickr OAuth handler",
            "FGA managed secret store",
            "FGA LrC Plugin",
            "Cloudflare",
            "Durable Object",
            "device-link",
        ):
            self.assertNotIn(obsolete, values)

    def test_browser_flow_layout(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        browser_geometry = cells["browser"].find("mxGeometry")
        user_geometry = cells["user"].find("mxGeometry")
        self.assertIsNotNone(browser_geometry)
        self.assertIsNotNone(user_geometry)
        assert browser_geometry is not None
        assert user_geometry is not None
        self.assertEqual(browser_geometry.attrib.get("y"), "440")
        self.assertEqual(browser_geometry.attrib.get("height"), "65")
        self.assertEqual(user_geometry.attrib.get("y"), "425")
        self.assertEqual(user_geometry.attrib.get("height"), "95")
        self.assertIn("align=right", cells["browser"].attrib["style"])

        login_geometry = cells["google-login-endpoint"].find("mxGeometry")
        self.assertIsNotNone(login_geometry)
        assert login_geometry is not None
        self.assertEqual(login_geometry.attrib.get("y"), "315")
        self.assertEqual(login_geometry.attrib.get("height"), "135")

        user_center = float(user_geometry.attrib["y"]) + float(user_geometry.attrib["height"]) / 2
        browser_center = (
            float(browser_geometry.attrib["y"]) + float(browser_geometry.attrib["height"]) / 2
        )
        login_center = (
            90 + float(login_geometry.attrib["y"]) + float(login_geometry.attrib["height"]) / 2
        )
        self.assertEqual(user_center, browser_center)
        self.assertEqual(browser_center, login_center)

        for edge_id in ("user-browser", "browser-google-login"):
            edge_style = cells[edge_id].attrib["style"]
            self.assertIn("exitY=0.5", edge_style)
            self.assertIn("entryY=0.5", edge_style)

        frontend_geometry = cells["frontend"].find("mxGeometry")
        self.assertIsNotNone(frontend_geometry)
        assert frontend_geometry is not None
        self.assertEqual(
            (
                frontend_geometry.attrib.get("x"),
                frontend_geometry.attrib.get("y"),
                frontend_geometry.attrib.get("width"),
                frontend_geometry.attrib.get("height"),
            ),
            ("32.5", "142.5", "180", "90"),
        )
        self.assertIn("verticalLabelPosition=top", cells["frontend"].attrib["style"])

        google_edge = cells["browser-google"]
        self.assertEqual(google_edge.attrib.get("source"), "browser")
        self.assertEqual(google_edge.attrib.get("target"), "google")
        self.assertIn("exitX=0.5;exitY=1", google_edge.attrib["style"])
        self.assertIn("entryX=0.5;entryY=0", google_edge.attrib["style"])

        frontend_edge = cells["browser-frontend"]
        self.assertEqual(frontend_edge.attrib.get("source"), "browser")
        self.assertEqual(frontend_edge.attrib.get("target"), "frontend")
        self.assertIn("exitX=0.5;exitY=0", frontend_edge.attrib["style"])
        self.assertIn("entryX=0.5;entryY=1", frontend_edge.attrib["style"])

    def test_page_one_primary_arrows_and_badges_are_exactly_aligned(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.svg"
        ).getroot()
        assert root is not None
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        lines = {
            line.attrib["id"]: line
            for line in root.findall(".//svg:line", namespace)
            if "id" in line.attrib
        }
        for edge_id in (
            "browser-frontend",
            "browser-google",
            "login-jwks-cache",
            "login-session-database",
        ):
            self.assertEqual(lines[edge_id].attrib["x1"], lines[edge_id].attrib["x2"])
        for edge_id in ("user-browser", "browser-google-login"):
            self.assertEqual(lines[edge_id].attrib["y1"], lines[edge_id].attrib["y2"])
        for edge_id in ("jwks-worker-google", "jwks-worker-cache"):
            self.assertEqual(lines[edge_id].attrib["y1"], lines[edge_id].attrib["y2"])

        badges = {
            circle.attrib["id"]: circle
            for circle in root.findall(".//svg:circle", namespace)
            if circle.attrib.get("id", "").startswith("step-")
        }
        dns_edge = lines["browser-dns"]
        step_2 = badges["step-2"]
        step_2_x = float(step_2.attrib["cx"])
        dns_x_1 = float(dns_edge.attrib["x1"])
        dns_x_2 = float(dns_edge.attrib["x2"])
        dns_y_1 = float(dns_edge.attrib["y1"])
        dns_y_2 = float(dns_edge.attrib["y2"])
        step_2_fraction = (step_2_x - dns_x_1) / (dns_x_2 - dns_x_1)
        expected_step_2_y = dns_y_1 + step_2_fraction * (dns_y_2 - dns_y_1)
        self.assertAlmostEqual(float(step_2.attrib["cy"]), expected_step_2_y, places=2)

        user_browser = lines["user-browser"]
        user_browser_midpoint = (
            float(user_browser.attrib["x1"]) + float(user_browser.attrib["x2"])
        ) / 2
        for number in (1, 4):
            self.assertEqual(float(badges[f"step-{number}"].attrib["cx"]), user_browser_midpoint)

        horizontal_arrow_y = float(user_browser.attrib["y1"])
        pair_gaps: list[float] = []
        for upper_number, lower_number in ((1, 4), (6, 12)):
            upper_gap = horizontal_arrow_y - float(badges[f"step-{upper_number}"].attrib["cy"])
            lower_gap = float(badges[f"step-{lower_number}"].attrib["cy"]) - horizontal_arrow_y
            self.assertEqual(upper_gap, lower_gap)
            pair_gaps.append(upper_gap)
        self.assertEqual(pair_gaps, [18.0, 18.0])

        for number, edge_id in ((3, "browser-frontend"), (5, "browser-google")):
            edge = lines[edge_id]
            badge = badges[f"step-{number}"]
            self.assertEqual(badge.attrib["cx"], edge.attrib["x1"])
            edge_midpoint = (float(edge.attrib["y1"]) + float(edge.attrib["y2"])) / 2
            self.assertEqual(float(badge.attrib["cy"]), edge_midpoint)

        jwks_edge = lines["login-jwks-cache"]
        jwks_midpoint = (float(jwks_edge.attrib["y1"]) + float(jwks_edge.attrib["y2"])) / 2
        self.assertEqual(float(badges["step-8"].attrib["cy"]), jwks_midpoint)

    def test_backend_authentication_components_form_vertical_stack(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        expected_geometry = {
            "session-database": ("267.586", "120", "190", "135"),
            "google-login-endpoint": ("267.586", "315", "170", "135"),
            "google-jwks-cache": ("292.586", "502.5", "140", "105"),
        }
        centers: set[float] = set()
        for identifier, expected in expected_geometry.items():
            geometry = cells[identifier].find("mxGeometry")
            self.assertIsNotNone(geometry)
            assert geometry is not None
            actual = tuple(
                geometry.attrib[attribute] for attribute in ("x", "y", "width", "height")
            )
            self.assertEqual(actual, expected)
            center_fraction = (
                P1_GOOGLE_LOGIN_ENDPOINT_VISIBLE_CENTER_X_FRACTION
                if identifier == "google-login-endpoint"
                else 0.5
            )
            centers.add(float(actual[0]) + float(actual[2]) * center_fraction)
        self.assertEqual(centers, {362.586})

        self.assertIn(
            "verticalLabelPosition=bottom",
            cells["google-jwks-cache"].attrib["style"],
        )
        self.assertIn("verticalLabelPosition=top", cells["session-database"].attrib["style"])
        self.assertIn("spacingBottom=18", cells["session-database"].attrib["style"])
        self.assertIn("labelPosition=right", cells["google-login-endpoint"].attrib["style"])

        jwks_edge_style = cells["login-jwks-cache"].attrib["style"]
        self.assertIn(
            f"exitX={P1_GOOGLE_LOGIN_ENDPOINT_VISIBLE_CENTER_X_FRACTION};exitY=0.95",
            jwks_edge_style,
        )
        self.assertIn("entryX=0.5;entryY=0", jwks_edge_style)
        session_edge_style = cells["login-session-database"].attrib["style"]
        self.assertIn(
            f"exitX={P1_GOOGLE_LOGIN_ENDPOINT_VISIBLE_CENTER_X_FRACTION};exitY=0.05",
            session_edge_style,
        )
        self.assertIn("entryX=0.5;entryY=1", session_edge_style)

        worker_geometry = cells["google-jwks-refresh-worker"].find("mxGeometry")
        self.assertIsNotNone(worker_geometry)
        assert worker_geometry is not None
        self.assertEqual(
            tuple(worker_geometry.attrib[attribute] for attribute in ("x", "y", "width", "height")),
            ("42.586", "502.5", "140", "105"),
        )
        self.assertIn(
            "verticalLabelPosition=bottom",
            cells["google-jwks-refresh-worker"].attrib["style"],
        )
        worker_cache_style = cells["jwks-worker-cache"].attrib["style"]
        self.assertIn(
            f"exitX={P1_JWKS_REFRESH_WORKER_RIGHT_X_FRACTION};exitY=0.5",
            worker_cache_style,
        )
        self.assertIn("entryX=0;entryY=0.5", worker_cache_style)

        worker_google_style = cells["jwks-worker-google"].attrib["style"]
        self.assertIn(
            f"exitX={P1_JWKS_REFRESH_WORKER_LEFT_X_FRACTION};exitY=0.5",
            worker_google_style,
        )
        self.assertIn(
            f"entryX={P1_GOOGLE_REFRESH_TARGET_X_FRACTION};entryY=0.5",
            worker_google_style,
        )

    def test_page_one_top_row_and_dns_worker_column_are_aligned(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        def geometry(identifier: str) -> tuple[float, float, float, float]:
            value = cells[identifier].find("mxGeometry")
            assert value is not None
            return (
                float(value.attrib["x"]),
                float(value.attrib["y"]),
                float(value.attrib["width"]),
                float(value.attrib["height"]),
            )

        dns = geometry("dns")
        frontend = geometry("frontend")
        hosting = geometry("hosting-boundary")
        session = geometry("session-database")
        worker = geometry("google-jwks-refresh-worker")
        step_6 = geometry("step-6")
        step_12 = geometry("step-12")

        row_centers = (
            hosting[1] + dns[1] + dns[3] / 2,
            90 + frontend[1] + frontend[3] / 2,
            hosting[1] + session[1] + session[3] / 2,
        )
        self.assertEqual(row_centers, (277.5,) * 3)
        column_centers = (
            hosting[0] + dns[0] + dns[2] / 2,
            step_6[0] + step_6[2] / 2,
            step_12[0] + step_12[2] / 2,
            hosting[0] + worker[0] + worker[2] / 2,
        )
        self.assertEqual(column_centers, (600.0,) * 4)
        self.assertIn("spacingBottom=12.9", cells["dns"].attrib["style"])
        self.assertIn("spacingTop=-9", cells["google-jwks-refresh-worker"].attrib["style"])

        svg_root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.svg"
        ).getroot()
        assert svg_root is not None
        svg_namespace = {"svg": "http://www.w3.org/2000/svg"}

        def label_baselines(first_line: str) -> tuple[float, float]:
            for text in svg_root.findall(".//svg:text", svg_namespace):
                tspans = text.findall("svg:tspan", svg_namespace)
                if not tspans or tspans[0].text != first_line:
                    continue
                first = float(text.attrib["y"])
                return (
                    first,
                    first + sum(float(tspan.attrib["dy"]) for tspan in tspans[1:]),
                )
            raise AssertionError(f"missing SVG label: {first_line}")

        self.assertEqual(
            label_baselines("FGA.com Authoritative")[1],
            label_baselines("FGA Session Database")[1],
        )
        self.assertEqual(
            label_baselines("FGA JWKS Refresh Worker")[0],
            label_baselines("FGA Google JWKS")[0],
        )

    def test_page_one_horizontal_reflow_preserves_component_and_print_gutters(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        def geometry(identifier: str) -> tuple[float, float, float, float]:
            value = cells[identifier].find("mxGeometry")
            assert value is not None
            return (
                float(value.attrib["x"]),
                float(value.attrib["y"]),
                float(value.attrib["width"]),
                float(value.attrib["height"]),
            )

        cdn = geometry("cdn-boundary")
        hosting = geometry("hosting-boundary")
        legend = geometry("browser-session-flow")
        self.assertEqual(hosting[0] - (cdn[0] + cdn[2]), 30)
        self.assertEqual(legend[0] - (hosting[0] + hosting[2]), 30)
        self.assertEqual(1400 - (legend[0] + legend[2]), 31)

        browser = geometry("browser")
        frontend = geometry("frontend")
        google = geometry("google")
        visual_column_centers = (
            browser[0] + browser[2] / 2,
            cdn[0] + frontend[0] + frontend[2] / 2,
            google[0] + google[2] / 2,
        )
        self.assertEqual(visual_column_centers, (334.914,) * 3)
        self.assertEqual(geometry("user")[0], 35)

        svg_root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.svg"
        ).getroot()
        assert svg_root is not None
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        label_anchors: dict[str, float] = {}
        title_baseline: float | None = None
        authority_baseline: float | None = None
        for text in svg_root.findall(".//svg:text", namespace):
            first_line = text.find("svg:tspan", namespace)
            if first_line is None or first_line.text is None:
                continue
            if first_line.text in (
                "FGA Google Login",
                "FGA JWKS Refresh Worker",
            ):
                label_anchors[first_line.text] = float(text.attrib["x"])
            elif first_line.text == "FlickrGroupAddr Browser Auth w/ Backend":
                title_baseline = float(text.attrib["y"])
            elif first_line.text.startswith("Authority:"):
                authority_baseline = float(text.attrib["y"])

        worker_left = (
            label_anchors["FGA JWKS Refresh Worker"] - P1_JWKS_REFRESH_WORKER_LABEL_WIDTH / 2
        )
        login_right = label_anchors["FGA Google Login"] + P1_GOOGLE_LOGIN_LABEL_WIDTH
        self.assertAlmostEqual(
            worker_left - hosting[0],
            hosting[0] + hosting[2] - login_right,
            delta=0.001,
        )

        assert title_baseline is not None
        assert authority_baseline is not None
        title_top = title_baseline - 15
        authority_bottom = authority_baseline + 2
        self.assertEqual(title_top, 34)
        self.assertEqual(850 - authority_bottom, 34)

    def test_jwks_refresh_arrows_have_matching_visible_glyph_whitespace(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.svg"
        ).getroot()
        assert root is not None
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        lines = {
            line.attrib["id"]: line
            for line in root.findall(".//svg:line", namespace)
            if "id" in line.attrib
        }

        marker_tip_length = 4 * 2.25
        google_visible_right = 264.914 + 140
        google_horizontal_gap = (
            float(lines["jwks-worker-google"].attrib["x2"])
            - marker_tip_length
            - google_visible_right
        )

        google_viewbox_width = 269.59
        google_viewbox_height = 81.589996
        google_visible_top = 620 + (50 - google_viewbox_height * 140 / google_viewbox_width) / 2
        google_vertical_gap = (
            google_visible_top - float(lines["browser-google"].attrib["y2"]) - marker_tip_length
        )

        worker_viewbox_width = 170
        worker_viewbox_height = 135
        worker_image_width = 140
        worker_image_height = 105
        worker_scale = worker_image_height / worker_viewbox_height
        worker_horizontal_padding = (worker_image_width - worker_viewbox_width * worker_scale) / 2
        worker_visible_left = 530 + worker_horizontal_padding + 28 * worker_scale
        worker_visible_right = 530 + worker_horizontal_padding + 142 * worker_scale
        worker_left_gap = (
            worker_visible_left
            - float(lines["jwks-worker-google"].attrib["x1"])
            - marker_tip_length
        )
        worker_right_gap = float(lines["jwks-worker-cache"].attrib["x1"]) - worker_visible_right

        self.assertAlmostEqual(google_horizontal_gap, google_vertical_gap, delta=0.25)
        self.assertAlmostEqual(worker_left_gap, google_horizontal_gap, delta=0.01)
        self.assertAlmostEqual(worker_right_gap, google_horizontal_gap, delta=0.01)

    def test_numbered_badges_follow_their_connectors(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-browser-session-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        expected_badge_positions = {
            1: ("198.707", "444.5"),
            2: ("410.594", "399.59"),
            3: ("324.914", "371.25"),
            4: ("198.707", "480.5"),
            5: ("324.914", "552.5"),
            6: ("590", "444.5"),
            7: ("875", "395"),
            8: ("840", "548.875"),
            9: ("905", "395"),
            10: ("935", "395"),
            11: ("840", "372"),
            12: ("590", "480.5"),
        }
        for number, expected_position in expected_badge_positions.items():
            geometry = cells[f"step-{number}"].find("mxGeometry")
            self.assertIsNotNone(geometry)
            assert geometry is not None
            self.assertEqual((geometry.attrib["x"], geometry.attrib["y"]), expected_position)

        dns_geometry = cells["dns"].find("mxGeometry")
        self.assertIsNotNone(dns_geometry)
        assert dns_geometry is not None
        self.assertEqual(dns_geometry.attrib.get("y"), "127.5")
        self.assertEqual(dns_geometry.attrib.get("height"), "120")
        self.assertIn("verticalLabelPosition=top", cells["dns"].attrib["style"])
        dns_edge_style = cells["browser-dns"].attrib["style"]
        self.assertIn(f"exitX={32 / 35};exitY={3 / 35}", dns_edge_style)
        self.assertIn("entryX=0.137;entryY=0.963", dns_edge_style)
        self.assertIn("entryX=0", cells["user-browser"].attrib["style"])
        self.assertIn("exitX=1", cells["browser-google-login"].attrib["style"])

    def test_browser_nodes_use_current_chrome_vector(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None

        for diagram_id, browser_id, expected_label_style in (
            ("fga-clean-room-browser-session-legal", "browser", "spacingRight=-25"),
            (
                "fga-clean-room-plugin-code-transfer-legal",
                "p2-browser",
                "verticalLabelPosition=top",
            ),
        ):
            diagram = root.find(f"./diagram[@id='{diagram_id}']")
            assert diagram is not None
            cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}
            browser = cells[browser_id]
            geometry = browser.find("mxGeometry")
            assert geometry is not None
            self.assertEqual(geometry.attrib["width"], "65")
            self.assertEqual(geometry.attrib["height"], "65")
            self.assertIn(expected_label_style, browser.attrib["style"])
            if browser_id == "p2-browser":
                self.assertIn("verticalLabelPosition=top", cells["p2-user"].attrib["style"])
                self.assertIn("spacingBottom=13", browser.attrib["style"])
                self.assertIn("spacingBottom=-2", cells["p2-user"].attrib["style"])
                user_geometry = cells["p2-user"].find("mxGeometry")
                assert user_geometry is not None
                self.assertEqual(geometry.attrib["y"], "370")
                self.assertEqual(user_geometry.attrib["y"], "355")
                for number, expected in (
                    (1, ("153", "378")),
                    (10, ("138", "408")),
                    (15, ("168", "408")),
                ):
                    step_geometry = cells[f"step-{number}"].find("mxGeometry")
                    assert step_geometry is not None
                    self.assertEqual(
                        (step_geometry.attrib["x"], step_geometry.attrib["y"]),
                        expected,
                    )

            data_uri = (
                browser.attrib["style"]
                .split("image=", maxsplit=1)[1]
                .split(";fontSize", maxsplit=1)[0]
            )
            chrome_svg = base64.b64decode(data_uri.partition(",")[2]).decode()
            self.assertIn('aria-label="Google Chrome Browser"', chrome_svg)
            self.assertIn('viewBox="0 0 48 48"', chrome_svg)
            self.assertIn("#1A73E8", chrome_svg)

    def test_plugin_code_transfer_page_is_simple_and_orthogonal(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        self.assertIsNotNone(diagram)
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}
        values = "\n".join(cell.attrib.get("value", "") for cell in cells.values())

        for required in (
            "Authority: Normative happy-path interaction map",
            "ADR 0006, ADR 0039, ADR 0040, ADR 0041, ADR 0044",
            "FlickrGroupAddr Plugin Code Generation",
            "FGA Backend Hosting Platform",
            "FGA Plugin Code API",
            "GET · POST · PATCH",
            "GET /api/v001/plugin-codes",
            "/api/v001/plugin-codes",
            "FGA Session Database",
            "FGA Installation Records",
            "FGA Append-Only Audit Log",
            "audit_events · Same FGA Database",
            "SHA2-256(Plugin Code)",
            "Installation + lrc_plugin Class",
            "FGA LrC plug-in",
            "LrC Password Store",
            "User opens FGA User UI",
            "FGA User UI JavaScript calls",
            "GET /api/v001/plugin-codes.",
            "Browser attaches the HttpOnly",
            "__Host-… cookie; JavaScript",
            "cannot read it.",
            "Plugin Code API computes",
            "SHA2-256(session token).",
            "API requests session status",
            "using that SHA2-256 digest.",
            "DB returns active, unexpired",
            "session with fgaUserId.",
            "API queries owned Plugin Code",
            "page by fgaUserId.",
            "Records return metadata page.",
            "API appends list-read audit.",
            "User selects Create",
            "GET returns metadata;",
            "JavaScript renders FGA User UI.",
            "Browser POSTs",
            "with cookie, exact origin,",
            "CSRF, and recent-auth proof.",
            "API generates 32 CSPRNG octets;",
            "encodes canonical 13-group",
            "Crockford Base32 Plugin Code.",
            "API atomically stores Plugin Code",
            "record + create audit event;",
            "never stores plaintext.",
            "exactly once with no-store.",
            "FGA User UI displays clear-text",
            "canonical Plugin Code once.",
            "clear-text FGA LrC plug-in input;",
            "compares identical grouped values.",
            "strictly validates",
            "clears field.",
        ):
            self.assertIn(required, values)

        for rejected in ("device code", "redemption code", "polling"):
            self.assertNotIn(rejected, values.casefold())
        self.assertNotIn("Admin UI", values)
        self.assertNotIn("LrPasswords", values)
        self.assertNotIn("password-style field", values)

        for backend_component in (
            "p2-installation-endpoint",
            "p2-session-database",
            "p2-installation-database",
            "p2-audit-log",
        ):
            self.assertEqual(cells[backend_component].attrib.get("parent"), "p2-hosting-boundary")
        for workstation_component in ("p2-lrc-mark", "p2-plugin", "p2-lrpasswords"):
            self.assertEqual(
                cells[workstation_component].attrib.get("parent"),
                "p2-workstation-boundary",
            )

        for edge_id in (
            "p2-user-browser",
            "p2-browser-installation-endpoint",
            "p2-endpoint-session-database",
            "p2-endpoint-installation-database",
            "p2-endpoint-audit-log",
            "p2-user-plugin",
            "p2-plugin-lrpasswords",
        ):
            style = cells[edge_id].attrib["style"]
            self.assertIn("edgeStyle=orthogonalEdgeStyle", style)
            self.assertIn("endArrow=block", style)
        for one_way_edge in ("p2-user-plugin", "p2-plugin-lrpasswords"):
            self.assertIn("startArrow=none", cells[one_way_edge].attrib["style"])
        self.assertIn(
            f"exitX=0.5;exitY={43 / 45}",
            cells["p2-plugin-lrpasswords"].attrib["style"],
        )
        self.assertIn("startArrow=none", cells["p2-endpoint-audit-log"].attrib["style"])
        for bidirectional_edge in (
            "p2-user-browser",
            "p2-browser-installation-endpoint",
            "p2-endpoint-session-database",
            "p2-endpoint-installation-database",
        ):
            self.assertIn("startArrow=block", cells[bidirectional_edge].attrib["style"])

        for number in range(1, 18):
            badge = cells[f"step-{number}"]
            self.assertEqual(badge.attrib.get("value"), str(number))

        badge_x_values: list[str] = []
        for number in (2, 9, 11, 14):
            badge_geometry = cells[f"step-{number}"].find("mxGeometry")
            assert badge_geometry is not None
            badge_x_values.append(badge_geometry.attrib["x"])
        self.assertEqual(badge_x_values, ["324", "369", "414", "459"])

        browser_geometry = cells["p2-browser"].find("mxGeometry")
        hosting_geometry = cells["p2-hosting-boundary"].find("mxGeometry")
        endpoint_geometry = cells["p2-installation-endpoint"].find("mxGeometry")
        session_geometry = cells["p2-session-database"].find("mxGeometry")
        installation_geometry = cells["p2-installation-database"].find("mxGeometry")
        assert browser_geometry is not None
        assert hosting_geometry is not None
        assert endpoint_geometry is not None
        assert session_geometry is not None
        assert installation_geometry is not None

        database_centers = {
            float(hosting_geometry.attrib["x"])
            + float(geometry.attrib["x"])
            + float(geometry.attrib["width"]) / 2
            for geometry in (session_geometry, installation_geometry)
        }
        self.assertEqual(database_centers, {724.0})
        endpoint_visible_center = (
            float(hosting_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["width"])
            * P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION
        )
        self.assertEqual(endpoint_visible_center, 724.0)

        browser_arrow_y = (
            float(browser_geometry.attrib["y"]) + float(browser_geometry.attrib["height"]) / 2
        )
        endpoint_y_center = (
            float(hosting_geometry.attrib["y"])
            + float(endpoint_geometry.attrib["y"])
            + float(endpoint_geometry.attrib["height"]) / 2
        )
        self.assertEqual(browser_arrow_y, endpoint_y_center)
        self.assertIn(
            "exitX=1;exitY=0.5",
            cells["p2-browser-installation-endpoint"].attrib["style"],
        )

    def test_plugin_code_backend_boundary_has_balanced_side_gutters(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        self.assertEqual(
            cells["p2-hosting-boundary"].attrib["value"],
            "FGA Backend Hosting Platform <i>(Provider Undecided)</i>",
        )

        workstation = cells["p2-workstation-boundary"].find("mxGeometry")
        hosting = cells["p2-hosting-boundary"].find("mxGeometry")
        legend = cells["plugin-code-transfer-flow"].find("mxGeometry")
        assert workstation is not None
        assert hosting is not None
        assert legend is not None

        workstation_right = float(workstation.attrib["x"]) + float(workstation.attrib["width"])
        hosting_left = float(hosting.attrib["x"])
        hosting_right = hosting_left + float(hosting.attrib["width"])
        legend_left = float(legend.attrib["x"])
        self.assertEqual(hosting_left - workstation_right, legend_left - hosting_right)
        self.assertEqual(hosting_left - workstation_right, 30)
        self.assertEqual(
            (
                hosting.attrib["width"],
                legend.attrib["x"],
                legend.attrib["width"],
                legend.attrib["height"],
            ),
            ("539", "1079", "290", "710"),
        )

    def test_plugin_code_audit_edge_and_labels_are_aligned(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        audit_geometry = cells["p2-audit-log"].find("mxGeometry")
        installation_geometry = cells["p2-installation-database"].find("mxGeometry")
        step_2_geometry = cells["step-2"].find("mxGeometry")
        step_8_geometry = cells["step-8"].find("mxGeometry")
        assert audit_geometry is not None
        assert installation_geometry is not None
        assert step_2_geometry is not None
        assert step_8_geometry is not None

        self.assertEqual(
            float(audit_geometry.attrib["y"]) + 7,
            float(installation_geometry.attrib["y"]),
        )
        session_style = cells["p2-session-database"].attrib["style"]
        self.assertIn("labelPosition=right", session_style)
        self.assertIn("spacingLeft=-22", session_style)
        installation_style = cells["p2-installation-database"].attrib["style"]
        self.assertIn("verticalLabelPosition=bottom", installation_style)
        self.assertIn("spacingTop=0", installation_style)
        audit_style = cells["p2-audit-log"].attrib["style"]
        self.assertIn("verticalLabelPosition=bottom", audit_style)
        self.assertIn("spacingTop=7", audit_style)
        audit_edge_style = cells["p2-endpoint-audit-log"].attrib["style"]
        self.assertIn("entryX=0.5;entryY=0.014", audit_edge_style)
        self.assertIn(
            f"exitX={P2_PLUGIN_CODE_API_VISIBLE_RIGHT_X_FRACTION};exitY=0.5",
            audit_edge_style,
        )
        self.assertIn(
            "labelPosition=left;align=right;verticalLabelPosition=middle;"
            "verticalAlign=top;spacingTop=20;spacingRight=-20",
            cells["p2-installation-endpoint"].attrib["style"],
        )
        self.assertEqual(step_8_geometry.attrib["y"], step_2_geometry.attrib["y"])

    def test_plugin_code_session_lookup_steps_have_distinct_badge_positions(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        hosting_geometry = cells["p2-hosting-boundary"].find("mxGeometry")
        endpoint_geometry = cells["p2-installation-endpoint"].find("mxGeometry")
        step_3_geometry = cells["step-3"].find("mxGeometry")
        step_4_geometry = cells["step-4"].find("mxGeometry")
        step_5_geometry = cells["step-5"].find("mxGeometry")
        step_6_geometry = cells["step-6"].find("mxGeometry")
        step_7_geometry = cells["step-7"].find("mxGeometry")
        step_12_geometry = cells["step-12"].find("mxGeometry")
        assert hosting_geometry is not None
        assert endpoint_geometry is not None
        assert step_3_geometry is not None
        assert step_4_geometry is not None
        assert step_5_geometry is not None
        assert step_6_geometry is not None
        assert step_7_geometry is not None
        assert step_12_geometry is not None

        endpoint_right = (
            float(hosting_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["width"])
        )
        endpoint_top = float(hosting_geometry.attrib["y"]) + float(endpoint_geometry.attrib["y"])
        self.assertEqual(
            float(step_12_geometry.attrib["x"]) + float(step_12_geometry.attrib["width"]),
            endpoint_right,
        )
        self.assertEqual(
            float(step_3_geometry.attrib["y"]) + float(step_3_geometry.attrib["height"]),
            endpoint_top + 8,
        )
        self.assertEqual(
            float(step_12_geometry.attrib["y"]) + float(step_12_geometry.attrib["height"]),
            endpoint_top + 8,
        )
        # The endpoint SVG has 13 units of transparent top padding. The badges use
        # eight of them and retain five units before the first visible black pixel.
        self.assertLess(
            float(step_12_geometry.attrib["y"]) + float(step_12_geometry.attrib["height"]),
            endpoint_top + 13,
        )
        self.assertEqual(step_3_geometry.attrib["y"], step_12_geometry.attrib["y"])
        self.assertLess(float(step_3_geometry.attrib["x"]), float(step_12_geometry.attrib["x"]))
        session_arrow_x = (
            float(hosting_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["width"])
            * P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION
        )
        self.assertLess(
            float(step_4_geometry.attrib["x"]) + float(step_4_geometry.attrib["width"]),
            session_arrow_x,
        )
        self.assertGreater(float(step_5_geometry.attrib["x"]), session_arrow_x)
        self.assertEqual(step_4_geometry.attrib["y"], step_5_geometry.attrib["y"])
        self.assertEqual(step_4_geometry.attrib["x"], step_6_geometry.attrib["x"])
        self.assertEqual(step_5_geometry.attrib["x"], step_7_geometry.attrib["x"])
        self.assertIn(
            f"exitX={P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION};exitY=0.022",
            cells["p2-endpoint-session-database"].attrib["style"],
        )

    def test_plugin_code_record_lookup_badges_show_request_and_response(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        hosting_geometry = cells["p2-hosting-boundary"].find("mxGeometry")
        endpoint_geometry = cells["p2-installation-endpoint"].find("mxGeometry")
        step_6_geometry = cells["step-6"].find("mxGeometry")
        step_7_geometry = cells["step-7"].find("mxGeometry")
        step_13_geometry = cells["step-13"].find("mxGeometry")
        assert hosting_geometry is not None
        assert endpoint_geometry is not None
        assert step_6_geometry is not None
        assert step_7_geometry is not None
        assert step_13_geometry is not None

        installation_arrow_x = (
            float(hosting_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["x"])
            + float(endpoint_geometry.attrib["width"])
            * P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION
        )
        self.assertLess(
            float(step_6_geometry.attrib["x"]) + float(step_6_geometry.attrib["width"]),
            installation_arrow_x,
        )
        self.assertGreater(float(step_7_geometry.attrib["x"]), installation_arrow_x)
        self.assertEqual(step_6_geometry.attrib["y"], step_7_geometry.attrib["y"])
        self.assertEqual(
            float(step_13_geometry.attrib["x"]) + float(step_13_geometry.attrib["width"]) / 2,
            installation_arrow_x,
        )
        self.assertGreater(
            float(step_13_geometry.attrib["y"]),
            float(step_6_geometry.attrib["y"]) + float(step_6_geometry.attrib["height"]),
        )
        installation_edge_style = cells["p2-endpoint-installation-database"].attrib["style"]
        self.assertIn(
            f"exitX={P2_PLUGIN_CODE_API_VISIBLE_CENTER_X_FRACTION};exitY=0.978",
            installation_edge_style,
        )
        self.assertIn("entryX=0.5;entryY=-0.034", installation_edge_style)

    def test_plugin_code_horizontal_arrows_end_pointing_right(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-plugin-code-transfer-legal.svg"
        ).getroot()
        assert root is not None
        elements = {element.attrib.get("id"): element for element in root.iter()}

        for edge_id in ("p2-user-browser", "p2-browser-installation-endpoint"):
            edge = elements[edge_id]
            self.assertTrue(edge.tag.endswith("line"))
            self.assertEqual(edge.attrib["y1"], edge.attrib["y2"])
            self.assertLess(float(edge.attrib["x1"]), float(edge.attrib["x2"]))

        plugin_store_edge = elements["p2-plugin-lrpasswords"]
        self.assertEqual(plugin_store_edge.attrib["y1"], "656")
        self.assertEqual(plugin_store_edge.attrib["y2"], "691")

        manual_entry_edge = elements["p2-user-plugin"]
        self.assertTrue(manual_entry_edge.tag.endswith("polyline"))
        self.assertEqual(manual_entry_edge.attrib["points"], "75,445 75,615 148,615")

    def test_plugin_store_arrow_and_labels_clear_visible_glyphs(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-plugin-code-transfer-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        manual_entry_edge = cells["p2-user-plugin"]
        self.assertEqual(manual_entry_edge.attrib["source"], "p2-user")
        self.assertEqual(manual_entry_edge.attrib["target"], "p2-plugin")
        manual_entry_bend = manual_entry_edge.find("mxGeometry/Array/mxPoint")
        assert manual_entry_bend is not None
        self.assertEqual(
            (manual_entry_bend.attrib["x"], manual_entry_bend.attrib["y"]),
            ("75", "615"),
        )

        for step, expected in ((16, ("65", "495")), (17, ("183", "659"))):
            geometry = cells[f"step-{step}"].find("mxGeometry")
            assert geometry is not None
            self.assertEqual((geometry.attrib["x"], geometry.attrib["y"]), expected)

        plugin_geometry = cells["p2-plugin"].find("mxGeometry")
        lrpasswords_geometry = cells["p2-lrpasswords"].find("mxGeometry")
        assert plugin_geometry is not None
        assert lrpasswords_geometry is not None
        self.assertEqual(plugin_geometry.attrib["x"], "20")
        self.assertEqual(lrpasswords_geometry.attrib["x"], "20")

        workstation_geometry = cells["p2-workstation-boundary"].find("mxGeometry")
        assert workstation_geometry is not None
        self.assertEqual(cells["p2-workstation-boundary"].attrib["value"], "")
        self.assertEqual(
            (workstation_geometry.attrib["y"], workstation_geometry.attrib["height"]),
            ("465", "315"),
        )

        lrc_mark = cells["p2-lrc-mark"]
        lrc_mark_geometry = lrc_mark.find("mxGeometry")
        assert lrc_mark_geometry is not None
        self.assertEqual(
            (
                lrc_mark_geometry.attrib["x"],
                lrc_mark_geometry.attrib["y"],
                lrc_mark_geometry.attrib["width"],
                lrc_mark_geometry.attrib["height"],
            ),
            ("260", "15", "85", "83"),
        )
        lrc_mark_data_uri = (
            lrc_mark.attrib["style"]
            .split("image=", maxsplit=1)[1]
            .split(";fontSize", maxsplit=1)[0]
        )
        lrc_mark_svg = base64.b64decode(lrc_mark_data_uri.partition(",")[2]).decode()
        self.assertIn('aria-label="Adobe Lightroom Classic"', lrc_mark_svg)
        self.assertIn('viewBox="0 0 240 234"', lrc_mark_svg)
        self.assertIn("#001E36", lrc_mark_svg)
        self.assertIn("#31A8FF", lrc_mark_svg)

        self.assertIn(
            f"entryX=0.5;entryY={-6 / 65}",
            cells["p2-plugin-lrpasswords"].attrib["style"],
        )
        self.assertIn("spacingLeft=-12", cells["p2-plugin"].attrib["style"])
        self.assertIn("spacingLeft=-27", cells["p2-lrpasswords"].attrib["style"])
        store_data_uri = (
            cells["p2-lrpasswords"]
            .attrib["style"]
            .split("image=", maxsplit=1)[1]
            .split(";fontSize", maxsplit=1)[0]
        )
        store_svg = base64.b64decode(store_data_uri.partition(",")[2]).decode()
        self.assertIn('viewBox="0 -5 170 140"', store_svg)

    def test_publish_png_and_group_flow_preserves_split_authority(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-publish-png-groups-legal']")
        self.assertIsNotNone(diagram)
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}
        values = "\n".join(cell.attrib.get("value", "") for cell in cells.values())
        self.assertEqual(
            cells["publish-png-groups-date"].attrib.get("value"),
            "2026-08-31",
        )

        for required in (
            "FlickrGroupAddr Publish PNG + Add to Groups",
            "Authority: Normative happy-path interaction map (ADRs 0005–0007, 0041)",
            "zero groups skip 16–19",
            "User chooses Create Album…;",
            "empty Album remains local-only.",
            "User adds one or more photos",
            "User selects zero or more",
            "add-only groups per photo.",
            "User chooses Album Publish Now;",
            "runtime supplies pending photos.",
            "FGA LrC Plugin",
            "LrC Password Store",
            "LrC Rendering Engine",
            "FGA API Backend",
            "FGA Database",
            "FGA Group-Submission",
            "Flickr Upload API",
            "Flickr REST API",
            "GET /api/v001/",
            "installations/current;",
            "SHA2-256; verifies active",
            "lrc_plugin; returns Connected.",
            "allowlisted",
            "upload metadata; no image bytes.",
            "no image bytes.",
            "signed envelope: no-store, memory-only.",
            "Plugin streams PNG directly to",
            "photo ID and Bearer.",
            "202 = durable handoff.",
            "fresh getAllContexts",
            "groups.getInfo",
            "pools.add &lt;1 s after getInfo",
            "group handling is add-only and fail-polite",
        ):
            self.assertIn(required, values)

        for workstation_component in (
            "p3-lrc-mark",
            "p3-plugin",
            "p3-lrpasswords",
            "p3-rendering-engine",
        ):
            self.assertEqual(
                cells[workstation_component].attrib.get("parent"),
                "p3-workstation-boundary",
            )
        for backend_component in (
            "p3-api-backend",
            "p3-database",
            "p3-group-worker",
        ):
            self.assertEqual(
                cells[backend_component].attrib.get("parent"),
                "p3-hosting-boundary",
            )
        for flickr_component in ("p3-upload-api", "p3-rest-api"):
            self.assertEqual(
                cells[flickr_component].attrib.get("parent"),
                "p3-flickr-boundary",
            )

        direct_upload = cells["p3-plugin-upload-api"]
        self.assertEqual(direct_upload.attrib.get("source"), "p3-plugin")
        self.assertEqual(direct_upload.attrib.get("target"), "p3-upload-api")
        self.assertIn("startArrow=block", direct_upload.attrib["style"])
        self.assertIn("endArrow=block", direct_upload.attrib["style"])
        self.assertNotIn("p3-api-backend", direct_upload.attrib.values())

        for number in range(1, 20):
            self.assertEqual(cells[f"step-{number}"].attrib.get("value"), str(number))

        self.assertNotIn("groups.pools.remove", values)
        self.assertNotIn("remove from group", values.casefold())

    def test_publish_png_layout_rebalances_boundaries_and_branding(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-publish-png-groups-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}
        geometry = {
            identifier: cells[identifier].find("mxGeometry")
            for identifier in (
                "p3-workstation-boundary",
                "p3-hosting-boundary",
                "p3-flickr-boundary",
                "p3-lrc-mark",
                "p3-upload-api",
                "p3-rest-api",
            )
        }
        assert all(item is not None for item in geometry.values())

        def geometry_for(identifier: str) -> Element:
            item = geometry[identifier]
            assert item is not None
            return item

        def center_x(identifier: str) -> float:
            item = geometry_for(identifier)
            return float(item.attrib["x"]) + float(item.attrib["width"]) / 2

        self.assertEqual(cells["p3-workstation-boundary"].attrib.get("value"), "")
        self.assertEqual(cells["p3-flickr-boundary"].attrib.get("value"), "")
        self.assertEqual(cells["p3-flickr-wordmark"].attrib.get("parent"), "p3-flickr-boundary")
        lrc_mark_geometry = geometry_for("p3-lrc-mark")
        self.assertEqual(
            (lrc_mark_geometry.attrib["x"], lrc_mark_geometry.attrib["y"]),
            ("12", "10"),
        )
        self.assertEqual(center_x("p3-upload-api"), center_x("p3-rest-api"))
        self.assertEqual(float(geometry_for("p3-workstation-boundary").attrib["width"]), 570.0)
        self.assertEqual(float(geometry_for("p3-hosting-boundary").attrib["width"]), 570.0)
        self.assertEqual(float(geometry_for("p3-flickr-boundary").attrib["x"]), 744.0)
        self.assertEqual(float(geometry_for("p3-flickr-boundary").attrib["width"]), 316.0)
        for identifier in ("p3-upload-api", "p3-rest-api"):
            self.assertIn(
                "labelPosition=right;align=left;verticalLabelPosition=middle;verticalAlign=middle",
                cells[identifier].attrib["style"],
            )

        svg_root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-publish-png-groups-legal.svg"
        ).getroot()
        assert svg_root is not None
        text_by_first_line = {
            element[0].text: element
            for element in svg_root.iter()
            if element.tag.endswith("text") and len(element) > 0 and element[0].text is not None
        }
        self.assertEqual(
            text_by_first_line["User chooses Create Album…;"].attrib["font-size"],
            "13.25",
        )
        self.assertEqual(
            (
                text_by_first_line["Flickr Upload API"].attrib["x"],
                text_by_first_line["Flickr Upload API"].attrib["y"],
            ),
            ("940", "250.2"),
        )
        self.assertEqual(
            (
                text_by_first_line["Flickr REST API"].attrib["x"],
                text_by_first_line["Flickr REST API"].attrib["y"],
            ),
            ("923", "584.7"),
        )
        self.assertEqual(text_by_first_line["LrC Password Store"].attrib["y"], "405")
        self.assertEqual(text_by_first_line["LrC Rendering Engine"].attrib["y"], "405")
        self.assertEqual(text_by_first_line["FGA LrC Plugin"].attrib["y"], "198")
        svg_elements = {element.attrib.get("id"): element for element in svg_root.iter()}
        flickr_badge_x = float(svg_elements["step-19"].attrib["cx"])
        self.assertEqual(flickr_badge_x, 775.0)
        for number in (12, 13, 15, 18):
            self.assertEqual(float(svg_elements[f"step-{number}"].attrib["cx"]), flickr_badge_x)
        # Native Chrome paints the blue badge one unit inside its vector circle.
        # Balance its left boundary clearance against the clearance to the base,
        # or widest part, of the right-pointing upload arrowhead.
        badge_painted_left = flickr_badge_x - 9
        badge_painted_right = flickr_badge_x + 9
        flickr_inner_left = 744 + 1
        upload_arrow = svg_elements["p3-plugin-upload-api"]
        arrow_marker = svg_elements["arrow"]
        arrowhead_base_x = float(upload_arrow.attrib["x2"]) - float(
            arrow_marker.attrib["refX"]
        ) * float(upload_arrow.attrib["stroke-width"])
        self.assertAlmostEqual(
            badge_painted_left - flickr_inner_left,
            arrowhead_base_x - badge_painted_right,
            delta=0.1,
        )

        user_arrow = svg_elements["p3-user-plugin"]
        user_badges = [svg_elements[f"step-{number}"] for number in (1, 2, 7, 8)]
        left_padding = (
            float(user_badges[0].attrib["cx"])
            - 10
            - float(geometry_for("p3-workstation-boundary").attrib["x"])
        )
        right_padding = float(user_arrow.attrib["x2"]) - (float(user_badges[-1].attrib["cx"]) + 10)
        self.assertAlmostEqual(left_padding, right_padding, delta=0.002)
        for badge in user_badges:
            self.assertEqual(
                float(user_arrow.attrib["y1"]) - (float(badge.attrib["cy"]) + 10),
                7.5,
            )

    def test_publish_png_component_triangles_are_balanced(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-legal.drawio"
        ).getroot()
        assert root is not None
        diagram = root.find("./diagram[@id='fga-clean-room-publish-png-groups-legal']")
        assert diagram is not None
        cells = {cell.attrib["id"]: cell for cell in diagram.iter("mxCell")}

        def geometry_for(identifier: str) -> Element:
            item = cells[identifier].find("mxGeometry")
            assert item is not None
            return item

        def center_x(identifier: str) -> float:
            item = geometry_for(identifier)
            return float(item.attrib["x"]) + float(item.attrib["width"]) / 2

        password_center = center_x("p3-lrpasswords")
        renderer_center = center_x("p3-rendering-engine")
        database_center = center_x("p3-database")
        worker_center = center_x("p3-group-worker")
        plugin_center = center_x("p3-plugin")
        self.assertEqual(database_center, password_center)
        self.assertEqual(worker_center, renderer_center)
        self.assertAlmostEqual(plugin_center - password_center, renderer_center - plugin_center)

        api_geometry = geometry_for("p3-api-backend")
        api_scale = float(api_geometry.attrib["height"]) / 135
        api_image_padding = (float(api_geometry.attrib["width"]) - 190 * api_scale) / 2
        api_rectangle_center = (
            float(api_geometry.attrib["x"]) + api_image_padding + (34 + 145 / 2) * api_scale
        )
        self.assertAlmostEqual(api_rectangle_center, plugin_center, places=3)
        self.assertAlmostEqual(
            api_rectangle_center - database_center,
            worker_center - api_rectangle_center,
            delta=0.001,
        )
        api_painted_half_width = (145 + 6) * api_scale / 2
        database_geometry = geometry_for("p3-database")
        database_scale = float(database_geometry.attrib["height"]) / 130
        database_painted_right = database_center + (168 + 3 - 90) * database_scale
        worker_geometry = geometry_for("p3-group-worker")
        worker_scale = float(worker_geometry.attrib["height"]) / 180
        worker_painted_left = worker_center - (252 + 4) * worker_scale / 2
        self.assertAlmostEqual(
            api_rectangle_center - api_painted_half_width - database_painted_right,
            worker_painted_left - (api_rectangle_center + api_painted_half_width),
            delta=0.1,
        )

        password_geometry = geometry_for("p3-lrpasswords")
        password_scale = float(password_geometry.attrib["height"]) / 140
        password_padding = (float(password_geometry.attrib["width"]) - 170 * password_scale) / 2
        password_painted_left = (
            float(password_geometry.attrib["x"]) + password_padding + (14 - 3) * password_scale
        )
        renderer_geometry = geometry_for("p3-rendering-engine")
        renderer_scale = float(renderer_geometry.attrib["height"]) / 140
        renderer_padding = (float(renderer_geometry.attrib["width"]) - 180 * renderer_scale) / 2
        renderer_painted_right = (
            float(renderer_geometry.attrib["x"])
            + renderer_padding
            + (10 + 160 + 3) * renderer_scale
        )
        workstation_width = float(geometry_for("p3-workstation-boundary").attrib["width"])
        self.assertAlmostEqual(
            password_painted_left,
            workstation_width - renderer_painted_right,
            delta=0.002,
        )

    def test_publish_png_connectors_reach_visible_glyphs(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-publish-png-groups-legal.svg"
        ).getroot()
        assert root is not None
        elements = {element.attrib.get("id"): element for element in root.iter()}
        arrow_marker = elements["arrow"]
        self.assertEqual(
            (arrow_marker.attrib["refX"], arrow_marker[0].attrib["d"]),
            ("7", "M 0 0 L 8 4 L 0 8 z"),
        )

        expected_polylines = {
            "p3-group-worker-rest-api": ("649.367,685 880,685 880,633.806"),
            "p3-api-database": ("256.589,642 256.589,577.074 331.589,577.074"),
        }
        for edge_id, points in expected_polylines.items():
            edge = elements[edge_id]
            self.assertTrue(edge.tag.endswith("polyline"))
            self.assertEqual(edge.attrib["points"], points)

        direct_upload = elements["p3-plugin-upload-api"]
        self.assertEqual(
            (
                direct_upload.attrib["x1"],
                direct_upload.attrib["y1"],
                direct_upload.attrib["x2"],
                direct_upload.attrib["y2"],
            ),
            ("483.139", "252", "820.8", "252"),
        )
        expected_corner_lines = {
            "p3-store-plugin": ("299.489", "332.25", "370.039", "298.1"),
            "p3-plugin-rendering-engine": (
                "483.139",
                "298.1",
                "549.339",
                "315.75",
            ),
        }
        for edge_id, expected_coordinates in expected_corner_lines.items():
            edge = elements[edge_id]
            self.assertTrue(edge.tag.endswith("line"))
            self.assertEqual(
                (
                    edge.attrib["x1"],
                    edge.attrib["y1"],
                    edge.attrib["x2"],
                    edge.attrib["y2"],
                ),
                expected_coordinates,
            )
        plugin_api = elements["p3-plugin-api-backend"]
        self.assertEqual(
            (
                plugin_api.attrib["x1"],
                plugin_api.attrib["y1"],
                plugin_api.attrib["x2"],
                plugin_api.attrib["y2"],
            ),
            ("426.589", "298.1", "426.589", "524.667"),
        )
        api_rest = elements["p3-api-rest-api"]
        self.assertEqual(
            (
                api_rest.attrib["x1"],
                api_rest.attrib["y1"],
                api_rest.attrib["x2"],
                api_rest.attrib["y2"],
            ),
            ("493.293", "578", "838.6", "578"),
        )
        database_worker = elements["p3-database-group-worker"]
        self.assertEqual(
            (
                database_worker.attrib["x1"],
                database_worker.attrib["y1"],
                database_worker.attrib["x2"],
                database_worker.attrib["y2"],
            ),
            ("309.389", "685", "543.812", "685"),
        )

        expected_badge_centers = {
            1: (194.02, 234.5),
            2: (236.02, 234.5),
            4: (446.589, 326.0),
            5: (294.089, 555.074),
            6: (446.589, 350.0),
            7: (278.02, 234.5),
            8: (320.02, 234.5),
            9: (516.339, 307.0),
            10: (446.589, 374.0),
            11: (294.089, 577.074),
            14: (446.589, 398.0),
            16: (446.589, 422.0),
            17: (294.089, 599.074),
        }
        for number, expected_center in expected_badge_centers.items():
            badge = elements[f"step-{number}"]
            self.assertEqual(
                (float(badge.attrib["cx"]), float(badge.attrib["cy"])),
                expected_center,
            )

        plugin_api_x = float(plugin_api.attrib["x1"])
        user_badges = [elements[f"step-{number}"] for number in (1, 2, 7, 8)]
        self.assertEqual(
            [float(badge.attrib["cx"]) for badge in user_badges],
            [194.02, 236.02, 278.02, 320.02],
        )
        self.assertEqual({float(badge.attrib["cy"]) for badge in user_badges}, {234.5})

        api_badges = [elements[f"step-{number}"] for number in (4, 6, 10, 14, 16)]
        self.assertEqual({float(badge.attrib["cx"]) for badge in api_badges}, {446.589})
        self.assertGreater(float(api_badges[0].attrib["cx"]) - 10, plugin_api_x)
        self.assertEqual(
            [float(badge.attrib["cy"]) for badge in api_badges],
            [326, 350, 374, 398, 422],
        )
        self.assertGreaterEqual(float(api_badges[0].attrib["cy"]) - 10, 316)
        self.assertLessEqual(float(api_badges[-1].attrib["cy"]) + 10, 440)

        group_line_y = 685
        step_18 = elements["step-18"]
        step_19 = elements["step-19"]
        self.assertEqual(group_line_y - float(step_18.attrib["cy"]), 18)
        self.assertEqual(float(step_19.attrib["cy"]) - group_line_y, 18)

    def test_publish_png_database_badges_cross_api_connector(self) -> None:
        root = ElementTree.parse(
            DIAGRAM_DIRECTORY / "clean-room-authentication-publish-png-groups-legal.svg"
        ).getroot()
        assert root is not None
        elements = {element.attrib.get("id"): element for element in root.iter()}
        api_database_points = tuple(
            tuple(float(coordinate) for coordinate in point.split(","))
            for point in elements["p3-api-database"].attrib["points"].split()
        )
        corner_x, corner_y = api_database_points[1]
        target_x, target_y = api_database_points[2]
        badge_5 = elements["step-5"]
        badge_11 = elements["step-11"]
        badge_17 = elements["step-17"]
        self.assertAlmostEqual(float(badge_11.attrib["cx"]), (corner_x + target_x) / 2)
        self.assertAlmostEqual(float(badge_11.attrib["cy"]), (corner_y + target_y) / 2)
        arrow_dx = target_x - corner_x
        arrow_dy = target_y - corner_y
        badge_axis_dx = float(badge_17.attrib["cx"]) - float(badge_5.attrib["cx"])
        badge_axis_dy = float(badge_17.attrib["cy"]) - float(badge_5.attrib["cy"])
        self.assertAlmostEqual(
            arrow_dx * badge_axis_dx + arrow_dy * badge_axis_dy,
            0,
            delta=0.1,
        )
        self.assertLess(float(badge_5.attrib["cy"]), corner_y)
        self.assertGreater(float(badge_17.attrib["cy"]), corner_y)

    def test_svg_derivatives_are_script_free_and_native_sized(self) -> None:
        expected = {
            "clean-room-authentication-legal.svg": ("1400", "850"),
            "clean-room-authentication-4k.svg": ("3840", "2160"),
            "clean-room-authentication-plugin-code-transfer-legal.svg": (
                "1400",
                "850",
            ),
            "clean-room-authentication-plugin-code-transfer-4k.svg": (
                "3840",
                "2160",
            ),
            "clean-room-authentication-publish-png-groups-legal.svg": (
                "1400",
                "850",
            ),
            "clean-room-authentication-publish-png-groups-4k.svg": (
                "3840",
                "2160",
            ),
        }
        for filename, (width, height) in expected.items():
            text = (DIAGRAM_DIRECTORY / filename).read_text(encoding="utf-8")
            root = ElementTree.fromstring(text)
            self.assertIsNotNone(root)
            assert root is not None
            self.assertEqual(root.attrib.get("width"), width)
            self.assertEqual(root.attrib.get("height"), height)
            self.assertNotIn("<script", text.casefold())

    def test_svg_arrow_markers_cover_stem_caps_on_every_tab(self) -> None:
        filenames = (
            "clean-room-authentication-legal.svg",
            "clean-room-authentication-plugin-code-transfer-legal.svg",
            "clean-room-authentication-publish-png-groups-legal.svg",
        )
        marker_tip_x = 8.0

        for filename in filenames:
            with self.subTest(svg=filename):
                root = ElementTree.parse(DIAGRAM_DIRECTORY / filename).getroot()
                assert root is not None
                marker = next(
                    element
                    for element in root.iter()
                    if element.tag.endswith("marker") and element.attrib.get("id") == "arrow"
                )
                ref_x = float(marker.attrib["refX"])
                # At least one marker unit of triangle must remain beyond the
                # connector endpoint. At that cross-section the triangle is at
                # least as wide as the stroke, hiding the square butt cap.
                self.assertLessEqual(ref_x, marker_tip_x - 1)

    def test_legal_svg_painted_bounds_are_centered_inside_print_margin(self) -> None:
        margin = 30.0
        filenames = (
            "clean-room-authentication-legal.svg",
            "clean-room-authentication-plugin-code-transfer-legal.svg",
            "clean-room-authentication-publish-png-groups-legal.svg",
        )
        for filename in filenames:
            root = ElementTree.parse(DIAGRAM_DIRECTORY / filename).getroot()
            assert root is not None
            width = float(root.attrib["width"])
            height = float(root.attrib["height"])
            drawing = next(element for element in root if element.tag.endswith("g"))
            title = next(element for element in drawing if element.tag.endswith("text"))
            authority = next(
                element for element in reversed(tuple(drawing)) if element.tag.endswith("text")
            )

            with self.subTest(filename=filename, element="title"):
                title_size = float(title.attrib["font-size"])
                self.assertGreaterEqual(float(title.attrib["x"]) - 1, margin)
                self.assertGreaterEqual(
                    float(title.attrib["y"]) - (title_size - 2),
                    margin,
                )

            with self.subTest(filename=filename, element="authority"):
                authority_size = float(authority.attrib["font-size"])
                self.assertGreaterEqual(float(authority.attrib["x"]) - 1, margin)
                self.assertLessEqual(
                    float(authority.attrib["y"]) + authority_size * 0.2,
                    height - margin,
                )

            legend = next(
                element
                for element in drawing
                if element.tag.endswith("rect") and element.attrib.get("stroke") == "#003087"
            )
            # Native Arial/Chrome rendering gives the shared title a 15-pixel
            # ascent and the authority line a one-pixel descent. At the smaller
            # tab-3 authority font, the initial "A" does not overhang its anchor.
            authority_overhang = 0 if "publish-png-groups" in filename else 1
            painted_left = float(authority.attrib["x"]) - authority_overhang
            painted_right = float(legend.attrib["x"]) + float(legend.attrib["width"])
            painted_top = float(title.attrib["y"]) - 15
            painted_bottom = float(authority.attrib["y"]) + 1
            with self.subTest(filename=filename, element="painted-center"):
                self.assertEqual(painted_left, width - 1 - painted_right)
                self.assertEqual(painted_top, height - 1 - painted_bottom)
                self.assertGreaterEqual(painted_left, margin)
                self.assertGreaterEqual(painted_top, margin)

            for element in drawing:
                local_name = element.tag.rpartition("}")[2]
                element_id = element.attrib.get("id", local_name)
                if local_name == "rect":
                    half_stroke = float(element.attrib.get("stroke-width", "0")) / 2
                    bounds = (
                        float(element.attrib["x"]) - half_stroke,
                        float(element.attrib["y"]) - half_stroke,
                        float(element.attrib["x"]) + float(element.attrib["width"]) + half_stroke,
                        float(element.attrib["y"]) + float(element.attrib["height"]) + half_stroke,
                    )
                elif local_name == "image":
                    bounds = (
                        float(element.attrib["x"]),
                        float(element.attrib["y"]),
                        float(element.attrib["x"]) + float(element.attrib["width"]),
                        float(element.attrib["y"]) + float(element.attrib["height"]),
                    )
                elif local_name == "circle":
                    radius = float(element.attrib["r"])
                    half_stroke = float(element.attrib.get("stroke-width", "0")) / 2
                    painted_radius = radius + half_stroke
                    bounds = (
                        float(element.attrib["cx"]) - painted_radius,
                        float(element.attrib["cy"]) - painted_radius,
                        float(element.attrib["cx"]) + painted_radius,
                        float(element.attrib["cy"]) + painted_radius,
                    )
                else:
                    continue

                with self.subTest(filename=filename, element=element_id):
                    left, top, right, bottom = bounds
                    self.assertGreaterEqual(left, margin)
                    self.assertGreaterEqual(top, margin)
                    self.assertLessEqual(right, width - margin)
                    self.assertLessEqual(bottom, height - margin)

    def test_4k_svg_legends_apply_raster_centering_insets(self) -> None:
        pairs = (
            (
                "clean-room-authentication-legal.svg",
                "clean-room-authentication-4k.svg",
                1,
            ),
            (
                "clean-room-authentication-plugin-code-transfer-legal.svg",
                "clean-room-authentication-plugin-code-transfer-4k.svg",
                1.5,
            ),
            (
                "clean-room-authentication-publish-png-groups-legal.svg",
                "clean-room-authentication-publish-png-groups-4k.svg",
                1,
            ),
        )
        scale_x = 3840 / 1400

        for legal_name, large_name, inset_pixels in pairs:
            with self.subTest(svg=large_name):
                legal_root = ElementTree.parse(DIAGRAM_DIRECTORY / legal_name).getroot()
                large_root = ElementTree.parse(DIAGRAM_DIRECTORY / large_name).getroot()
                assert legal_root is not None
                assert large_root is not None
                legal_legend = next(
                    element
                    for element in legal_root.iter()
                    if element.tag.endswith("rect")
                    and element.attrib.get("fill") == "#FFFFFF"
                    and element.attrib.get("stroke") == "#003087"
                )
                large_legend = next(
                    element
                    for element in large_root.iter()
                    if element.tag.endswith("rect")
                    and element.attrib.get("fill") == "#FFFFFF"
                    and element.attrib.get("stroke") == "#003087"
                )

                self.assertAlmostEqual(
                    float(large_legend.attrib["x"]),
                    float(legal_legend.attrib["x"]) * scale_x,
                    delta=0.001,
                )
                self.assertAlmostEqual(
                    float(large_legend.attrib["width"]),
                    float(legal_legend.attrib["width"]) * scale_x - inset_pixels,
                    delta=0.001,
                )


if __name__ == "__main__":
    unittest.main()
