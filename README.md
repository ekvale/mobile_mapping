# Minnesota Mobile Medical Programs — Interactive Map

A Streamlit map of mobile medical and street medicine programs operating in Minnesota,
built from the Mobile Landscape Survey (REDCap project 165).

Markers are placed at county centroids and color-coded by program type, with a small
deterministic jitter so overlapping counties stay readable. Click any marker for
services, populations served, staffing, and documentation practices.

## Quick start

```bash
git clone https://github.com/ekvale/mobile_mapping.git
cd mobile_mapping
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Repository layout

```
app.py                                  Streamlit map application
clean_explore.py                        REDCap export → cleaned CSV + console summary
requirements.txt                        Python dependencies
data/
  cleaned_mobile_landscape_data.csv     De-identified analysis file (app reads this)
  MobileLandscapeSurvey_DataDictionary_v2.csv
  MobileLandscapeSurvey_DataDictionary.csv
private_data/                           Git-ignored — raw REDCap export lives here
.streamlit/config.toml                  Theme
```

## Data handling

**The raw REDCap export contains respondent names, titles, and email addresses.**
It stays in `private_data/`, which is listed in `.gitignore` and must never be
committed to a public repository.

`data/cleaned_mobile_landscape_data.csv` is the published copy with the
`respondent_email` column removed. Respondent names, titles, and organization
names are retained because the app displays them as program contacts — if that
isn't appropriate for public release, drop those columns before publishing:

```python
import pandas as pd
df = pd.read_csv("private_data/cleaned_mobile_landscape_data.csv")
df = df.drop(columns=["respondent_email", "respondent_name", "respondent_title"])
df.to_csv("data/cleaned_mobile_landscape_data.csv", index=False)
```

## Refreshing the data

1. Export the survey from REDCap and drop the CSV in `private_data/`.
2. Update `DATA_FILE` in `clean_explore.py` if the filename changed.
3. Run `python clean_explore.py` — this writes the cleaned file to `private_data/`
   and prints a summary of program types, services, counties, and populations.
4. Copy the cleaned file to `data/` with identifiers removed (see above).

County assignment is parsed from free-text fields. Words like *sometimes*,
*monthly*, *occasionally*, *periodically*, and *as needed* split a response into
primary and secondary service areas, so review the "Full county text" section of
the `clean_explore.py` output after each refresh.

## Deploying

Hosted on [Streamlit Community Cloud](https://share.streamlit.io) — connect this
repo, set the main file to `app.py`, and deploy. The app reads only files committed
to `data/`, so no secrets or database access are required.

## Notes and limitations

- Markers show county centroids, not actual service locations.
- Seven survey responses total; two are incomplete and excluded from the map.
- Weekly schedule fields exist in the data dictionary but are unpopulated.
