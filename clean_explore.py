"""
REDCap 165 Mobile Medical Mapping — Data Cleaning & Exploration
Survey: Mobile Landscape Survey
Source: REDCap165MobileMedic_DATA_2026-07-15_1037.csv
"""

import re
from collections import Counter
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "private_data" / "REDCap165MobileMedic_DATA_20260715_1037.csv"
OUTPUT_FILE = ROOT / "private_data" / "cleaned_mobile_landscape_data.csv"

# ── Label maps (from data dictionary) ─────────────────────────────────────

SERVICE_LABELS = {
    1: "Asthma",
    2: "Audiology/Hearing",
    3: "Behavioral Health",
    4: "Cancer Screening",
    5: "Community Paramedicine",
    6: "Dental",
    7: "Dermatology",
    8: "Disaster Response",
    9: "Drug Testing",
    10: "Foot Care",
    11: "Immunizations",
    12: "Infectious Disease Testing",
    13: "Infectious Disease Treatment",
    14: "Mammography",
    15: "Maternal and Infant Health",
    16: "Medications for Opioid Use Disorder",
    17: "Occupational Health",
    18: "Other Specialties",
    19: "Pediatrics",
    20: "Preventive",
    21: "Primary Care",
    22: "Sexual and Reproductive Health",
    23: "Social Services",
    24: "Vision",
    25: "Wound Care",
    26: "Other",
}

COMMUNITY_LABELS = {
    1: "Agricultural Workers",
    2: "Children and Families",
    3: "Homeless/Unhoused",
    4: "Immigrants/Refugees",
    5: "LGBTQ+",
    6: "Low-Income",
    7: "Older Adults",
    8: "Other",
    9: "Students",
    10: "Tribal",
    11: "Uninsured",
    12: "Veterans",
}

MN_COUNTIES = [
    "Aitkin", "Anoka", "Becker", "Beltrami", "Benton", "Big Stone", "Blue Earth",
    "Brown", "Carlton", "Carver", "Cass", "Chippewa", "Chisago", "Clay",
    "Clearwater", "Cook", "Cottonwood", "Crow Wing", "Dakota", "Dodge",
    "Douglas", "Faribault", "Fillmore", "Freeborn", "Goodhue", "Grant",
    "Hennepin", "Houston", "Hubbard", "Isanti", "Itasca", "Jackson",
    "Kanabec", "Kandiyohi", "Kittson", "Koochiching", "Lac qui Parle",
    "Lake", "Lake of the Woods", "Le Sueur", "Lincoln", "Lyon", "Mahnomen",
    "Marshall", "Martin", "McLeod", "Meeker", "Mille Lacs", "Morrison",
    "Mower", "Murray", "Nicollet", "Nobles", "Norman", "Olmsted",
    "Otter Tail", "Pennington", "Pine", "Pipestone", "Polk", "Pope",
    "Ramsey", "Red Lake", "Redwood", "Renville", "Rice", "Rock",
    "Roseau", "St. Louis", "Saint Louis", "Scott", "Sherburne", "Sibley",
    "Stearns", "Steele", "Stevens", "Swift", "Todd", "Traverse",
    "Wabasha", "Wadena", "Waseca", "Washington", "Watonwan", "Wilkin",
    "Winona", "Wright", "Yellow Medicine",
]

# Normalize "St. Louis" and "Saint Louis" to one name
COUNTY_NORMALIZE = {"Saint Louis": "St. Louis"}

# Words/phrases that introduce secondary / occasional service areas
SECONDARY_MARKERS = re.compile(
    r"\b(sometimes(?:\s+in)?|monthly(?:\s+in)?|occasionally(?:\s+in)?"
    r"|periodically(?:\s+in)?|as\s+needed(?:\s+in)?)\b",
    re.IGNORECASE,
)

# ── Helpers ────────────────────────────────────────────────────────────────

def checkbox_labels(row, prefix, labels):
    """Collapse checkbox columns (prefix1, prefix2, …) into a readable list."""
    result = []
    for n, label in labels.items():
        col = f"{prefix}{n}"
        if col in row.index and row[col] == 1:
            result.append(label)
    return "; ".join(result)


def extract_counties(text):
    """Extract MN county names from a free-text field."""
    if pd.isna(text) or not str(text).strip():
        return []
    found = set()
    for county in MN_COUNTIES:
        if re.search(r"\b" + re.escape(county) + r"\b", text, re.IGNORECASE):
            canonical = COUNTY_NORMALIZE.get(county, county)
            found.add(canonical)
    return sorted(found)


def parse_counties_by_frequency(text):
    """
    Split a county text field into (primary, secondary) county lists.
    Primary = predominant / main service area.
    Secondary = counties that follow qualifiers like 'sometimes', 'monthly', 'occasionally'.
    Returns (primary_list, secondary_list).
    """
    if pd.isna(text) or not str(text).strip():
        return [], []
    match = SECONDARY_MARKERS.search(text)
    if match:
        primary = extract_counties(text[: match.start()])
        secondary = [c for c in extract_counties(text[match.start() :]) if c not in set(primary)]
    else:
        primary = extract_counties(text)
        secondary = []
    return primary, secondary


def count_labels(series):
    """Count how many respondents selected each semicolon-delimited label."""
    counts = Counter()
    for val in series:
        if val and not pd.isna(val):
            for item in str(val).split("; "):
                item = item.strip()
                if item:
                    counts[item] += 1
    return pd.Series(counts).sort_values(ascending=False)


def bar(n, total=None):
    """ASCII bar — n filled blocks, optionally show pct of total."""
    b = "#" * n
    if total:
        pct = n / total * 100
        return f"{b} {n} ({pct:.0f}%)"
    return f"{b} {n}"


def section(title):
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


# ── Load ───────────────────────────────────────────────────────────────────

df = pd.read_csv(DATA_FILE)
print(f"Loaded {len(df)} records x {len(df.columns)} columns")

# ── Clean ──────────────────────────────────────────────────────────────────

# Drop administrative columns
df.drop(
    columns=["redcap_survey_identifier", "mobile_landscape_survey_complete"],
    errors="ignore",
    inplace=True,
)

# Rename to match data dictionary field labels
df.rename(
    columns={
        "mobile_landscape_survey_timestamp": "survey_timestamp",
        "operate_mobile_units": "operates_mobile_units",
        "operate_street_medicine": "operates_street_medicine",
        "partner_programs": "partners_only",
        "mobile_counties": "counties_mobile",
        "street_counties": "counties_street",
        "walk_ins": "accepts_walkins",
        "follow_up_partners": "has_referral_partners",
    },
    inplace=True,
)

# Binary → Yes / No for yes/no fields (NaN stays NaN = question not shown)
YESNO_COLS = [
    "operates_mobile_units",
    "operates_street_medicine",
    "partners_only",
    "has_set_schedule",
    "services_free",
    "accepts_walkins",
    "has_referral_partners",
]
for col in YESNO_COLS:
    if col in df.columns:
        df[col] = df[col].map({1: "Yes", 0: "No", 1.0: "Yes", 0.0: "No"})

# Build checkbox aggregate columns
df["mobile_services"] = df.apply(
    lambda r: checkbox_labels(r, "mobile_services___", SERVICE_LABELS), axis=1
)
df["street_services"] = df.apply(
    lambda r: checkbox_labels(r, "street_services___", SERVICE_LABELS), axis=1
)
df["communities_served"] = df.apply(
    lambda r: checkbox_labels(r, "communities_served___", COMMUNITY_LABELS), axis=1
)

# Parse county text into primary (predominant) and secondary (occasional) lists
for field, prim_col, sec_col in [
    ("counties_mobile", "counties_mobile_primary", "counties_mobile_secondary"),
    ("counties_street", "counties_street_primary", "counties_street_secondary"),
]:
    parsed = df[field].apply(parse_counties_by_frequency)
    df[prim_col] = parsed.apply(lambda x: ", ".join(x[0]))
    df[sec_col] = parsed.apply(lambda x: ", ".join(x[1]))

# Program type summary column
def program_type(row):
    mob = row.get("operates_mobile_units")
    st = row.get("operates_street_medicine")
    par = row.get("partners_only")
    if mob == "Yes" and st == "Yes":
        return "Both Mobile & Street"
    if mob == "Yes":
        return "Mobile Unit Only"
    if st == "Yes":
        return "Street Medicine Only"
    if par == "Yes":
        return "Partner / Referral Only"
    return "Incomplete"

df["program_type"] = df.apply(program_type, axis=1)

# Drop raw checkbox columns (replaced by readable aggregates above)
raw_checkbox_cols = (
    [f"mobile_services___{n}" for n in range(1, 27)]
    + [f"street_services___{n}" for n in range(1, 27)]
    + [f"communities_served___{n}" for n in range(1, 13)]
)
df.drop(columns=raw_checkbox_cols, errors="ignore", inplace=True)

# Reorder columns: key fields first, then schedule, then free-text
key_cols = [
    "record_id", "survey_timestamp",
    "respondent_name", "respondent_title", "respondent_email",
    "organization_name", "organization_website",
    "program_type",
    "operates_mobile_units", "operates_street_medicine", "partners_only",
    "mobile_services", "mobile_services_other",
    "counties_mobile", "counties_mobile_primary", "counties_mobile_secondary",
    "street_services", "street_services_other",
    "counties_street", "counties_street_primary", "counties_street_secondary",
    "has_set_schedule",
    "communities_served", "communities_served_other",
    "services_free", "accepts_walkins",
    "patient_documentation", "has_referral_partners", "staffing",
]
sched_cols = [c for c in df.columns if c.startswith("schedule_")]
remaining = [c for c in df.columns if c not in key_cols and c not in sched_cols]
df = df[[c for c in key_cols if c in df.columns] + sched_cols + remaining]

df.to_csv(OUTPUT_FILE, index=False)
print(f"Cleaned CSV saved -> {OUTPUT_FILE.name}\n")

# ── Exploration ────────────────────────────────────────────────────────────

complete = df[df["program_type"] != "Incomplete"].copy()
incomplete = df[df["program_type"] == "Incomplete"].copy()

# ── 1. Program Structure ───────────────────────────────────────────────────

section("1. PROGRAM STRUCTURE")

print(f"\nTotal responses:     {len(df)}")
print(f"Complete responses:  {len(complete)}")
if len(incomplete):
    names = incomplete["respondent_name"].fillna("(unnamed)").tolist()
    print(f"Incomplete (skipped from counts below): {', '.join(names)}")

print("\nProgram types:")
for ptype, cnt in complete["program_type"].value_counts().items():
    print(f"  {bar(cnt)}  {ptype}")

print("\nService details (complete responses):")
for col, label in [
    ("services_free", "Services free"),
    ("accepts_walkins", "Accepts walk-ins"),
    ("has_set_schedule", "Has set schedule"),
    ("has_referral_partners", "Has referral partners"),
]:
    vc = complete[col].value_counts()
    yes = vc.get("Yes", 0)
    no = vc.get("No", 0)
    na = complete[col].isna().sum()
    print(f"  {label:30s}  Yes: {yes}  No: {no}  N/A: {na}")

# ── 2. Mobile Unit Services ────────────────────────────────────────────────

section("2. MOBILE UNIT SERVICES")

mobile = complete[complete["operates_mobile_units"] == "Yes"]
print(f"\n{len(mobile)} org(s) operate mobile units\n")

svc_counts = count_labels(mobile["mobile_services"])
if not svc_counts.empty:
    print("Services offered (# of orgs):")
    for svc, cnt in svc_counts.items():
        print(f"  {bar(cnt, len(mobile)):15s}  {svc}")
else:
    print("  No mobile services recorded.")

others = mobile["mobile_services_other"].dropna()
if not others.empty:
    print("\nOther mobile services noted:")
    for v in others:
        print(f"  - {v.strip()}")

# ── 3. Street Medicine Services ───────────────────────────────────────────

section("3. STREET / BACKPACK MEDICINE SERVICES")

street = complete[complete["operates_street_medicine"] == "Yes"]
print(f"\n{len(street)} org(s) operate street medicine\n")

svc_counts = count_labels(street["street_services"])
if not svc_counts.empty:
    print("Services offered (# of orgs):")
    for svc, cnt in svc_counts.items():
        print(f"  {bar(cnt, len(street)):15s}  {svc}")
else:
    print("  No street services recorded.")

others = street["street_services_other"].dropna()
if not others.empty:
    print("\nOther street services noted:")
    for v in others:
        print(f"  - {v.strip()}")

# ── 4. Counties Served ────────────────────────────────────────────────────

section("4. COUNTIES SERVED")

mob_primary_ctr = Counter()
mob_secondary_ctr = Counter()
st_primary_ctr = Counter()
st_secondary_ctr = Counter()

for _, row in complete.iterrows():
    prim, sec = parse_counties_by_frequency(row.get("counties_mobile", ""))
    for c in prim:
        mob_primary_ctr[c] += 1
    for c in sec:
        mob_secondary_ctr[c] += 1
    prim, sec = parse_counties_by_frequency(row.get("counties_street", ""))
    for c in prim:
        st_primary_ctr[c] += 1
    for c in sec:
        st_secondary_ctr[c] += 1

def print_county_table(primary_ctr, secondary_ctr):
    all_keys = sorted(set(primary_ctr) | set(secondary_ctr))
    if not all_keys:
        print("  (none)")
        return
    print(f"  {'County':<22}  Primary  Secondary")
    print(f"  {'-'*22}  -------  ---------")
    for county in sorted(all_keys, key=lambda c: (-primary_ctr.get(c, 0), -secondary_ctr.get(c, 0), c)):
        p = primary_ctr.get(county, 0)
        s = secondary_ctr.get(county, 0)
        p_bar = "#" * p if p else "-"
        s_bar = "#" * s if s else "-"
        print(f"  {county:<22}  {p_bar:<7}  {s_bar}")

print("\nMobile unit counties:")
print_county_table(mob_primary_ctr, mob_secondary_ctr)

print("\nStreet medicine counties:")
print_county_table(st_primary_ctr, st_secondary_ctr)

all_primary = set(mob_primary_ctr) | set(st_primary_ctr)
all_secondary = set(mob_secondary_ctr) | set(st_secondary_ctr)
all_counties = all_primary | all_secondary
print(f"\nPrimary counties  ({len(all_primary)}): {', '.join(sorted(all_primary))}")
print(f"Secondary counties ({len(all_secondary)}): {', '.join(sorted(all_secondary)) or '(none)'}")
print(f"Total unique counties across all programs: {len(all_counties)}")

# Raw text for review / counties that may not be parsed
print("\nFull county text (for review):")
for _, row in complete.iterrows():
    org = row.get("organization_name") or row.get("respondent_name", "?")
    mob_raw = row.get("counties_mobile", "")
    st_raw = row.get("counties_street", "")
    if not pd.isna(mob_raw) and str(mob_raw).strip():
        print(f"  [Mobile]  {org}: {mob_raw.strip()}")
    if not pd.isna(st_raw) and str(st_raw).strip():
        print(f"  [Street]  {org}: {st_raw.strip()}")

# ── 5. Populations Served ─────────────────────────────────────────────────

section("5. POPULATIONS SERVED")

comm_counts = count_labels(complete["communities_served"])
n = len(complete)
print(f"\nCommunities targeted (out of {n} complete responses):\n")
if not comm_counts.empty:
    for comm, cnt in comm_counts.items():
        print(f"  {bar(cnt, n):20s}  {comm}")
else:
    print("  No community data recorded.")

others = complete["communities_served_other"].dropna()
if not others.empty:
    print("\nOther populations noted:")
    for v in others:
        print(f"  - {v.strip()}")

# ── 6. Staffing Notes ─────────────────────────────────────────────────────

section("6. STAFFING NOTES")

for _, row in complete.iterrows():
    org = row.get("organization_name") or row.get("respondent_name", "Unknown")
    staffing = row.get("staffing", "")
    if staffing and not pd.isna(staffing):
        print(f"\n{org}:")
        for line in str(staffing).strip().splitlines():
            print(f"  {line.strip()}")

# ── 7. Patient Documentation ──────────────────────────────────────────────

section("7. PATIENT DOCUMENTATION PRACTICES")

for _, row in complete.iterrows():
    org = row.get("organization_name") or row.get("respondent_name", "Unknown")
    doc = row.get("patient_documentation", "")
    if doc and not pd.isna(doc):
        print(f"\n{org}:")
        for line in str(doc).strip().splitlines():
            print(f"  {line.strip()}")

# ── Summary ───────────────────────────────────────────────────────────────

section("SUMMARY")

mobile_orgs = complete[complete["operates_mobile_units"] == "Yes"]["organization_name"].fillna(
    complete[complete["operates_mobile_units"] == "Yes"]["respondent_name"]
).tolist()
street_orgs = complete[complete["operates_street_medicine"] == "Yes"]["organization_name"].fillna(
    complete[complete["operates_street_medicine"] == "Yes"]["respondent_name"]
).tolist()

print(f"\nComplete responses:          {len(complete)} / {len(df)}")
print(f"Mobile unit programs:        {len(mobile)} org(s)")
print(f"  {', '.join(mobile_orgs)}")
print(f"Street medicine programs:    {len(street)} org(s)")
print(f"  {', '.join(street_orgs)}")
print(f"Unique counties covered:     {len(all_counties)}")
print(f"Most common mobile service:  {svc_counts.index[0] if not svc_counts.empty else 'N/A'}")
print(f"\nCleaned data -> {OUTPUT_FILE}")
print("=" * 60)
