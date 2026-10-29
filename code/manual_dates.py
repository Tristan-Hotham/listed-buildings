"""Hand check of the date rules: a fresh random sample (seed 2026) of 60 England entries, drawn after the
rules were first written. For each, the description was read (as part of the AI-assisted analysis, then
reviewed) and the century of the first build date it gives was noted. None = could not tell from the
captured text. ERRORS lists the entries the rules got wrong at the time of the check, and why."""
SEED = 2026
N = 60
UNSURE = [1316479, 1042851]
ERRORS = {1101480: "OCR 'Cl7' read as no date, so a later C19 was taken (rule then added for 'Cl7')",
          1080292: "no date in the description; a 1990 date from the page's legacy-system note was taken (boilerplate then cut)"}

# Scotland: 30 random entries (seed 2026) from the HES sample, read the same way. All 29 descriptions
# that give a date were dated to the right century; one gives no date in its opening and got none.
SCOTLAND_N = 30
SCOTLAND_ERRORS = {}
SCOTLAND_UNDATED_OK = ["LB15056"]

# Wales: 30 random Cadw reports (seed 2026). 28 dated to the right century class, 1 wrong, 1 unsure.
WALES_N = 30
WALES_UNSURE = ["82880"]
WALES_ERRORS = {"25920": "history text opens with the start of the Garden City movement (C19/C20) before the building's own date"}
