"""Build the deliberately simplified FGA authentication architecture diagram.

The legal-landscape sheet is the authored source of truth for layout. The 4K
sheet is a deterministic 16:9 projection with a small outer-legend inset
that preserves raster centering. Both
diagrams.net source and browser-friendly SVG are generated without an external
graphics dependency.
"""

from __future__ import annotations

import argparse
import base64
import html
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DIAGRAM_DIRECTORY = REPOSITORY_ROOT / "docs" / "diagrams"
LEGAL_WIDTH = 1400
LEGAL_HEIGHT = 850
LEGAL_PRINT_MARGIN = 30
OUTER_TEXT_X = LEGAL_PRINT_MARGIN + 1
TITLE_DRAWIO_Y = 18
TITLE_SVG_BASELINE_Y = 49
# Native Arial rendering paints the title 15 units above its baseline and the
# authority line two units below its baseline. Matching those outer extents
# centers the complete painted composition vertically on the legal sheet.
TITLE_PAINTED_ASCENT = 15
AUTHORITY_PAINTED_DESCENT = 2
AUTHORITY_SVG_BASELINE_Y = (
    LEGAL_HEIGHT - (TITLE_SVG_BASELINE_Y - TITLE_PAINTED_ASCENT) - AUTHORITY_PAINTED_DESCENT
)


@dataclass(frozen=True)
class Sheet:
    """One physical or display-oriented rendering of the diagram."""

    name: str
    suffix: str
    width: int
    height: int

    @property
    def scale_x(self) -> float:
        """Return the horizontal scale relative to the legal composition."""

        return self.width / LEGAL_WIDTH

    @property
    def scale_y(self) -> float:
        """Return the vertical scale relative to the legal composition."""

        return self.height / LEGAL_HEIGHT

    @property
    def font_scale(self) -> float:
        """Scale text with height so the 4K derivative remains readable."""

        return self.scale_y


@dataclass(frozen=True)
class Boundary:
    """One deliberately simplified hosting boundary."""

    identifier: str
    x: float
    y: int
    width: float
    height: int
    drawio_label: str
    svg_label: tuple[str, ...]
    label_align: str = "center"


@dataclass(frozen=True)
class Icon:
    """One labeled, embedded vector glyph."""

    identifier: str
    x: float
    y: float
    width: int
    height: int
    drawio_label: str
    svg_label: tuple[str, ...]
    svg: str
    parent: str = "1"
    label_align: str = "center"
    label_position: str = "bottom"
    label_space: int = 30
    top_label_offset: float = 0
    bottom_label_offset: int = 0
    bottom_label_x_offset: int = 0
    right_label_offset: int = 0
    right_label_inset: int = 0
    center_right_label_on_image: bool = False


@dataclass(frozen=True)
class Edge:
    """One conceptual relationship between two diagram glyphs."""

    identifier: str
    source: str
    target: str
    source_x: float = 1
    source_y: float = 0.5
    target_x: float = 0
    target_y: float = 0.5
    bidirectional: bool = True
    orthogonal: bool = False
    drawio_target_y: float | None = None
    svg_target_x_offset: int = 0
    svg_target_y_offset: int = 0
    vertical_first: bool = False
    waypoints: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class FlowStep:
    """One chronological legend entry and its numbered canvas badge."""

    number: int
    edge: str
    badge_x: float
    badge_y: float
    lines: tuple[str, ...]


@dataclass(frozen=True)
class DiagramPage:
    """One diagrams.net tab and its standalone SVG projection."""

    identifier: str
    tab_name: str
    title: str
    date: str
    description: str
    legend_heading: str
    authority: str
    svg_stem: str
    boundaries: tuple[Boundary, ...]
    icons: tuple[Icon, ...]
    edges: tuple[Edge, ...]
    flow_steps: tuple[FlowStep, ...]
    legend_row_padding: int = 6
    legend_height: int = 690
    legend_min_row_height: int = 30
    legend_text_size: float = 14
    legend_x: int = 1110
    legend_width: int = 250
    legend_4k_inset_pixels: float = 1
    authority_baseline_y: float = AUTHORITY_SVG_BASELINE_Y
    authority_width: float = 1330
    arrow_marker_ref_x: int = 4


LEGAL = Sheet("Canonical legal landscape (8.5 × 14)", "legal", 1400, 850)
UHD = Sheet("Generated 16:9 native 4K", "4k", 3840, 2160)
SHEETS = (LEGAL, UHD)
LEGEND_X = 1110
LEGEND_Y = 90
LEGEND_WIDTH = 250
LEGEND_HEIGHT = 690
LEGEND_HEADING_SIZE = 16
LEGEND_NUMBER_SIZE = 12
LEGEND_TEXT_SIZE = 14
LEGEND_ROW_PADDING = 6
LEGEND_LINE_HEIGHT = 1.15

# These attachment fractions preserve roughly three drawing units of visible
# whitespace from the nearest rendered glyph pixel. The Google target also
# compensates for the wordmark's vertical letterboxing so its right-side gap
# matches the established top gap.
GOOGLE_REFRESH_TARGET_X_FRACTION = 38 / 35
JWKS_REFRESH_WORKER_LEFT_X_FRACTION = 41 / 420
JWKS_REFRESH_WORKER_RIGHT_X_FRACTION = 88 / 105
# Move the first two visual columns together while keeping the hosting right
# edge fixed. This preserves the paired label gutters and restores the original
# 250-unit separation between the DNS/JWKS and database/endpoint columns.
LEFT_COLUMN_SHIFT = 22.5859375
DNS_JWKS_COLUMN_CENTER_X = 622.5859375 - LEFT_COLUMN_SHIFT

HOSTING = Boundary(
    "hosting-boundary",
    510 - LEFT_COLUMN_SHIFT,
    90,
    570 + LEFT_COLUMN_SHIFT,
    690,
    "FGA Backend Hosting Platform<br><i>(Provider Undecided)</i>",
    ("FGA Backend Hosting Platform", "(Provider Undecided)"),
)

CDN = Boundary(
    "cdn-boundary",
    235 - LEFT_COLUMN_SHIFT,
    90,
    245,
    258,
    "CDN Provider<br><i>(Provider Undecided)</i>",
    ("CDN Provider", "(Provider Undecided)"),
)

BOUNDARIES = (HOSTING, CDN)
BOUNDARY_BY_ID = {boundary.identifier: boundary for boundary in BOUNDARIES}

USER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 160"
  role="img" aria-label="User">
  <circle cx="64" cy="36" r="28" fill="#1A1A1A"/>
  <path d="M14 151c0-39 22-67 50-67s50 28 50 67z" fill="#1A1A1A"/>
</svg>"""

# Wikimedia Commons lists Google's current Chrome icon as public-domain simple
# geometry. Chrome trademarks remain Google property; this visual uses the mark
# only to identify the Browser. Source:
# https://commons.wikimedia.org/wiki/File:Google_Chrome_icon_(February_2022).svg
CHROME_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"
  role="img" aria-label="Google Chrome Browser">
  <defs>
    <linearGradient id="chrome-red" x1="3.2173" y1="15" x2="44.7812" y2="15"
      gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#D93025"/>
      <stop offset="1" stop-color="#EA4335"/>
    </linearGradient>
    <linearGradient id="chrome-yellow" x1="20.7219" y1="47.6791" x2="41.5039"
      y2="11.6837" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#FCC934"/>
      <stop offset="1" stop-color="#FBBC04"/>
    </linearGradient>
    <linearGradient id="chrome-green" x1="26.5981" y1="46.5015" x2="5.8161"
      y2="10.506" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#1E8E3E"/>
      <stop offset="1" stop-color="#34A853"/>
    </linearGradient>
  </defs>
  <circle cx="24" cy="23.9947" r="12" fill="#FFFFFF"/>
  <path d="M3.2154 36A24 24 0 1 0 12 3.2154 24 24 0 0 0 3.2154 36ZM34.3923
    18A12 12 0 1 1 18 13.6077 12 12 0 0 1 34.3923 18Z" fill="none"/>
  <path d="M24 12H44.7812A23.9939 23.9939 0 0 0 3.2173 12.0029L13.6079
    30l.0093-.0024A11.9852 11.9852 0 0 1 24 12Z" fill="url(#chrome-red)"/>
  <circle cx="24" cy="24" r="9.5" fill="#1A73E8"/>
  <path d="M34.3913 30.0029 24.0007 48A23.994 23.994 0 0 0 44.78
    12.0031H23.9989l-.0025.0093A11.985 11.985 0 0 1 34.3913 30.0029Z"
    fill="url(#chrome-yellow)"/>
  <path d="M13.6086 30.0031 3.218 12.006A23.994 23.994 0 0 0 24.0025
    48L34.3931 30.0029l-.0067-.0068a11.9852 11.9852 0 0 1-20.7778.007Z"
    fill="url(#chrome-green)"/>
</svg>"""

SERVER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 180"
  role="img" aria-label="Server">
  <g fill="#546E7A" stroke="#1A1A1A" stroke-width="4">
    <rect x="10" y="10" width="140" height="45" rx="7"/>
    <rect x="10" y="68" width="140" height="45" rx="7"/>
    <rect x="10" y="126" width="140" height="45" rx="7"/>
  </g>
  <g fill="#FFFFFF">
    <circle cx="30" cy="32.5" r="6"/>
    <circle cx="30" cy="90.5" r="6"/>
    <circle cx="30" cy="148.5" r="6"/>
  </g>
  <g stroke="#FFFFFF" stroke-width="5" stroke-linecap="round">
    <path d="M50 32.5h78"/>
    <path d="M50 90.5h78"/>
    <path d="M50 148.5h78"/>
  </g>
</svg>"""

FRONTEND_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150"
  role="img" aria-label="Static Web Frontend">
  <rect x="8" y="8" width="184" height="134" rx="8" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <path d="M8 38h184" stroke="#1A1A1A" stroke-width="6"/>
  <g fill="#546E7A">
    <circle cx="25" cy="23" r="6"/>
    <circle cx="45" cy="23" r="6"/>
    <circle cx="65" cy="23" r="6"/>
    <rect x="28" y="58" width="58" height="56" rx="5"/>
    <rect x="102" y="58" width="70" height="12" rx="4"/>
    <rect x="102" y="82" width="70" height="12" rx="4"/>
    <rect x="102" y="106" width="48" height="12" rx="4"/>
  </g>
</svg>"""

LOGIN_ENDPOINT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 135"
  role="img" aria-label="Verified Login Endpoint">
  <rect x="34" y="12" width="145" height="111" rx="10" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <path d="M3 67h63m-18-18 18 18-18 18" fill="none" stroke="#546E7A"
    stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M110 32 146 45v27c0 23-14 38-36 48-22-10-36-25-36-48V45z"
    fill="#003087"/>
  <path d="m91 72 13 13 25-29" fill="none" stroke="#FFFFFF" stroke-width="8"
    stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

JWKS_CACHE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 135"
  role="img" aria-label="JWKS Cache">
  <path d="M15 28c0-14 31-24 70-24s70 10 70 24v78c0 14-31 24-70 24s-70-10-70-24z"
    fill="#FFFFFF" stroke="#1A1A1A" stroke-width="6"/>
  <ellipse cx="85" cy="28" rx="70" ry="24" fill="#CFD8DC" stroke="#1A1A1A"
    stroke-width="6"/>
  <path d="M15 65c0 14 31 24 70 24s70-10 70-24M15 99c0 14 31 24 70 24s70-10 70-24"
    fill="none" stroke="#546E7A" stroke-width="6"/>
  <circle cx="70" cy="57" r="11" fill="none" stroke="#003087" stroke-width="7"/>
  <path d="M81 57h42m-14 0v13m-14-13v9" fill="none" stroke="#003087"
    stroke-width="7" stroke-linecap="round"/>
</svg>"""

JWKS_REFRESH_WORKER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 135"
  role="img" aria-label="FGA JWKS Refresh Worker">
  <circle cx="85" cy="67.5" r="54" fill="#FFFFFF" stroke="#1A1A1A"
    stroke-width="6"/>
  <path d="M85 31v38l25 17" fill="none" stroke="#003087" stroke-width="8"
    stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="85" cy="67.5" r="7" fill="#003087"/>
  <path d="M42 31a57 57 0 0 1 85 1" fill="none" stroke="#3186FF"
    stroke-width="7" stroke-linecap="round"/>
  <path d="m127 18 2 19-19-2" fill="#3186FF"/>
</svg>"""

SESSION_DATABASE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 130"
  role="img" aria-label="Key Value Session Database">
  <path d="M12 25C12 12 47 3 90 3s78 9 78 22v80c0 13-35 22-78 22s-78-9-78-22z"
    fill="#FFFFFF" stroke="#1A1A1A" stroke-width="6"/>
  <ellipse cx="90" cy="25" rx="78" ry="22" fill="#CFD8DC" stroke="#1A1A1A"
    stroke-width="6"/>
  <path d="M12 63c0 13 35 22 78 22s78-9 78-22M12 98c0 13 35 22 78 22s78-9 78-22"
    fill="none" stroke="#546E7A" stroke-width="6"/>
  <rect x="38" y="48" width="44" height="13" rx="4" fill="#003087"/>
  <rect x="96" y="48" width="46" height="13" rx="4" fill="#546E7A"/>
  <rect x="38" y="88" width="44" height="13" rx="4" fill="#003087"/>
  <rect x="96" y="88" width="46" height="13" rx="4" fill="#546E7A"/>
</svg>"""

# Wikimedia Commons lists this Google LLC wordmark as public domain. Google
# trademarks remain Google property; the mark is used here only to identify the
# external identity provider.
# Source: https://commons.wikimedia.org/wiki/File:Google_2026_logo.svg
GOOGLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 269.59 81.589996"
  role="img" aria-label="Google">
  <path d="M31.32 63.35C48.97 63.52 60.99 51.67 60.99 33.43Q61 31.14
    60.56 28.35H31.2v8.76h20.6C50.7 48.58 42.62 54.55 31.53 54.55
    19.09 54.55 9.57 45.2 9.57 31.61 9.57 18.2 18.67 8.84 31.53
    8.84c6.48 0 11.26 2 16.04 6.9l6.14-6.43C48.33 3.01 40.55 0
    31.41 0 13.7 0 0 13.29 0 31.48c0 17.4 13.25 31.7 31.32 31.87"
    fill="#3186ff"/>
  <path d="M88.2 63.35c13.2 0 22.77-9.69 22.77-23.15
    0-13.2-9.35-22.98-22.77-22.98-12.7 0-22.68 9.02-22.68 22.98
    0 13.33 9.43 23.15 22.68 23.15m0-8.04c-8.04 0-13.67-6.6-13.67-15.1
    0-8.5 5.93-14.95 13.67-14.95 8.17 0 13.67 6.6 13.67 14.94
    0 8.64-5.63 15.11-13.67 15.11" fill="#fc413d"/>
  <path d="M137.42 63.35c13.29 0 22.77-9.73 22.77-23.15
    0-13.2-9.35-22.98-22.77-22.98-12.7 0-22.68 9.02-22.68 22.98
    0 13.33 9.43 23.15 22.68 23.15m0-8.04c-8.04 0-13.67-6.6-13.67-15.1
    0-8.5 5.93-14.95 13.67-14.95 8.17 0 13.67 6.6 13.67 14.94
    0 8.64-5.63 15.11-13.67 15.11" fill="#ffbe00"/>
  <path d="M185.37 81.59q21.51 0 21.5-24.63V18.79h-8.8v5.37h-.17
    c-2.75-4.27-7.96-6.68-13.84-6.68-12.7 0-20.44 9.69-20.44 22.6
    0 12.86 7.53 22.34 20.78 22.34 6.52 0 11.34-3.72 13.37-6.77h.3
    v3.94c0 8.67-4.49 13.8-12.82 13.8-5.46 0-9.1-3.01-11.77-8.05
    l-7.96 3.52c4.2 8.84 10.16 12.73 19.85 12.73m0-27.55
    c-7.74 0-12.7-5.71-12.7-14.22 0-8.2 4.92-14.13 12.75-14.13
    s12.65 5.5 12.65 14.09c0 8.68-5.08 14.26-12.7 14.26" fill="#3186ff"/>
  <path d="M222.91 1.35h-9.22v60.6h9.22z" fill="#00af57"/>
  <path d="M250.17 63.27a22.1 22.1 0 0 0 19-10.54l-6.86-4.49
    c-3 4.2-7.1 6.6-11.72 6.6a13.6 13.6 0 0 1-11.93-7.23l30.93-13.12
    a20 20 0 0 0-.84-3.22c-3.69-9.48-10.12-13.8-18.8-13.8
    -13.24 0-22.25 9.66-22.25 23.03 0 13.67 9.47 22.77 22.47 22.77
    m-13.5-22.81v-.51c0-8.76 5.03-14.64 12.95-14.64 3.76 0 7.15 1.69
    9.44 5.67z" fill="#fc413d"/>
</svg>"""

PLUGIN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 135"
  role="img" aria-label="FGA Lightroom Classic Plugin">
  <rect x="12" y="10" width="146" height="115" rx="10" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <path d="M62 42v20m46-20v20M53 60h64v20c0 18-14 32-32 32S53 98 53 80z"
    fill="#CFD8DC" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/>
  <path d="M85 112v13" stroke="#003087" stroke-width="9"
    stroke-linecap="round"/>
  <circle cx="85" cy="79" r="10" fill="#003087"/>
</svg>"""

# Hand-drawn Adobe Lightroom Classic mark reused from the prior FGA backend API
# architecture diagram. It identifies Lightroom Classic nominatively and is not
# copied from an Adobe-distributed asset.
# Source: https://github.com/FlickrGroupAddr/backend-api/blob/main/docs/architecture/FlickrGroupAddr-Architecture-2026-08-19-8.5x14.drawio
LIGHTROOM_CLASSIC_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 234"
  role="img" aria-label="Adobe Lightroom Classic">
  <rect x="0" y="0" width="240" height="234" rx="42" ry="42" fill="#001E36"/>
  <g fill="#31A8FF">
    <path d="M27 77 h19 v61 h29 v19 H27 Z"/>
    <path d="M85 102 h18 v12 c5,-8 12,-12 20,-12 v19 c-12,0 -20,6 -20,17 v19 h-18 Z"/>
  </g>
  <path d="M200.28 101.25 A31.5 31.5 0 1 0 200.28 132.75"
    fill="none" stroke="#31A8FF" stroke-width="17"/>
</svg>"""

LRPASSWORDS_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -5 170 140"
  role="img" aria-label="LrC Password Store">
  <rect x="14" y="30" width="142" height="94" rx="10" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <path d="M52 30v-6C52 10 66 2 85 2s33 8 33 22v6" fill="none"
    stroke="#546E7A" stroke-width="9"/>
  <circle cx="85" cy="70" r="14" fill="#003087"/>
  <path d="M85 81v22" stroke="#003087" stroke-width="10"
    stroke-linecap="round"/>
</svg>"""

ICONS = (
    Icon("user", 35, 425, 80, 125, "<b>User</b>", ("User",), USER_SVG),
    Icon(
        "browser",
        325 - LEFT_COLUMN_SHIFT,
        440,
        65,
        95,
        "<b>Browser</b>",
        ("Browser",),
        CHROME_SVG,
        label_align="right",
        bottom_label_x_offset=25,
    ),
    Icon(
        "dns",
        DNS_JWKS_COLUMN_CENTER_X - 75,
        187.5,
        150,
        150,
        "<b>FGA.com Authoritative<br>DNS</b>",
        ("FGA.com Authoritative", "DNS"),
        SERVER_SVG,
        HOSTING.identifier,
        label_position="top",
        top_label_offset=-6.9,
    ),
    Icon(
        "google-login-endpoint",
        755,
        405,
        170,
        135,
        "<b>FGA Google Login<br>Endpoint</b>",
        ("FGA Google Login", "Endpoint"),
        LOGIN_ENDPOINT_SVG,
        HOSTING.identifier,
        label_position="right",
        label_space=0,
    ),
    Icon(
        "google-jwks-cache",
        780,
        592.5,
        140,
        135,
        "<b>FGA Google JWKS<br>Cache</b>",
        ("FGA Google JWKS", "Cache"),
        JWKS_CACHE_SVG,
        HOSTING.identifier,
    ),
    Icon(
        "session-database",
        755,
        180,
        190,
        165,
        ("<b>FGA Session Database</b><br><i>Key: SHA2-256(token)<br>Value: FGA Session Record</i>"),
        (
            "FGA Session Database",
            "Key: SHA2-256(token)",
            "Value: FGA Session Record",
        ),
        SESSION_DATABASE_SVG,
        HOSTING.identifier,
        label_position="top",
        top_label_offset=-12,
    ),
    Icon(
        "google-jwks-refresh-worker",
        DNS_JWKS_COLUMN_CENTER_X - 70,
        592.5,
        140,
        150,
        ("<b>FGA JWKS Refresh Worker</b><br><i>Maximum 6h</i>"),
        (
            "FGA JWKS Refresh Worker",
            "Maximum 6h",
        ),
        JWKS_REFRESH_WORKER_SVG,
        HOSTING.identifier,
        label_space=45,
        bottom_label_offset=-15,
    ),
    Icon(
        "frontend",
        267.5 - LEFT_COLUMN_SHIFT,
        185.5,
        180,
        137,
        (
            "<b>FGA User UI</b><br><i>JAMstack Static Frontend<br>"
            "HTML · CSS · JS · Images · Etc.</i>"
        ),
        ("FGA User UI", "JAMstack Static Frontend", "HTML · CSS · JS · Images · Etc."),
        FRONTEND_SVG,
        CDN.identifier,
        label_position="top",
        label_space=47,
    ),
    Icon("google", 287.5 - LEFT_COLUMN_SHIFT, 620, 140, 50, "", (), GOOGLE_SVG),
)

EDGES = (
    Edge("user-browser", "user", "browser", target_x=0),
    Edge(
        "browser-dns",
        "browser",
        "dns",
        source_x=32 / 35,
        source_y=3 / 35,
        target_x=0.137,
        target_y=0.963,
    ),
    Edge(
        "browser-frontend",
        "browser",
        "frontend",
        source_x=0.5,
        source_y=0,
        target_x=0.5,
        target_y=1,
    ),
    Edge(
        "browser-google",
        "browser",
        "google",
        source_x=0.5,
        source_y=1,
        target_x=0.5,
        target_y=0,
    ),
    Edge(
        "browser-google-login",
        "browser",
        "google-login-endpoint",
        source_x=1,
        source_y=0.5,
        target_x=0,
        target_y=0.5,
    ),
    Edge(
        "login-jwks-cache",
        "google-login-endpoint",
        "google-jwks-cache",
        source_x=19 / 34,
        source_y=0.95,
        target_x=0.5,
        target_y=0,
    ),
    Edge(
        "login-session-database",
        "google-login-endpoint",
        "session-database",
        source_x=19 / 34,
        source_y=0.05,
        target_x=0.5,
        target_y=1,
    ),
    Edge(
        "jwks-worker-google",
        "google-jwks-refresh-worker",
        "google",
        source_x=JWKS_REFRESH_WORKER_LEFT_X_FRACTION,
        source_y=0.5,
        target_x=GOOGLE_REFRESH_TARGET_X_FRACTION,
        target_y=0.5,
    ),
    Edge(
        "jwks-worker-cache",
        "google-jwks-refresh-worker",
        "google-jwks-cache",
        source_x=JWKS_REFRESH_WORKER_RIGHT_X_FRACTION,
        source_y=0.5,
        target_x=0,
        target_y=0.5,
        bidirectional=False,
    ),
)

ICON_BY_ID = {icon.identifier: icon for icon in ICONS}

FLOW_STEPS = (
    FlowStep(1, "user-browser", 198.707, 444.5, ("User opens FGA.com", "in Browser.")),
    FlowStep(2, "browser-dns", 410.594, 399.59, ("Browser resolves FGA.com.",)),
    FlowStep(
        3,
        "browser-frontend",
        324.914,
        371.25,
        ("Browser retrieves landing", "page static assets."),
    ),
    FlowStep(4, "user-browser", 198.707, 480.5, ("User clicks Login.",)),
    FlowStep(
        5,
        "browser-google",
        324.914,
        552.5,
        ("Browser follows Google", "sign-in redirect."),
    ),
    FlowStep(
        6,
        "browser-google-login",
        DNS_JWKS_COLUMN_CENTER_X - 10,
        444.5,
        (
            "Google redirect UX:",
            "Browser POSTs credential +",
            "CSRF token to the FGA",
            "Google Login Endpoint.",
        ),
    ),
    FlowStep(
        7,
        "browser-google-login",
        875,
        395,
        (
            "Login Endpoint verifies CSRF:",
            "POST-cookie g_csrf_token ==",
            "request-body g_csrf_token.",
        ),
    ),
    FlowStep(
        8,
        "login-jwks-cache",
        840,
        548.875,
        ("Login Endpoint reads current", "Google JWKS from FGA cache."),
    ),
    FlowStep(
        9,
        "browser-google-login",
        905,
        395,
        (
            "Login Endpoint performs",
            "current Google-required JWT",
            "validation: trusted alg/key,",
            "signature, iss, aud, and",
            "time claims.",
        ),
    ),
    FlowStep(
        10,
        "browser-google-login",
        935,
        395,
        ("Login Endpoint generates", "256-bit opaque token with", "CSPRNG."),
    ),
    FlowStep(
        11,
        "login-session-database",
        840,
        372,
        (
            "Endpoint maps (iss, sub) to",
            "fgaUserId; atomically stores",
            "SHA2-256(token) session +",
            "sanitized login audit.",
        ),
    ),
    FlowStep(
        12,
        "browser-google-login",
        DNS_JWKS_COLUMN_CENTER_X - 10,
        480.5,
        (
            "Login Endpoint sets",
            "__Host-… cookie: Secure,",
            "HttpOnly, Path=/,",
            "SameSite=Strict, no Domain,",
            "Max-Age=86400.",
        ),
    ),
)

PAGE_1 = DiagramPage(
    identifier="browser-session",
    tab_name="1 · Browser Session",
    title="FlickrGroupAddr Browser Auth w/ Backend",
    date="2026-08-30",
    description=(
        "The authoritative simplified happy-path interaction map for a user, browser, "
        "authoritative DNS, static frontend, Google authentication, Google Login "
        "Endpoint, asynchronously refreshed JWKS cache, and server-side session "
        "persistence."
    ),
    legend_heading="Authentication Flow",
    authority=(
        "Authority: Normative happy-path interaction map (ADR 0039, ADR 0041); omitted "
        "failure/lifecycle/provider detail stays with controlling sources; session "
        "creation + login audit commit atomically; proactive JWKS refresh is outside the "
        "numbered login sequence; failed logins are audited when possible."
    ),
    svg_stem="clean-room-authentication",
    boundaries=BOUNDARIES,
    icons=ICONS,
    edges=EDGES,
    flow_steps=FLOW_STEPS,
    legend_width=259,
    authority_width=1339,
)

P2_HOSTING = Boundary(
    "p2-hosting-boundary",
    510,
    90,
    539,
    690,
    "FGA Backend Hosting Platform <i>(Provider Undecided)</i>",
    ("FGA Backend Hosting Platform (Provider Undecided)",),
)

P2_WORKSTATION = Boundary(
    "p2-workstation-boundary",
    120,
    465,
    360,
    315,
    "",
    (),
)

P2_BOUNDARIES = (P2_HOSTING, P2_WORKSTATION)

P2_ICONS = (
    Icon(
        "p2-user",
        35,
        325,
        80,
        125,
        "<b>User</b>",
        ("User",),
        USER_SVG,
        label_position="top",
        top_label_offset=8,
    ),
    Icon(
        "p2-browser",
        210,
        340,
        65,
        95,
        "<b>Browser</b>",
        ("Browser",),
        CHROME_SVG,
        label_position="top",
        top_label_offset=-7,
    ),
    Icon(
        "p2-installation-endpoint",
        623,
        335,
        180,
        135,
        "<b>FGA Plugin Code API</b><br><i>GET · POST · PATCH</i>",
        ("FGA Plugin Code API", "GET · POST · PATCH"),
        LOGIN_ENDPOINT_SVG,
        P2_HOSTING.identifier,
        label_position="top-left",
        label_space=0,
    ),
    Icon(
        "p2-session-database",
        629,
        150,
        190,
        110,
        "<b>FGA Session Database</b><br><i>Key: SHA2-256(token)<br>Value: FGA Session Record</i>",
        (
            "FGA Session Database",
            "Key: SHA2-256(token)",
            "Value: FGA Session Record",
        ),
        SESSION_DATABASE_SVG,
        P2_HOSTING.identifier,
        label_position="right",
        label_space=0,
        right_label_inset=28,
    ),
    Icon(
        "p2-installation-database",
        629,
        550,
        190,
        175,
        (
            "<b>FGA Installation Records</b><br>"
            "<i>SHA2-256(Plugin Code)<br>Installation + lrc_plugin Class</i>"
        ),
        (
            "FGA Installation Records",
            "SHA2-256(Plugin Code)",
            "Installation + lrc_plugin Class",
        ),
        SESSION_DATABASE_SVG,
        P2_HOSTING.identifier,
        bottom_label_offset=-6,
    ),
    Icon(
        "p2-audit-log",
        849,
        543,
        170,
        175,
        (
            "<b>FGA Append-Only Audit Log</b><br>"
            "<i>audit_events · Same FGA Database<br>GET · POST · PATCH</i>"
        ),
        (
            "FGA Append-Only Audit Log",
            "audit_events · Same FGA Database",
            "GET · POST · PATCH",
        ),
        SESSION_DATABASE_SVG,
        P2_HOSTING.identifier,
        bottom_label_offset=1,
    ),
    Icon(
        "p2-lrc-mark",
        380,
        480,
        85,
        83,
        "",
        (),
        LIGHTROOM_CLASSIC_SVG,
        P2_WORKSTATION.identifier,
        label_space=0,
    ),
    Icon(
        "p2-plugin",
        140,
        570,
        135,
        90,
        "<b>FGA LrC plug-in</b>",
        ("FGA LrC plug-in",),
        PLUGIN_SVG,
        P2_WORKSTATION.identifier,
        label_position="right",
        label_space=0,
        right_label_inset=18,
    ),
    Icon(
        "p2-lrpasswords",
        140,
        705,
        135,
        65,
        "<b>LrC Password Store</b>",
        ("LrC Password Store",),
        LRPASSWORDS_SVG,
        P2_WORKSTATION.identifier,
        label_position="right",
        label_space=0,
        right_label_inset=33,
    ),
)

P2_EDGES = (
    Edge(
        "p2-user-browser",
        "p2-user",
        "p2-browser",
        target_x=0,
        orthogonal=True,
    ),
    Edge(
        "p2-browser-installation-endpoint",
        "p2-browser",
        "p2-installation-endpoint",
        source_x=1,
        target_x=0,
        orthogonal=True,
    ),
    Edge(
        "p2-endpoint-session-database",
        "p2-installation-endpoint",
        "p2-session-database",
        source_x=101 / 180,
        source_y=0.022,
        target_x=0.5,
        target_y=1,
        orthogonal=True,
    ),
    Edge(
        "p2-endpoint-installation-database",
        "p2-installation-endpoint",
        "p2-installation-database",
        source_x=101 / 180,
        source_y=0.978,
        target_x=0.5,
        target_y=-0.034,
        orthogonal=True,
    ),
    Edge(
        "p2-endpoint-audit-log",
        "p2-installation-endpoint",
        "p2-audit-log",
        source_x=43 / 45,
        source_y=0.5,
        target_x=0.5,
        target_y=0.014,
        bidirectional=False,
        orthogonal=True,
    ),
    Edge(
        "p2-user-plugin",
        "p2-user",
        "p2-plugin",
        source_x=0.5,
        source_y=18 / 19,
        target_x=17 / 135,
        target_y=0.5,
        bidirectional=False,
        orthogonal=True,
        svg_target_x_offset=-9,
        vertical_first=True,
    ),
    Edge(
        "p2-plugin-lrpasswords",
        "p2-plugin",
        "p2-lrpasswords",
        source_x=0.5,
        source_y=43 / 45,
        target_x=0.5,
        target_y=0,
        bidirectional=False,
        orthogonal=True,
        drawio_target_y=-6 / 65,
        svg_target_y_offset=-6,
    ),
)

P2_FLOW_STEPS = (
    FlowStep(1, "p2-user-browser", 153, 378, ("User opens FGA User UI.",)),
    FlowStep(
        2,
        "p2-browser-installation-endpoint",
        324,
        392,
        (
            "FGA User UI JavaScript calls",
            "GET /api/v001/plugin-codes.",
            "Browser attaches the HttpOnly",
            "__Host-… cookie; JavaScript",
            "cannot read it.",
        ),
    ),
    FlowStep(
        3,
        "p2-browser-installation-endpoint",
        753,
        323,
        ("Plugin Code API computes", "SHA2-256(session token)."),
    ),
    FlowStep(
        4,
        "p2-endpoint-session-database",
        699,
        293,
        ("API requests session status", "using that SHA2-256 digest."),
    ),
    FlowStep(
        5,
        "p2-endpoint-session-database",
        729,
        293,
        ("DB returns active, unexpired", "session with fgaUserId."),
    ),
    FlowStep(
        6,
        "p2-endpoint-installation-database",
        699,
        480,
        ("API queries owned Plugin Code", "page by fgaUserId."),
    ),
    FlowStep(
        7,
        "p2-endpoint-installation-database",
        729,
        480,
        ("Records return metadata page.",),
    ),
    FlowStep(
        8,
        "p2-endpoint-audit-log",
        859,
        392,
        ("API appends list-read audit.",),
    ),
    FlowStep(
        9,
        "p2-browser-installation-endpoint",
        369,
        392,
        ("GET returns metadata;", "JavaScript renders FGA User UI."),
    ),
    FlowStep(
        10,
        "p2-user-browser",
        138,
        408,
        ("User selects Create", "Plugin Code."),
    ),
    FlowStep(
        11,
        "p2-browser-installation-endpoint",
        414,
        392,
        (
            "Browser POSTs",
            "/api/v001/plugin-codes",
            "with cookie, exact origin,",
            "CSRF, and recent-auth proof.",
        ),
    ),
    FlowStep(
        12,
        "p2-browser-installation-endpoint",
        783,
        323,
        (
            "API generates 32 CSPRNG octets;",
            "encodes canonical 13-group",
            "Crockford Base32 Plugin Code.",
        ),
    ),
    FlowStep(
        13,
        "p2-endpoint-installation-database",
        714,
        505,
        (
            "API atomically stores Plugin Code",
            "record + create audit event;",
            "never stores plaintext.",
        ),
    ),
    FlowStep(
        14,
        "p2-browser-installation-endpoint",
        459,
        392,
        ("API returns Plugin Code", "exactly once with no-store."),
    ),
    FlowStep(
        15,
        "p2-user-browser",
        168,
        408,
        ("FGA User UI displays clear-text", "canonical Plugin Code once."),
    ),
    FlowStep(
        16,
        "p2-user-plugin",
        65,
        495,
        (
            "User copies and pastes into",
            "clear-text FGA LrC plug-in input;",
            "compares identical grouped values.",
        ),
    ),
    FlowStep(
        17,
        "p2-plugin-lrpasswords",
        183,
        659,
        (
            "FGA LrC plug-in strictly validates,",
            "stores in LrC Password Store;",
            "clears field.",
        ),
    ),
)

PAGE_2 = DiagramPage(
    identifier="plugin-code-transfer",
    tab_name="2 · Plugin Code Generation",
    title="FlickrGroupAddr Plugin Code Generation",
    date="2026-09-03",
    description=(
        "The authoritative simplified happy-path interaction map for an authenticated "
        "browser listing and auditing its Plugin Code records, creating one canonical "
        "grouped FGA installation credential with an atomic audit event, and visually "
        "comparing it on the same workstation before LrC Password Store persistence."
    ),
    legend_heading="Plugin Code Transfer",
    authority=(
        "Authority: Normative happy-path interaction map (ADR 0006, ADR 0039, ADR 0040, "
        "ADR 0041, ADR 0044); controlling sources own omitted failures, recent authentication, "
        "revocation, and later Bearer verification."
    ),
    svg_stem="clean-room-authentication-plugin-code-transfer",
    boundaries=P2_BOUNDARIES,
    icons=P2_ICONS,
    edges=P2_EDGES,
    flow_steps=P2_FLOW_STEPS,
    legend_row_padding=0,
    legend_height=710,
    legend_min_row_height=16,
    legend_x=1079,
    legend_width=290,
    legend_4k_inset_pixels=1.5,
)

P3_RENDERING_ENGINE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 140"
  role="img" aria-label="LrC Rendering Engine">
  <rect x="10" y="10" width="160" height="120" rx="9" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <rect x="28" y="28" width="124" height="67" rx="5" fill="#CFD8DC"
    stroke="#546E7A" stroke-width="5"/>
  <circle cx="57" cy="50" r="10" fill="#31A8FF"/>
  <path d="m35 87 31-28 23 20 19-15 37 23" fill="none" stroke="#003087"
    stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="55" y="105" width="70" height="17" rx="5" fill="#003087"/>
  <text x="90" y="118" fill="#FFFFFF" font-family="Arial, sans-serif"
    font-size="13" font-weight="700" text-anchor="middle">PNG</text>
</svg>"""

P3_GROUP_SUBMISSION_WORKER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 284 180"
  role="img" aria-label="FGA Group-Submission Worker">
  <g fill="#546E7A" stroke="#1A1A1A" stroke-width="4">
    <rect x="16" y="10" width="252" height="45" rx="7"/>
    <rect x="16" y="68" width="252" height="45" rx="7"/>
    <rect x="16" y="126" width="252" height="45" rx="7"/>
  </g>
  <g fill="#FFFFFF">
    <circle cx="38" cy="32.5" r="6"/>
    <circle cx="38" cy="90.5" r="6"/>
    <circle cx="38" cy="148.5" r="6"/>
  </g>
  <g stroke="#FFFFFF" stroke-width="5" stroke-linecap="round">
    <path d="M58 32.5h186"/>
    <path d="M58 90.5h186"/>
    <path d="M58 148.5h186"/>
  </g>
</svg>"""

P3_FLICKR_UPLOAD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 140"
  role="img" aria-label="Flickr Upload API">
  <rect x="10" y="10" width="160" height="120" rx="10" fill="#FFFFFF"
    stroke="#1A1A1A" stroke-width="6"/>
  <rect x="27" y="28" width="126" height="82" rx="6" fill="#CFD8DC"
    stroke="#546E7A" stroke-width="5"/>
  <circle cx="57" cy="52" r="10" fill="#FF0084"/>
  <path d="m34 101 32-31 24 21 19-16 37 26" fill="none" stroke="#0063DC"
    stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M90 119V73m-17 17 17-17 17 17" fill="none" stroke="#003087"
    stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

# Source: https://commons.wikimedia.org/wiki/File:Flickr_wordmark.svg
# Wikimedia Commons marks this text logo public-domain for copyright and
# separately trademarked. ADR 0042 records Terry's explicit trademark-risk
# override for this hobby-project architecture diagram.
FLICKR_WORDMARK_SVG = """<svg xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 515 155.72">
  <g fill="#0063DB">
    <path d="M20.591 73.837H0V48.486h21.173V42.05
      C21.173 10.865 35.353 0 63.324 0c7.576 0 13.403 1.207 17.87 2.013
      L79.058 26.96c-2.913-1.006-5.827-1.61-11.071-1.61
      c-8.935 0-12.432 6.438-12.432 16.7v6.437h24.863v25.351H55.555
      v79.467H20.591V73.837Z"/>
    <path d="M98.675 2.415h34.964v150.889H98.675z
      M163.552 4.829h34.965v26.557h-34.965z
      M163.552 48.486h34.965v104.817h-34.965z"/>
    <path d="M303.604 78.462c-6.41-4.021-12.82-5.833-21.173-5.833
      c-15.151 0-26.806 10.864-26.806 28.972
      c0 16.699 13.598 27.561 28.749 27.561
      c7.965 0 15.93-1.809 21.756-5.029l.777 26.959
      c-8.742 3.02-19.23 4.629-28.554 4.629
      c-33.412 0-58.857-20.119-58.857-54.723
      c0-34.806 25.445-54.924 58.857-54.924
      c10.49 0 19.812 1.811 27.777 5.834l-2.526 26.554Z
      M321.477 2.415h34.963v90.133h.389l29.136-44.062h38.266
      l-35.158 48.083 38.072 56.735h-42.346l-27.97-51.905h-.389
      v51.905h-34.963V2.415Z"/>
  </g>
  <path fill="#FF0084" d="M512.417 77.456
    c-3.885-1.205-7.771-1.205-11.848-1.205
    c-16.316 0-25.447 12.271-25.447 32.793v44.26h-34.963V48.486h31.855
    V67.8h.389c6.02-13.279 14.762-21.728 29.914-21.728
    c4.076 0 8.35.603 11.85 1.206l-1.75 30.178Z"/>
</svg>"""

# Several tab-three SVGs preserve aspect ratio inside deliberately uniform icon
# cells. These attachment fractions terminate connectors roughly three drawing
# units from the nearest visible glyph pixel rather than at transparent cell
# edges.
P3_USER_VISIBLE_RIGHT_X_FRACTION = 0.91
P3_PLUGIN_VISIBLE_LEFT_X_FRACTION = 0.123
P3_PLUGIN_VISIBLE_RIGHT_X_FRACTION = 0.877
P3_PLUGIN_VISIBLE_BOTTOM_Y_FRACTION = 0.98
P3_PASSWORD_STORE_VISIBLE_RIGHT_X_FRACTION = 0.83
P3_RENDERER_VISIBLE_LEFT_X_FRACTION = 0.15
P3_API_VISIBLE_LEFT_X_FRACTION = 0.16
P3_API_VISIBLE_RIGHT_X_FRACTION = 0.95
P3_ARROW_GLYPH_GAP = 3
# The workstation and backend boundaries share this visual centerline. The
# password-store and renderer glyphs have different painted widths, so offset
# the three component columns slightly left within the boundary: this keeps
# their centers equidistant while giving the two outer painted edges identical
# whitespace. The backend components reuse those exact column centers.
P3_BOUNDARY_CENTER_X = 429
P3_FGA_BOUNDARY_X = 144
P3_FGA_BOUNDARY_WIDTH = 570
P3_FLICKR_BOUNDARY_X = 744
P3_FLICKR_BOUNDARY_WIDTH = 316
P3_BOTTOM_LABEL_IMAGE_SCALE = (105 - 30) / 140
P3_PASSWORD_STORE_PAINTED_HALF_WIDTH = (142 + 6) * P3_BOTTOM_LABEL_IMAGE_SCALE / 2
P3_RENDERER_PAINTED_HALF_WIDTH = (160 + 6) * P3_BOTTOM_LABEL_IMAGE_SCALE / 2
P3_CENTER_COLUMN_X = (
    P3_BOUNDARY_CENTER_X
    + (P3_PASSWORD_STORE_PAINTED_HALF_WIDTH - P3_RENDERER_PAINTED_HALF_WIDTH) / 2
)
P3_PLUGIN_CELL_X = P3_CENTER_COLUMN_X - 150 / 2
P3_PLUGIN_PAINTED_LEFT_X = P3_PLUGIN_CELL_X + P3_PLUGIN_VISIBLE_LEFT_X_FRACTION * 150
P3_OUTER_COLUMN_OFFSET_X = 170
P3_LEFT_COLUMN_CENTER_X = P3_CENTER_COLUMN_X - P3_OUTER_COLUMN_OFFSET_X
P3_RIGHT_COLUMN_CENTER_X = P3_CENTER_COLUMN_X + P3_OUTER_COLUMN_OFFSET_X
P3_CENTER_COLUMN_SHIFT_X = P3_CENTER_COLUMN_X - P3_BOUNDARY_CENTER_X
P3_RIGHT_COLUMN_SHIFT_X = P3_RIGHT_COLUMN_CENTER_X - (534 + 135 / 2)
# The endpoint SVG's visible rectangle is right of its cell center because the
# incoming-arrow artwork occupies the left side. Offset the whole cell left,
# then anchor the plugin connector on the rectangle's visual center.
P3_API_IMAGE_SCALE = 115 / 135
P3_API_IMAGE_X_PADDING = (170 - 190 * P3_API_IMAGE_SCALE) / 2
P3_API_RECTANGLE_CENTER_WITHIN_CELL = P3_API_IMAGE_X_PADDING + (34 + 145 / 2) * P3_API_IMAGE_SCALE
P3_API_CELL_X = P3_CENTER_COLUMN_X - P3_API_RECTANGLE_CENTER_WITHIN_CELL
P3_API_RECTANGLE_CENTER_X_FRACTION = P3_API_RECTANGLE_CENTER_WITHIN_CELL / 170
P3_API_RECTANGLE_TARGET_TOP_Y_FRACTION = (
    (12 - 6 / 2) * P3_API_IMAGE_SCALE - P3_ARROW_GLYPH_GAP
) / 115
P3_API_ARROW_STEM_PAINTED_LEFT_WITHIN_CELL = (
    P3_API_IMAGE_X_PADDING + (3 - 9 / 2) * P3_API_IMAGE_SCALE
)
P3_API_ARROW_STEM_TARGET_LEFT_X_FRACTION = (
    P3_API_ARROW_STEM_PAINTED_LEFT_WITHIN_CELL - P3_ARROW_GLYPH_GAP
) / 170
P3_API_ARROW_STEM_CENTER_Y_FRACTION = 67 / 135
P3_API_DATABASE_BADGE_X = (
    P3_LEFT_COLUMN_CENTER_X + P3_API_CELL_X + P3_API_ARROW_STEM_TARGET_LEFT_X_FRACTION * 170
) / 2 - 10
P3_DATABASE_VISIBLE_RIGHT_X_FRACTION = 0.83
P3_DATABASE_VISIBLE_TOP_Y_FRACTION = -0.0375
P3_WORKER_IMAGE_SCALE = 70 / 180
P3_WORKER_PAINTED_HALF_WIDTH = (252 + 4) * P3_WORKER_IMAGE_SCALE / 2
P3_WORKER_TARGET_LEFT_X_FRACTION = (
    130 / 2 - P3_WORKER_PAINTED_HALF_WIDTH - P3_ARROW_GLYPH_GAP
) / 130
P3_WORKER_TARGET_RIGHT_X_FRACTION = (
    130 / 2 + P3_WORKER_PAINTED_HALF_WIDTH + P3_ARROW_GLYPH_GAP
) / 130
P3_UPLOAD_VISIBLE_LEFT_X_FRACTION = 0.13
P3_REST_VISIBLE_LEFT_X_FRACTION = 0.27
P3_REST_IMAGE_SCALE = 95 / 180
P3_REST_TARGET_BOTTOM_Y_FRACTION = ((171 + 4 / 2) * P3_REST_IMAGE_SCALE + P3_ARROW_GLYPH_GAP) / 95

P3_WORKSTATION = Boundary(
    "p3-workstation-boundary",
    P3_FGA_BOUNDARY_X,
    90,
    P3_FGA_BOUNDARY_WIDTH,
    350,
    "",
    (),
    label_align="left",
)

P3_HOSTING = Boundary(
    "p3-hosting-boundary",
    P3_FGA_BOUNDARY_X,
    460,
    P3_FGA_BOUNDARY_WIDTH,
    320,
    "FGA Backend Hosting Platform <i>(Provider Undecided)</i>",
    ("FGA Backend Hosting Platform", "(Provider Undecided)"),
    label_align="left",
)

P3_FLICKR = Boundary(
    "p3-flickr-boundary",
    P3_FLICKR_BOUNDARY_X,
    90,
    P3_FLICKR_BOUNDARY_WIDTH,
    690,
    "",
    (),
)

P3_BOUNDARIES = (P3_WORKSTATION, P3_HOSTING, P3_FLICKR)

P3_ICONS = (
    Icon(
        "p3-user",
        35,
        205,
        80,
        125,
        "<b>User</b>",
        ("User",),
        USER_SVG,
    ),
    Icon(
        "p3-lrc-mark",
        P3_FGA_BOUNDARY_X + 12,
        100,
        65,
        63,
        "",
        (),
        LIGHTROOM_CLASSIC_SVG,
        P3_WORKSTATION.identifier,
        label_space=0,
    ),
    Icon(
        "p3-plugin",
        P3_PLUGIN_CELL_X,
        165,
        150,
        135,
        "<b>FGA LrC Plugin</b>",
        ("FGA LrC Plugin",),
        PLUGIN_SVG,
        P3_WORKSTATION.identifier,
        label_position="top",
        label_space=40,
        top_label_offset=21,
    ),
    Icon(
        "p3-lrpasswords",
        P3_LEFT_COLUMN_CENTER_X - 130 / 2,
        315,
        130,
        105,
        "<b>LrC Password Store</b>",
        ("LrC Password Store",),
        LRPASSWORDS_SVG,
        P3_WORKSTATION.identifier,
        bottom_label_offset=-6,
    ),
    Icon(
        "p3-rendering-engine",
        P3_RIGHT_COLUMN_CENTER_X - 135 / 2,
        315,
        135,
        105,
        "<b>LrC Rendering Engine</b>",
        ("LrC Rendering Engine",),
        P3_RENDERING_ENGINE_SVG,
        P3_WORKSTATION.identifier,
        bottom_label_offset=-6,
    ),
    Icon(
        "p3-api-backend",
        P3_API_CELL_X,
        520,
        170,
        115,
        "<b>FGA API Backend</b>",
        ("FGA API Backend",),
        LOGIN_ENDPOINT_SVG,
        P3_HOSTING.identifier,
        label_position="top-right",
        label_space=0,
    ),
    Icon(
        "p3-database",
        P3_LEFT_COLUMN_CENTER_X - 160 / 2,
        645,
        160,
        110,
        "<b>FGA Database</b>",
        ("FGA Database",),
        SESSION_DATABASE_SVG,
        P3_HOSTING.identifier,
    ),
    Icon(
        "p3-group-worker",
        P3_RIGHT_COLUMN_CENTER_X - 130 / 2,
        650,
        130,
        100,
        "<b>FGA Group-Submission<br>Worker</b>",
        ("FGA Group-Submission", "Worker"),
        P3_GROUP_SUBMISSION_WORKER_SVG,
        P3_HOSTING.identifier,
    ),
    Icon(
        "p3-flickr-wordmark",
        864,
        102,
        90,
        28,
        "",
        (),
        FLICKR_WORDMARK_SVG,
        P3_FLICKR.identifier,
        label_space=0,
    ),
    Icon(
        "p3-upload-api",
        800,
        205,
        160,
        125,
        "<b>Flickr Upload API</b><br><i>up.flickr.com</i>",
        ("Flickr Upload API", "up.flickr.com"),
        P3_FLICKR_UPLOAD_SVG,
        P3_FLICKR.identifier,
        label_position="right",
        right_label_inset=30,
        center_right_label_on_image=True,
    ),
    Icon(
        "p3-rest-api",
        790,
        539.5,
        180,
        125,
        "<b>Flickr REST API</b><br><i>www.flickr.com</i>",
        ("Flickr REST API", "www.flickr.com"),
        SERVER_SVG,
        P3_FLICKR.identifier,
        label_position="right",
        right_label_inset=57,
        center_right_label_on_image=True,
    ),
)

P3_EDGES = (
    Edge(
        "p3-user-plugin",
        "p3-user",
        "p3-plugin",
        source_x=P3_USER_VISIBLE_RIGHT_X_FRACTION,
        target_x=P3_PLUGIN_VISIBLE_LEFT_X_FRACTION,
        bidirectional=False,
        orthogonal=True,
    ),
    Edge(
        "p3-store-plugin",
        "p3-lrpasswords",
        "p3-plugin",
        source_x=P3_PASSWORD_STORE_VISIBLE_RIGHT_X_FRACTION,
        source_y=0.23,
        target_x=P3_PLUGIN_VISIBLE_LEFT_X_FRACTION,
        target_y=P3_PLUGIN_VISIBLE_BOTTOM_Y_FRACTION,
        bidirectional=False,
    ),
    Edge(
        "p3-plugin-rendering-engine",
        "p3-plugin",
        "p3-rendering-engine",
        source_x=P3_PLUGIN_VISIBLE_RIGHT_X_FRACTION,
        source_y=P3_PLUGIN_VISIBLE_BOTTOM_Y_FRACTION,
        target_x=P3_RENDERER_VISIBLE_LEFT_X_FRACTION,
        target_y=0.01,
    ),
    Edge(
        "p3-plugin-api-backend",
        "p3-plugin",
        "p3-api-backend",
        source_x=0.5,
        source_y=P3_PLUGIN_VISIBLE_BOTTOM_Y_FRACTION,
        target_x=P3_API_RECTANGLE_CENTER_X_FRACTION,
        target_y=P3_API_RECTANGLE_TARGET_TOP_Y_FRACTION,
        orthogonal=True,
    ),
    Edge(
        "p3-plugin-upload-api",
        "p3-plugin",
        "p3-upload-api",
        source_x=P3_PLUGIN_VISIBLE_RIGHT_X_FRACTION,
        source_y=0.5,
        target_x=P3_UPLOAD_VISIBLE_LEFT_X_FRACTION,
        target_y=0.5,
        orthogonal=True,
    ),
    Edge(
        "p3-api-database",
        "p3-database",
        "p3-api-backend",
        source_x=0.5,
        source_y=P3_DATABASE_VISIBLE_TOP_Y_FRACTION,
        target_x=P3_API_ARROW_STEM_TARGET_LEFT_X_FRACTION,
        target_y=P3_API_ARROW_STEM_CENTER_Y_FRACTION,
        orthogonal=True,
        vertical_first=True,
    ),
    Edge(
        "p3-api-rest-api",
        "p3-api-backend",
        "p3-rest-api",
        source_x=P3_API_VISIBLE_RIGHT_X_FRACTION,
        source_y=0.5,
        target_x=P3_REST_VISIBLE_LEFT_X_FRACTION,
        target_y=0.4,
        orthogonal=True,
    ),
    Edge(
        "p3-database-group-worker",
        "p3-database",
        "p3-group-worker",
        source_x=P3_DATABASE_VISIBLE_RIGHT_X_FRACTION,
        source_y=0.5,
        target_x=P3_WORKER_TARGET_LEFT_X_FRACTION,
        target_y=0.5,
        orthogonal=True,
    ),
    Edge(
        "p3-group-worker-rest-api",
        "p3-group-worker",
        "p3-rest-api",
        source_x=P3_WORKER_TARGET_RIGHT_X_FRACTION,
        source_y=0.5,
        target_x=0.5,
        target_y=P3_REST_TARGET_BOTTOM_Y_FRACTION,
        orthogonal=True,
        waypoints=((880, 685),),
    ),
)

P3_API_BADGE_STACK_X = P3_CENTER_COLUMN_X + 10
P3_API_BADGE_STACK_TOP_Y = 316
P3_API_BADGE_STACK_STEP_Y = 24
P3_USER_BADGE_ROW_Y = 234.5
P3_USER_BADGE_ROW_STEP_X = 42
P3_USER_BADGE_GROUP_WIDTH = 20 + 3 * P3_USER_BADGE_ROW_STEP_X
P3_USER_BADGE_ROW_START_X = (
    P3_WORKSTATION.x + P3_PLUGIN_PAINTED_LEFT_X - P3_USER_BADGE_GROUP_WIDTH
) / 2
P3_FLICKR_BADGE_X = P3_FLICKR.x + 21

P3_FLOW_STEPS = (
    FlowStep(
        1,
        "p3-user-plugin",
        P3_USER_BADGE_ROW_START_X,
        P3_USER_BADGE_ROW_Y - 10,
        (
            "User chooses Create Album…;",
            "empty Album remains local-only.",
        ),
    ),
    FlowStep(
        2,
        "p3-user-plugin",
        P3_USER_BADGE_ROW_START_X + P3_USER_BADGE_ROW_STEP_X,
        P3_USER_BADGE_ROW_Y - 10,
        ("User adds one or more photos", "to the Album."),
    ),
    FlowStep(
        3,
        "p3-store-plugin",
        327 + P3_CENTER_COLUMN_SHIFT_X,
        305,
        (
            "FGA LrC plugin retrieves",
            "Plugin Code from LrC Password Store.",
        ),
    ),
    FlowStep(
        4,
        "p3-plugin-api-backend",
        P3_API_BADGE_STACK_X,
        P3_API_BADGE_STACK_TOP_Y,
        ("GET /api/v001/installations/current;", "Bearer Plugin Code."),
    ),
    FlowStep(
        5,
        "p3-api-database",
        P3_API_DATABASE_BADGE_X,
        545.074,
        (
            "FGA API backend computes",
            "SHA2-256; verifies active",
            "lrc_plugin; returns Connected.",
        ),
    ),
    FlowStep(
        6,
        "p3-plugin-api-backend",
        P3_API_BADGE_STACK_X,
        P3_API_BADGE_STACK_TOP_Y + P3_API_BADGE_STACK_STEP_Y,
        ("Plugin loads bounded writable-", "group snapshot; Bearer attached."),
    ),
    FlowStep(
        7,
        "p3-user-plugin",
        P3_USER_BADGE_ROW_START_X + 2 * P3_USER_BADGE_ROW_STEP_X,
        P3_USER_BADGE_ROW_Y - 10,
        ("User selects zero or more", "add-only groups per photo."),
    ),
    FlowStep(
        8,
        "p3-user-plugin",
        P3_USER_BADGE_ROW_START_X + 3 * P3_USER_BADGE_ROW_STEP_X,
        P3_USER_BADGE_ROW_Y - 10,
        ("User chooses Album Publish Now;", "runtime supplies pending photos."),
    ),
    FlowStep(
        9,
        "p3-plugin-rendering-engine",
        510 + (P3_CENTER_COLUMN_SHIFT_X + P3_RIGHT_COLUMN_SHIFT_X) / 2,
        297,
        (
            "LrC rendering engine renders PNG;",
            "FGA LrC plugin waits; size-preflights.",
        ),
    ),
    FlowStep(
        10,
        "p3-plugin-api-backend",
        P3_API_BADGE_STACK_X,
        P3_API_BADGE_STACK_TOP_Y + 2 * P3_API_BADGE_STACK_STEP_Y,
        (
            "Plugin POSTs Bearer + allowlisted",
            "upload metadata; no image bytes.",
        ),
    ),
    FlowStep(
        11,
        "p3-api-database",
        P3_API_DATABASE_BADGE_X,
        567.074,
        (
            "FGA API backend commits auth;",
            "signed envelope: no-store, memory-only.",
        ),
    ),
    FlowStep(
        12,
        "p3-plugin-upload-api",
        P3_FLICKR_BADGE_X,
        224.5,
        ("Plugin streams PNG directly to", "Flickr Upload API."),
    ),
    FlowStep(
        13,
        "p3-plugin-upload-api",
        P3_FLICKR_BADGE_X,
        260.5,
        (
            "Flickr returns photo ID; plugin",
            "records recovery + catalog remote ID.",
        ),
    ),
    FlowStep(
        14,
        "p3-plugin-api-backend",
        P3_API_BADGE_STACK_X,
        P3_API_BADGE_STACK_TOP_Y + 3 * P3_API_BADGE_STACK_STEP_Y,
        ("Plugin PUTs photo binding with", "photo ID and Bearer."),
    ),
    FlowStep(
        15,
        "p3-api-rest-api",
        P3_FLICKR_BADGE_X,
        568,
        (
            "FGA API backend verifies via getInfo;",
            "commits binding; returns ID + revision.",
        ),
    ),
    FlowStep(
        16,
        "p3-plugin-api-backend",
        P3_API_BADGE_STACK_X,
        P3_API_BADGE_STACK_TOP_Y + 4 * P3_API_BADGE_STACK_STEP_Y,
        ("Plugin POSTs group IDs with", "binding ID/rev + Bearer."),
    ),
    FlowStep(
        17,
        "p3-api-database",
        P3_API_DATABASE_BADGE_X,
        589.074,
        (
            "FGA API backend atomically commits",
            "group intents; 202 = durable handoff.",
        ),
    ),
    FlowStep(
        18,
        "p3-group-worker-rest-api",
        P3_FLICKR_BADGE_X,
        657,
        (
            "Worker calls fresh getAllContexts;",
            "if absent, calls groups.getInfo;",
            "records current moderation.",
        ),
    ),
    FlowStep(
        19,
        "p3-group-worker-rest-api",
        P3_FLICKR_BADGE_X,
        693,
        (
            "Worker marks dispatch, starts",
            "pools.add <1 s after getInfo;",
            "commits result or polite block.",
        ),
    ),
)

PAGE_3 = DiagramPage(
    identifier="publish-png-groups",
    tab_name="3 · Publish PNG + Groups",
    title="FlickrGroupAddr Publish PNG + Add to Groups",
    date="2026-08-31",
    description=(
        "The authoritative simplified happy-path interaction map for local FGA Album "
        "setup and group selection, FGA LrC plugin authentication, Lightroom Classic "
        "PNG rendering, direct Flickr upload, verified photo binding, and durable "
        "add-only group submission."
    ),
    legend_heading="Publish PNG + Groups",
    authority=(
        "Authority: Normative happy-path interaction map (ADRs 0005–0007, 0041); one "
        "photo; zero groups skip 16–19; PNG direct to Flickr; 202 = durable handoff; "
        "group handling is add-only and fail-polite. Contracts own omitted Album, "
        "failure, and recovery detail."
    ),
    svg_stem="clean-room-authentication-publish-png-groups",
    boundaries=P3_BOUNDARIES,
    icons=P3_ICONS,
    edges=P3_EDGES,
    flow_steps=P3_FLOW_STEPS,
    legend_row_padding=0,
    legend_height=690,
    legend_min_row_height=26,
    legend_text_size=13.25,
    legend_x=1080,
    legend_width=288,
    legend_4k_inset_pixels=1,
    authority_width=1339,
    # Keep one marker unit of triangle beyond the stem endpoint so the square
    # butt cap cannot paint through the arrow tip.
    arrow_marker_ref_x=7,
)

PAGES = (PAGE_1, PAGE_2, PAGE_3)


def _scaled(value: float, scale: float) -> str:
    """Return one stable diagrams.net or SVG number."""

    scaled = value * scale
    if scaled.is_integer():
        return str(int(scaled))
    return f"{scaled:.3f}".rstrip("0").rstrip(".")


def _legend_width(page: DiagramPage, sheet: Sheet) -> float:
    """Return the legend width, including the 4K raster-centering inset."""

    if sheet.suffix == "4k":
        return page.legend_width - (page.legend_4k_inset_pixels / sheet.scale_x)
    return float(page.legend_width)


def _data_uri(svg: str) -> str:
    """Embed one SVG glyph in a diagrams.net image cell."""

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _geometry(  # noqa: PLR0913, PLR0917
    parent: ET.Element,
    sheet: Sheet,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    """Attach scaled absolute geometry to one diagrams.net cell."""

    ET.SubElement(
        parent,
        "mxGeometry",
        {
            "x": _scaled(x, sheet.scale_x),
            "y": _scaled(y, sheet.scale_y),
            "width": _scaled(width, sheet.scale_x),
            "height": _scaled(height, sheet.scale_y),
            "as": "geometry",
        },
    )


def _drawio_text(  # noqa: PLR0913, PLR0917
    root: ET.Element,
    sheet: Sheet,
    identifier: str,
    value: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    font_size: int,
    bold: bool = False,
    align: str = "left",
    color: str = "#1A1A1A",
) -> None:
    """Add one editable diagrams.net text cell."""

    style = (
        "text;html=1;whiteSpace=wrap;verticalAlign=middle;"
        f"align={align};fontSize={_scaled(font_size, sheet.font_scale)};"
        f"fontColor={color};fontStyle={1 if bold else 0};"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": identifier,
            "value": value,
            "style": style,
            "vertex": "1",
            "parent": "1",
        },
    )
    _geometry(cell, sheet, x, y, width, height)


def _drawio_boundary(root: ET.Element, sheet: Sheet, boundary: Boundary) -> None:
    """Add one intentionally broad provider container."""

    style = (
        "rounded=0;whiteSpace=wrap;html=1;container=1;collapsible=0;"
        "recursiveResize=0;fillColor=none;strokeColor=#1A1A1A;"
        f"strokeWidth={_scaled(1.5, sheet.font_scale)};verticalAlign=top;"
        f"fontSize={_scaled(15, sheet.font_scale)};fontStyle=1;"
        f"align={boundary.label_align};spacingTop={_scaled(12, sheet.font_scale)};"
        f"spacingLeft={_scaled(12, sheet.scale_x)};"
        f"spacingRight={_scaled(12, sheet.scale_x)};"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": boundary.identifier,
            "value": boundary.drawio_label,
            "style": style,
            "vertex": "1",
            "parent": "1",
        },
    )
    _geometry(
        cell,
        sheet,
        boundary.x,
        boundary.y,
        boundary.width,
        boundary.height,
    )


def _drawio_icon(
    root: ET.Element,
    sheet: Sheet,
    icon: Icon,
    boundary_by_id: dict[str, Boundary],
) -> None:
    """Add one embedded glyph and its label."""

    x = icon.x
    y = icon.y
    label_space = icon.label_space if icon.drawio_label else 0
    height = icon.height - label_space
    if icon.label_position == "top":
        y += label_space
    if icon.parent != "1":
        boundary = boundary_by_id[icon.parent]
        x -= boundary.x
        y -= boundary.y
    label_style = (
        f"labelPosition=center;align={icon.label_align};"
        "verticalLabelPosition=bottom;verticalAlign=top;"
        f"spacingTop={6 + icon.bottom_label_offset};"
        f"spacingRight={-icon.bottom_label_x_offset};"
    )
    if icon.label_position == "top":
        label_style = (
            f"labelPosition=center;align={icon.label_align};"
            "verticalLabelPosition=top;verticalAlign=bottom;"
            f"spacingBottom={6 - icon.top_label_offset};"
        )
    elif icon.label_position == "top-left":
        label_style = (
            "labelPosition=left;align=right;verticalLabelPosition=middle;"
            "verticalAlign=top;spacingTop=20;spacingRight=-20;"
        )
    elif icon.label_position == "top-right":
        label_style = (
            "labelPosition=right;align=left;verticalLabelPosition=middle;"
            "verticalAlign=top;spacingTop=20;spacingLeft=0;"
        )
    elif icon.label_position == "right":
        vertical_spacing = (
            f"spacingBottom={-icon.right_label_offset};"
            if icon.right_label_offset < 0
            else f"spacingTop={icon.right_label_offset};"
        )
        label_style = (
            "labelPosition=right;align=left;verticalLabelPosition=middle;"
            f"verticalAlign=middle;spacingLeft={6 - icon.right_label_inset};"
            f"{vertical_spacing}"
        )
    style = (
        "shape=image;html=1;imageAspect=1;aspect=fixed;"
        f"image={_data_uri(icon.svg)};fontSize={_scaled(12, sheet.font_scale)};"
        f"fontStyle=1;{label_style}"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": icon.identifier,
            "value": icon.drawio_label,
            "style": style,
            "vertex": "1",
            "parent": icon.parent,
        },
    )
    _geometry(cell, sheet, x, y, icon.width, height)


def _drawio_edge(
    root: ET.Element,
    sheet: Sheet,
    edge: Edge,
    icon_by_id: dict[str, Icon],
) -> None:
    """Add one conceptual arrow with explicit attachment points."""

    start_arrow = "block" if edge.bidirectional else "none"
    start_fill = "1" if edge.bidirectional else "0"
    target_y = edge.target_y if edge.drawio_target_y is None else edge.drawio_target_y
    routing = (
        "edgeStyle=orthogonalEdgeStyle;orthogonalLoop=1;jettySize=auto;" if edge.orthogonal else ""
    )
    style = (
        "rounded=0;html=1;endArrow=block;endFill=1;"
        f"startArrow={start_arrow};startFill={start_fill};{routing}"
        f"endSize={_scaled(3, sheet.font_scale)};"
        f"startSize={_scaled(3, sheet.font_scale)};"
        f"strokeWidth={_scaled(2.25, sheet.font_scale)};"
        "strokeColor=#1A1A1A;labelBackgroundColor=#FFFFFF;"
        f"exitX={edge.source_x};exitY={edge.source_y};exitDx=0;exitDy=0;"
        f"entryX={edge.target_x};entryY={target_y};entryDx=0;entryDy=0;"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": edge.identifier,
            "value": "",
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": edge.source,
            "target": edge.target,
        },
    )
    geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if edge.waypoints:
        points = ET.SubElement(geometry, "Array", {"as": "points"})
        for waypoint_x, waypoint_y in edge.waypoints:
            ET.SubElement(
                points,
                "mxPoint",
                {
                    "x": _scaled(waypoint_x, sheet.scale_x),
                    "y": _scaled(waypoint_y, sheet.scale_y),
                },
            )
    elif edge.vertical_first:
        source_x, _ = _svg_anchor(
            icon_by_id[edge.source],
            edge.source_x,
            edge.source_y,
        )
        _, target_y = _svg_anchor(
            icon_by_id[edge.target],
            edge.target_x,
            edge.target_y,
        )
        points = ET.SubElement(geometry, "Array", {"as": "points"})
        ET.SubElement(
            points,
            "mxPoint",
            {
                "x": _scaled(source_x, sheet.scale_x),
                "y": _scaled(target_y, sheet.scale_y),
            },
        )


def _drawio_flow_step(root: ET.Element, sheet: Sheet, step: FlowStep) -> None:
    """Add one old-diagram-style numbered flow badge."""

    style = (
        "ellipse;whiteSpace=wrap;html=1;fillColor=#003087;strokeColor=#FFFFFF;"
        f"strokeWidth={_scaled(2, sheet.font_scale)};fontColor=#FFFFFF;"
        f"fontSize={_scaled(9, sheet.font_scale)};fontStyle=1;"
        "align=center;verticalAlign=middle;"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": f"step-{step.number}",
            "value": str(step.number),
            "style": style,
            "vertex": "1",
            "parent": "1",
        },
    )
    _geometry(cell, sheet, step.badge_x, step.badge_y, 20, 20)


def _drawio_flow_legend(
    root: ET.Element,
    sheet: Sheet,
    page: DiagramPage,
) -> None:
    """Add one page's chronological flow legend."""

    number_size = _scaled(LEGEND_NUMBER_SIZE, sheet.font_scale)
    text_size = _scaled(page.legend_text_size, sheet.font_scale)
    number_width = _scaled(18, sheet.scale_x)
    number_padding = _scaled(8, sheet.scale_x)
    row_padding = _scaled(page.legend_row_padding, sheet.scale_y)
    rows = "".join(
        (
            f'<tr><td style="width:{number_width}px;text-align:right;'
            f"padding:0 {number_padding}px {row_padding}px 0;"
            f'vertical-align:top;font-size:{number_size}px"><b>{step.number}</b></td>'
            f'<td style="vertical-align:top;padding-bottom:{row_padding}px;'
            f'font-size:{text_size}px">'
            f"{'<br>'.join(html.escape(line) for line in step.lines)}</td></tr>"
        )
        for step in page.flow_steps
    )
    heading_border = _scaled(1.5, sheet.font_scale)
    heading_padding = _scaled(3, sheet.scale_y)
    table_margin = _scaled(12, sheet.scale_y)
    value = (
        f'<div style="font-size:{_scaled(LEGEND_HEADING_SIZE, sheet.font_scale)}px;'
        f"border-bottom:{heading_border}px solid #1A1A1A;display:inline-block;"
        f'padding-bottom:{heading_padding}px"><b>{html.escape(page.legend_heading)}</b></div>'
        f'<table cellpadding="0" cellspacing="0" style="margin-top:{table_margin}px">'
        f"{rows}</table>"
    )
    style = (
        "rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
        "fillColor=#FFFFFF;strokeColor=#003087;"
        f"strokeWidth={_scaled(1.5, sheet.font_scale)};"
        f"spacingLeft={_scaled(10, sheet.scale_x)};"
        f"spacingTop={_scaled(10, sheet.scale_y)};"
        f"spacingRight={_scaled(10, sheet.scale_x)};"
    )
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": f"{page.identifier}-flow",
            "value": value,
            "style": style,
            "vertex": "1",
            "parent": "1",
        },
    )
    _geometry(
        cell,
        sheet,
        page.legend_x,
        LEGEND_Y,
        _legend_width(page, sheet),
        page.legend_height,
    )


def _append_drawio_page(mxfile: ET.Element, sheet: Sheet, page: DiagramPage) -> None:
    """Append one uncompressed diagrams.net tab."""

    diagram = ET.SubElement(
        mxfile,
        "diagram",
        {
            "id": f"fga-clean-room-{page.identifier}-{sheet.suffix}",
            "name": page.tab_name,
        },
    )
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": str(sheet.width),
            "dy": str(sheet.height),
            "grid": "0",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(sheet.width),
            "pageHeight": str(sheet.height),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    _drawio_text(
        root,
        sheet,
        f"{page.identifier}-title",
        page.title,
        OUTER_TEXT_X,
        TITLE_DRAWIO_Y,
        720,
        38,
        font_size=21,
        bold=True,
    )
    _drawio_text(
        root,
        sheet,
        f"{page.identifier}-date",
        page.date,
        30,
        52,
        310,
        26,
        font_size=15,
        bold=True,
        align="center",
    )
    boundary_by_id = {boundary.identifier: boundary for boundary in page.boundaries}
    icon_by_id = {icon.identifier: icon for icon in page.icons}
    for boundary in page.boundaries:
        _drawio_boundary(root, sheet, boundary)
    for icon in page.icons:
        _drawio_icon(root, sheet, icon, boundary_by_id)
    for edge in page.edges:
        _drawio_edge(
            root,
            sheet,
            edge,
            icon_by_id,
        )
    for step in page.flow_steps:
        _drawio_flow_step(root, sheet, step)
    _drawio_flow_legend(root, sheet, page)
    _drawio_text(
        root,
        sheet,
        f"{page.identifier}-authority",
        page.authority,
        OUTER_TEXT_X,
        page.authority_baseline_y - 20,
        page.authority_width,
        24,
        font_size=10,
        color="#555555",
    )


def _build_drawio(sheet: Sheet) -> str:
    """Build one multi-tab, uncompressed diagrams.net document."""

    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-08-30T00:00:00.000Z",
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
            "compressed": "false",
        },
    )
    for page in PAGES:
        _append_drawio_page(mxfile, sheet, page)

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode", short_empty_elements=True) + "\n"


def _svg_text(  # noqa: PLR0913
    parts: list[str],
    sheet: Sheet,
    x: float,
    y: float,
    lines: tuple[str, ...],
    *,
    size: float,
    weight: int = 400,
    anchor: str = "start",
    color: str = "#1A1A1A",
    line_height: float = 1.2,
) -> None:
    """Append one SVG text block."""

    text_x = _scaled(x, sheet.scale_x)
    text_y = _scaled(y, sheet.scale_y)
    parts.append(
        f'<text x="{text_x}" y="{text_y}" font-size="{_scaled(size, sheet.font_scale)}" '
        f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}">'
    )
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else _scaled(size * line_height, sheet.font_scale)
        parts.append(f'<tspan x="{text_x}" dy="{dy}">{html.escape(line)}</tspan>')
    parts.append("</text>")


def _svg_image(parts: list[str], sheet: Sheet, icon: Icon) -> None:
    """Append one embedded SVG glyph and its positioned label."""

    label_space = icon.label_space if icon.svg_label else 0
    image_y = icon.y + label_space if icon.label_position == "top" else icon.y
    image_height = icon.height - label_space
    parts.append(
        f'<image x="{_scaled(icon.x, sheet.scale_x)}" '
        f'y="{_scaled(image_y, sheet.scale_y)}" '
        f'width="{_scaled(icon.width, sheet.scale_x)}" '
        f'height="{_scaled(image_height, sheet.scale_y)}" '
        f'href="{_data_uri(icon.svg)}" preserveAspectRatio="xMidYMid meet" />'
    )
    if icon.svg_label:
        label_x = icon.x + icon.width // 2
        label_anchor = "middle"
        if icon.label_align == "right":
            label_x = icon.x + icon.width + icon.bottom_label_x_offset
            label_anchor = "end"
        label_y = icon.y + icon.height - 9
        if icon.label_position == "top":
            label_y = icon.y + 12 + icon.top_label_offset
        elif icon.label_position == "top-left":
            label_x = icon.x + 20
            label_y = icon.y + 20
            label_anchor = "end"
        elif icon.label_position == "top-right":
            label_x = icon.x + icon.width
            label_y = icon.y + 20
            label_anchor = "start"
        elif icon.label_position == "right":
            label_x = icon.x + icon.width + 10 - icon.right_label_inset
            label_y = icon.y + icon.height // 2 - 3 + icon.right_label_offset
            label_anchor = "start"
            if icon.center_right_label_on_image:
                line_step = 12 * 1.05
                label_y = (
                    image_y
                    + image_height / 2
                    + 4
                    - line_step * (len(icon.svg_label) - 1) / 2
                    + icon.right_label_offset
                )
        else:
            label_y += icon.bottom_label_offset
        _svg_text(
            parts,
            sheet,
            label_x,
            label_y,
            icon.svg_label,
            size=12,
            weight=700,
            anchor=label_anchor,
            line_height=1.05,
        )


def _svg_anchor(icon: Icon, x_fraction: float, y_fraction: float) -> tuple[float, float]:
    """Return one padded anchor point on an icon's visible image."""

    label_space = icon.label_space if icon.svg_label else 0
    image_y = icon.y + label_space if icon.label_position == "top" else icon.y
    image_height = icon.height - label_space
    x = icon.x + icon.width * x_fraction
    y = image_y + image_height * y_fraction
    if x_fraction == 0:
        x -= 8
    elif x_fraction == 1:
        x += 8
    elif y_fraction == 0:
        y -= 8
    elif y_fraction == 1:
        y += 8
    return x, y


def _svg_edge(
    parts: list[str],
    sheet: Sheet,
    edge: Edge,
    icon_by_id: dict[str, Icon],
) -> None:
    """Append one arrow between explicit icon anchors."""

    source = icon_by_id[edge.source]
    target = icon_by_id[edge.target]
    source_x, source_y = _svg_anchor(source, edge.source_x, edge.source_y)
    target_x, target_y = _svg_anchor(target, edge.target_x, edge.target_y)
    target_x += edge.svg_target_x_offset
    target_y += edge.svg_target_y_offset
    if edge.orthogonal and abs(source_y - target_y) <= 1:
        horizontal_y = round((source_y + target_y) / 2)
        source_y = horizontal_y
        target_y = horizontal_y
    marker_start = ' marker-start="url(#arrow)"' if edge.bidirectional else ""
    stroke = (
        f'stroke="#1A1A1A" stroke-width="{_scaled(2.25, sheet.font_scale)}"'
        f'{marker_start} marker-end="url(#arrow)"'
    )
    if edge.waypoints:
        points = " ".join(
            (
                f"{_scaled(source_x, sheet.scale_x)},{_scaled(source_y, sheet.scale_y)}",
                *(
                    f"{_scaled(waypoint_x, sheet.scale_x)},{_scaled(waypoint_y, sheet.scale_y)}"
                    for waypoint_x, waypoint_y in edge.waypoints
                ),
                f"{_scaled(target_x, sheet.scale_x)},{_scaled(target_y, sheet.scale_y)}",
            )
        )
        parts.append(
            f'<polyline id="{html.escape(edge.identifier)}" points="{points}" '
            f'fill="none" {stroke} />'
        )
        return
    if edge.orthogonal and source_x != target_x and source_y != target_y:
        bend_x = source_x if edge.vertical_first else target_x
        bend_y = target_y if edge.vertical_first else source_y
        points = " ".join(
            (
                f"{_scaled(source_x, sheet.scale_x)},{_scaled(source_y, sheet.scale_y)}",
                f"{_scaled(bend_x, sheet.scale_x)},{_scaled(bend_y, sheet.scale_y)}",
                f"{_scaled(target_x, sheet.scale_x)},{_scaled(target_y, sheet.scale_y)}",
            )
        )
        parts.append(
            f'<polyline id="{html.escape(edge.identifier)}" points="{points}" '
            f'fill="none" {stroke} />'
        )
        return
    parts.append(
        f'<line id="{html.escape(edge.identifier)}" '
        f'x1="{_scaled(source_x, sheet.scale_x)}" '
        f'y1="{_scaled(source_y, sheet.scale_y)}" '
        f'x2="{_scaled(target_x, sheet.scale_x)}" '
        f'y2="{_scaled(target_y, sheet.scale_y)}" {stroke} />'
    )


def _svg_flow_step(parts: list[str], sheet: Sheet, step: FlowStep) -> None:
    """Append one numbered flow badge."""

    center_x = step.badge_x + 10
    center_y = step.badge_y + 10
    parts.append(
        f'<circle id="step-{step.number}" cx="{_scaled(center_x, sheet.scale_x)}" '
        f'cy="{_scaled(center_y, sheet.scale_y)}" '
        f'r="{_scaled(10, sheet.font_scale)}" fill="#003087" stroke="#FFFFFF" '
        f'stroke-width="{_scaled(2, sheet.font_scale)}" />'
    )
    _svg_text(
        parts,
        sheet,
        center_x,
        center_y + 3,
        (str(step.number),),
        size=9,
        weight=700,
        anchor="middle",
        color="#FFFFFF",
    )


def _svg_flow_legend(parts: list[str], sheet: Sheet, page: DiagramPage) -> None:
    """Append one page's chronological flow legend."""

    parts.append(
        f'<rect x="{_scaled(page.legend_x, sheet.scale_x)}" '
        f'y="{_scaled(LEGEND_Y, sheet.scale_y)}" '
        f'width="{_scaled(_legend_width(page, sheet), sheet.scale_x)}" '
        f'height="{_scaled(page.legend_height, sheet.scale_y)}" fill="#FFFFFF" '
        f'stroke="#003087" stroke-width="{_scaled(1.5, sheet.font_scale)}" />'
    )
    _svg_text(
        parts,
        sheet,
        page.legend_x + 14,
        LEGEND_Y + 31,
        (page.legend_heading,),
        size=LEGEND_HEADING_SIZE,
        weight=700,
    )
    parts.append(
        f'<line x1="{_scaled(page.legend_x + 14, sheet.scale_x)}" '
        f'y1="{_scaled(LEGEND_Y + 40, sheet.scale_y)}" '
        f'x2="{_scaled(page.legend_x + 166, sheet.scale_x)}" '
        f'y2="{_scaled(LEGEND_Y + 40, sheet.scale_y)}" '
        f'stroke="#1A1A1A" stroke-width="{_scaled(1.5, sheet.font_scale)}" />'
    )
    row_y = LEGEND_Y + 66
    for step in page.flow_steps:
        _svg_text(
            parts,
            sheet,
            page.legend_x + 25,
            row_y,
            (str(step.number),),
            size=LEGEND_NUMBER_SIZE,
            weight=700,
            anchor="end",
        )
        _svg_text(
            parts,
            sheet,
            page.legend_x + 40,
            row_y,
            step.lines,
            size=page.legend_text_size,
            line_height=LEGEND_LINE_HEIGHT,
        )
        row_y += max(
            page.legend_min_row_height,
            round(
                len(step.lines) * page.legend_text_size * LEGEND_LINE_HEIGHT
                + page.legend_row_padding
            ),
        )


def _build_svg(sheet: Sheet, page: DiagramPage) -> str:
    """Build one standalone SVG derivative for one diagram tab."""

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet.width}" '
            f'height="{sheet.height}" viewBox="0 0 {sheet.width} {sheet.height}" '
            'role="img" aria-labelledby="diagram-title diagram-description">'
        ),
        f'<title id="diagram-title">{html.escape(page.title)}</title>',
        f'<desc id="diagram-description">{html.escape(page.description)}</desc>',
        "<defs>",
        (
            '<marker id="arrow" markerWidth="8" markerHeight="8" '
            f'refX="{page.arrow_marker_ref_x}" refY="4" '
            'orient="auto-start-reverse" markerUnits="strokeWidth">'
            '<path d="M 0 0 L 8 4 L 0 8 z" fill="#1A1A1A" /></marker>'
        ),
        "</defs>",
        '<rect width="100%" height="100%" fill="#FFFFFF" />',
        '<g font-family="Arial, Helvetica, sans-serif">',
    ]
    _svg_text(
        parts,
        sheet,
        OUTER_TEXT_X,
        TITLE_SVG_BASELINE_Y,
        (page.title,),
        size=21,
        weight=700,
    )
    _svg_text(
        parts,
        sheet,
        185,
        72,
        (page.date,),
        size=15,
        weight=700,
        anchor="middle",
    )
    for boundary in page.boundaries:
        parts.append(
            f'<rect x="{_scaled(boundary.x, sheet.scale_x)}" '
            f'y="{_scaled(boundary.y, sheet.scale_y)}" '
            f'width="{_scaled(boundary.width, sheet.scale_x)}" '
            f'height="{_scaled(boundary.height, sheet.scale_y)}" fill="none" '
            f'stroke="#1A1A1A" stroke-width="{_scaled(1.5, sheet.font_scale)}" />'
        )
        label_x = boundary.x + boundary.width // 2
        label_anchor = "middle"
        if boundary.label_align == "right":
            label_x = boundary.x + boundary.width - 12
            label_anchor = "end"
        elif boundary.label_align == "left":
            label_x = boundary.x + 12
            label_anchor = "start"
        _svg_text(
            parts,
            sheet,
            label_x,
            boundary.y + 30,
            boundary.svg_label,
            size=15,
            weight=700,
            anchor=label_anchor,
            line_height=1.05,
        )
    icon_by_id = {icon.identifier: icon for icon in page.icons}
    for edge in page.edges:
        _svg_edge(parts, sheet, edge, icon_by_id)
    for icon in page.icons:
        _svg_image(parts, sheet, icon)
    for step in page.flow_steps:
        _svg_flow_step(parts, sheet, step)
    _svg_flow_legend(parts, sheet, page)
    _svg_text(
        parts,
        sheet,
        OUTER_TEXT_X,
        page.authority_baseline_y,
        (page.authority,),
        size=10,
        color="#555555",
    )
    parts.extend(("</g>", "</svg>", ""))
    return "\n".join(parts)


def _outputs() -> dict[Path, str]:
    """Return every generated artifact and its complete content."""

    outputs: dict[Path, str] = {}
    for sheet in SHEETS:
        stem = f"clean-room-authentication-{sheet.suffix}"
        outputs[DIAGRAM_DIRECTORY / f"{stem}.drawio"] = _build_drawio(sheet)
        for page in PAGES:
            page_stem = f"{page.svg_stem}-{sheet.suffix}"
            outputs[DIAGRAM_DIRECTORY / f"{page_stem}.svg"] = _build_svg(sheet, page)
    return outputs


def _check(outputs: dict[Path, str]) -> int:
    """Report whether committed outputs match the generator."""

    stale = [
        path
        for path, content in outputs.items()
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if not stale:
        print("Clean-room authentication diagrams are current.")
        return 0
    for path in stale:
        print(f"Out of date: {path.relative_to(REPOSITORY_ROOT)}")
    return 1


def main() -> int:
    """Build or verify the clean-room authentication diagram artifacts."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report generated files that differ without writing them.",
    )
    args = parser.parse_args()
    outputs = _outputs()
    if args.check:
        return _check(outputs)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"Wrote {path.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
