"""
Participating Minnesota Mobile Medical Programs — Interactive Map
Run: streamlit run app.py
"""

import hashlib
import math
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# ── Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MN Mobile Medical Programs",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent

# Approximate centroids for all 87 Minnesota counties
MN_COUNTY_COORDS: dict[str, tuple[float, float]] = {
    "Aitkin":           (46.600,  -93.410),
    "Anoka":            (45.271,  -93.242),
    "Becker":           (46.936,  -95.674),
    "Beltrami":         (47.967,  -94.933),
    "Benton":           (45.703,  -93.991),
    "Big Stone":        (45.474,  -96.487),
    "Blue Earth":       (44.040,  -94.063),
    "Brown":            (44.244,  -94.732),
    "Carlton":          (46.600,  -92.672),
    "Carver":           (44.793,  -93.793),
    "Cass":             (47.130,  -94.348),
    "Chippewa":         (44.937,  -95.891),
    "Chisago":          (45.498,  -92.912),
    "Clay":             (46.900,  -96.493),
    "Clearwater":       (47.572,  -95.418),
    "Cook":             (47.819,  -90.573),
    "Cottonwood":       (44.037,  -95.190),
    "Crow Wing":        (46.572,  -94.073),
    "Dakota":           (44.676,  -93.057),
    "Dodge":            (44.022,  -92.859),
    "Douglas":          (45.883,  -95.440),
    "Faribault":        (43.672,  -93.959),
    "Fillmore":         (43.675,  -91.970),
    "Freeborn":         (43.674,  -93.352),
    "Goodhue":          (44.398,  -92.612),
    "Grant":            (45.933,  -96.001),
    "Hennepin":         (44.971,  -93.377),
    "Houston":          (43.672,  -91.470),
    "Hubbard":          (47.097,  -94.920),
    "Isanti":           (45.511,  -93.293),
    "Itasca":           (47.503,  -93.622),
    "Jackson":          (43.675,  -95.091),
    "Kanabec":          (45.949,  -93.283),
    "Kandiyohi":        (45.133,  -94.993),
    "Kittson":          (48.773,  -96.787),
    "Koochiching":      (48.213,  -94.023),
    "Lac qui Parle":    (44.957,  -96.151),
    "Lake":             (47.277,  -91.518),
    "Lake of the Woods":(48.753,  -94.882),
    "Le Sueur":         (44.361,  -93.729),
    "Lincoln":          (44.416,  -96.267),
    "Lyon":             (44.414,  -95.858),
    "Mahnomen":         (47.330,  -95.811),
    "Marshall":         (48.358,  -96.358),
    "Martin":           (43.672,  -94.559),
    "McLeod":           (44.842,  -94.259),
    "Meeker":           (45.121,  -94.521),
    "Mille Lacs":       (46.076,  -93.683),
    "Morrison":         (46.019,  -94.252),
    "Mower":            (43.674,  -92.712),
    "Murray":           (44.036,  -95.736),
    "Nicollet":         (44.342,  -94.218),
    "Nobles":           (43.673,  -95.738),
    "Norman":           (47.343,  -96.468),
    "Olmsted":          (44.003,  -92.371),
    "Otter Tail":       (46.413,  -95.728),
    "Pennington":       (48.072,  -96.053),
    "Pine":             (46.080,  -92.730),
    "Pipestone":        (44.013,  -96.317),
    "Polk":             (47.773,  -96.392),
    "Pope":             (45.583,  -95.556),
    "Ramsey":           (44.931,  -93.093),
    "Red Lake":         (47.880,  -96.061),
    "Redwood":          (44.421,  -95.236),
    "Renville":         (44.794,  -94.943),
    "Rice":             (44.371,  -93.298),
    "Rock":             (43.673,  -96.241),
    "Roseau":           (48.780,  -95.817),
    "St. Louis":        (47.574,  -92.456),
    "Scott":            (44.649,  -93.543),
    "Sherburne":        (45.483,  -93.772),
    "Sibley":           (44.574,  -94.234),
    "Stearns":          (45.553,  -94.638),
    "Steele":           (43.972,  -93.228),
    "Stevens":          (45.583,  -95.996),
    "Swift":            (45.299,  -95.819),
    "Todd":             (46.072,  -94.900),
    "Traverse":         (45.772,  -96.490),
    "Wabasha":          (44.291,  -92.050),
    "Wadena":           (46.572,  -95.000),
    "Waseca":           (44.073,  -93.597),
    "Washington":       (44.894,  -92.882),
    "Watonwan":         (43.992,  -94.608),
    "Wilkin":           (46.378,  -96.499),
    "Winona":           (44.033,  -91.631),
    "Wright":           (45.180,  -93.970),
    "Yellow Medicine":  (44.706,  -95.876),
}

SERVICE_LIST = [
    "Asthma", "Audiology/Hearing", "Behavioral Health", "Cancer Screening",
    "Community Paramedicine", "Dental", "Dermatology", "Disaster Response",
    "Drug Testing", "Foot Care", "Immunizations", "Infectious Disease Testing",
    "Infectious Disease Treatment", "Mammography", "Maternal and Infant Health",
    "Medications for Opioid Use Disorder", "Occupational Health", "Other Specialties",
    "Pediatrics", "Preventive", "Primary Care", "Sexual and Reproductive Health",
    "Social Services", "Vision", "Wound Care", "Other",
]

COMMUNITY_LIST = [
    "Agricultural Workers", "Children and Families", "Homeless/Unhoused",
    "Immigrants/Refugees", "LGBTQ+", "Low-Income", "Older Adults", "Other",
    "Students", "Tribal", "Uninsured", "Veterans",
]

# Colors per program type (mobile vs street differentiated by hue)
MOBILE_COLOR = "#1565C0"   # dark blue
STREET_COLOR = "#2E7D32"   # dark green

# ── Helpers ────────────────────────────────────────────────────────────────

def split_list(val: str | float) -> list[str]:
    """Split a semicolon- or comma-separated string into a trimmed list."""
    if pd.isna(val) or not str(val).strip():
        return []
    sep = ";" if ";" in str(val) else ","
    return [x.strip() for x in str(val).split(sep) if x.strip()]


def jitter(lat: float, lon: float, seed: str, scale: float = 0.045) -> tuple[float, float]:
    """Deterministic small offset so overlapping county markers stay distinct."""
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    angle = (h % 360) * math.pi / 180
    radius = ((h >> 8) % 1000) / 1000 * scale
    return lat + radius * math.cos(angle), lon + radius * math.sin(angle)


def safe_str(val) -> str:
    """Return empty string for NaN/None, otherwise stripped string."""
    return "" if pd.isna(val) else str(val).strip()


def org_label(row: pd.Series) -> str:
    return safe_str(row.get("organization_name")) or safe_str(row.get("respondent_name")) or "Unknown"


def make_popup(row: pd.Series, county: str, mode: str, frequency: str) -> folium.Popup:
    """Build an HTML popup for a marker."""
    name = org_label(row)
    title = safe_str(row.get("respondent_title"))
    program_type = safe_str(row.get("program_type"))
    svc_col = "mobile_services" if mode == "Mobile" else "street_services"
    other_col = "mobile_services_other" if mode == "Mobile" else "street_services_other"
    services = split_list(row.get(svc_col, ""))
    other_svc = safe_str(row.get(other_col))
    communities = split_list(row.get("communities_served", ""))
    free = safe_str(row.get("services_free"))
    walkins = safe_str(row.get("accepts_walkins"))
    website = safe_str(row.get("organization_website"))
    staffing = safe_str(row.get("staffing"))
    doc = safe_str(row.get("patient_documentation"))

    freq_badge_color = "#1565C0" if frequency == "Primary" else "#90CAF9"
    mode_badge_color = MOBILE_COLOR if mode == "Mobile" else STREET_COLOR

    services_html = "".join(f"<li>{s}</li>" for s in services)
    if other_svc:
        services_html += f"<li><em>{other_svc}</em></li>"
    communities_html = ", ".join(communities) if communities else "—"

    website_html = f'<a href="{website}" target="_blank">{website}</a>' if website else "—"
    staffing_html = staffing.replace("\n", "<br>") if staffing else "—"
    doc_html = doc.replace("\n", "<br>") if doc else "—"

    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; max-width: 340px; line-height: 1.5;">
      <h3 style="margin: 0 0 4px; font-size: 15px; color: #0d1117;">{name}</h3>
      {'<p style="margin:0 0 6px; color:#555;">'+title+'</p>' if title else ''}
      <span style="background:{mode_badge_color}; color:#fff; border-radius:4px;
                   padding:2px 7px; font-size:11px; margin-right:4px;">{mode} Unit</span>
      <span style="background:{freq_badge_color}; color:#fff; border-radius:4px;
                   padding:2px 7px; font-size:11px;">{frequency}</span>
      <p style="margin: 8px 0 2px;"><strong>County:</strong> {county}</p>
      <p style="margin: 2px 0;"><strong>Program type:</strong> {program_type}</p>
      <p style="margin: 2px 0;"><strong>Website:</strong> {website_html}</p>
      <hr style="margin: 8px 0; border-color: #e0e0e0;">
      <p style="margin: 0 0 2px;"><strong>Services ({mode}):</strong></p>
      <ul style="margin: 0 0 6px; padding-left: 18px;">{services_html or '<li>—</li>'}</ul>
      <p style="margin: 2px 0;"><strong>Populations served:</strong> {communities_html}</p>
      <p style="margin: 2px 0;"><strong>Free services:</strong> {free or '—'} &nbsp;|&nbsp;
         <strong>Walk-ins:</strong> {walkins or '—'}</p>
      <hr style="margin: 8px 0; border-color: #e0e0e0;">
      <p style="margin: 0 0 2px;"><strong>Staffing:</strong></p>
      <p style="margin: 0 0 6px; color: #444;">{staffing_html}</p>
      <p style="margin: 0 0 2px;"><strong>Patient documentation:</strong></p>
      <p style="margin: 0; color: #444;">{doc_html}</p>
    </div>
    """
    return folium.Popup(html, max_width=360)


def add_marker(fmap, lat, lon, color, fill_opacity, dash_array, tooltip_text, popup):
    folium.CircleMarker(
        location=(lat, lon),
        radius=9,
        color=color,
        weight=2.5,
        fill=True,
        fill_color=color,
        fill_opacity=fill_opacity,
        dash_array=dash_array,
        tooltip=folium.Tooltip(tooltip_text, sticky=False),
        popup=popup,
    ).add_to(fmap)


# ── Load data ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "cleaned_mobile_landscape_data.csv")
    return df[df["program_type"] != "Incomplete"].reset_index(drop=True)

df_all = load_data()

# ── Sidebar filters ────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Filters")

    program_types = sorted(df_all["program_type"].dropna().unique().tolist())
    sel_program_types = st.multiselect(
        "Program type",
        options=program_types,
        default=program_types,
    )

    show_secondary = st.checkbox("Show secondary / occasional counties", value=True)

    st.divider()

    sel_services = st.multiselect(
        "Services offered (any match)",
        options=SERVICE_LIST,
        default=[],
        placeholder="All services",
    )

    sel_populations = st.multiselect(
        "Populations served (any match)",
        options=COMMUNITY_LIST,
        default=[],
        placeholder="All populations",
    )

    st.divider()

    free_only = st.checkbox("Free services only")
    walkins_only = st.checkbox("Accepts walk-ins only")

    st.divider()

    # Legend
    st.markdown("**Legend**")
    st.markdown(
        f"""
        <div style="font-size:13px; line-height:2;">
          <span style="display:inline-block; width:14px; height:14px; border-radius:50%;
                       background:{MOBILE_COLOR}; margin-right:6px; vertical-align:middle;"></span>
          Mobile — Primary<br>
          <span style="display:inline-block; width:14px; height:14px; border-radius:50%;
                       background:{MOBILE_COLOR}; opacity:0.35; border:2px dashed {MOBILE_COLOR};
                       margin-right:6px; vertical-align:middle;"></span>
          Mobile — Secondary<br>
          <span style="display:inline-block; width:14px; height:14px; border-radius:50%;
                       background:{STREET_COLOR}; margin-right:6px; vertical-align:middle;"></span>
          Street Medicine — Primary<br>
          <span style="display:inline-block; width:14px; height:14px; border-radius:50%;
                       background:{STREET_COLOR}; opacity:0.35; border:2px dashed {STREET_COLOR};
                       margin-right:6px; vertical-align:middle;"></span>
          Street Medicine — Secondary
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Apply filters ──────────────────────────────────────────────────────────

df = df_all.copy()

# Program type
df = df[df["program_type"].isin(sel_program_types)]

# Services: org must have at least one selected service in either column
if sel_services:
    def has_service(row):
        combined = split_list(row.get("mobile_services", "")) + split_list(row.get("street_services", ""))
        return any(s in combined for s in sel_services)
    df = df[df.apply(has_service, axis=1)]

# Populations
if sel_populations:
    def has_population(row):
        pops = split_list(row.get("communities_served", ""))
        return any(p in pops for p in sel_populations)
    df = df[df.apply(has_population, axis=1)]

# Free / walk-ins
if free_only:
    df = df[df["services_free"] == "Yes"]
if walkins_only:
    df = df[df["accepts_walkins"] == "Yes"]

# ── Build map ──────────────────────────────────────────────────────────────

st.title("Participating Minnesota Mobile Medical Programs")
st.caption(
    f"Showing **{len(df)}** organization(s) — click any marker for details. "
    ""
)

# Minnesota center
mn_center = [46.40, -93.60]
fmap = folium.Map(
    location=mn_center,
    zoom_start=7,
    tiles="CartoDB positron",
    prefer_canvas=True,
)

# Add markers
for _, row in df.iterrows():
    name = org_label(row)
    pt = row.get("program_type", "")
    does_mobile = row.get("operates_mobile_units") == "Yes"
    does_street = row.get("operates_street_medicine") == "Yes"

    # Collect (county, mode, frequency, color, fill_opacity, dash_array) tuples
    entries: list[tuple] = []

    if does_mobile:
        for county in split_list(row.get("counties_mobile_primary", "")):
            entries.append((county, "Mobile", "Primary", MOBILE_COLOR, 0.85, None))
        if show_secondary:
            for county in split_list(row.get("counties_mobile_secondary", "")):
                entries.append((county, "Mobile", "Secondary", MOBILE_COLOR, 0.30, "6, 4"))

    if does_street:
        for county in split_list(row.get("counties_street_primary", "")):
            entries.append((county, "Street", "Primary", STREET_COLOR, 0.85, None))
        if show_secondary:
            for county in split_list(row.get("counties_street_secondary", "")):
                entries.append((county, "Street", "Secondary", STREET_COLOR, 0.30, "6, 4"))

    for county, mode, frequency, color, fill_opacity, dash_array in entries:
        coords = MN_COUNTY_COORDS.get(county)
        if not coords:
            continue
        lat, lon = jitter(coords[0], coords[1], seed=f"{name}|{county}|{mode}")
        tooltip = f"{name} — {county} ({mode}, {frequency})"
        popup = make_popup(row, county, mode, frequency)
        add_marker(fmap, lat, lon, color, fill_opacity, dash_array, tooltip, popup)

# ── Render ─────────────────────────────────────────────────────────────────

st_folium(fmap, use_container_width=True, height=620, returned_objects=[])

# ── Summary table ──────────────────────────────────────────────────────────

with st.expander("Organization details", expanded=False):
    display_cols = [
        "organization_name", "respondent_name", "respondent_title",
        "program_type", "mobile_services", "street_services",
        "counties_mobile_primary", "counties_mobile_secondary",
        "counties_street_primary", "counties_street_secondary",
        "communities_served", "services_free", "accepts_walkins",
    ]
    show_cols = [c for c in display_cols if c in df.columns]

    renamed = {
        "organization_name": "Organization",
        "respondent_name": "Contact",
        "respondent_title": "Title",
        "program_type": "Program Type",
        "mobile_services": "Mobile Services",
        "street_services": "Street Services",
        "counties_mobile_primary": "Mobile Counties (Primary)",
        "counties_mobile_secondary": "Mobile Counties (Secondary)",
        "counties_street_primary": "Street Counties (Primary)",
        "counties_street_secondary": "Street Counties (Secondary)",
        "communities_served": "Populations Served",
        "services_free": "Free",
        "accepts_walkins": "Walk-ins",
    }

    st.dataframe(
        df[show_cols].rename(columns=renamed).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
