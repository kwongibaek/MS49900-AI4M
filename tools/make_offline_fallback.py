#!/usr/bin/env python3
"""Build the saved copies the notebooks fall back to when the MP API is unavailable.

Run this once, from the repository root, with a Materials Project API key:

    MP_API_KEY=your_key python tools/make_offline_fallback.py

It writes two things into Data/:

    Hands_on_session1_data.xlsx   one sheet per summary.search query in the notebooks
    Li-Ni-O_entries.json.gz       the entries behind the section D assignment

In the notebooks these are reached by uncommenting the line marked
"## If the MP API is not working" in each cell that queries MP.

Re-run this whenever the queries in the notebooks change, or to refresh against a
newer Materials Project release.
"""
import os
import sys
from getpass import getpass
from pathlib import Path

import pandas as pd
from monty.serialization import dumpfn
from mp_api.client import MPRester

DATA = Path("Data")
XLSX = DATA / "Hands_on_session1_data.xlsx"

# Fields requested by the in-class notebook (section A) --------------------------
SUMMARY_FIELDS = ["material_id", "formula_pretty", "chemsys", "nelements", "nsites",
                  "band_gap", "energy_above_hull", "formation_energy_per_atom",
                  "is_stable", "density", "symmetry"]
FRAME_COLUMNS = ["material_id", "formula", "chemsys", "nelements", "nsites", "band_gap_eV",
                 "e_hull_eV_atom", "formation_eV_atom", "is_stable", "density_g_cm3",
                 "spacegroup", "spacegroup_number"]

# One entry per query the notebooks make. Sheet names match the cell that uses them.
SUMMARY_QUERIES = {
    "A5_LiFePO4": dict(formula="LiFePO4"),
    "A6_AO_oxides": dict(chemsys="*-O", formula="AB", num_elements=2,
                         energy_above_hull=(0, 0.05), band_gap=(1, 4)),
    "A7_ABC2_R3m": dict(elements=["Li", "O"], num_elements=3, formula="ABC2",
                        spacegroup_number=166, is_stable=True),
}

# Fields requested by the preclass notebook (section 4) --------------------------
PRECLASS_FIELDS = ["material_id", "formula_pretty", "band_gap", "energy_above_hull"]

# The one system every student builds in the section D assignment ----------------
ASSIGNMENT_ELEMENTS = ["Li", "Ni", "O"]
ASSIGNMENT_PATH = DATA / f"{'-'.join(ASSIGNMENT_ELEMENTS)}_entries.json.gz"
THERMO_TYPE = "GGA_GGA+U"


def summary_to_frame(docs):
    """Same conversion the notebook uses, so the saved sheet matches a live result."""
    rows = []
    for doc in docs:
        sym = doc.symmetry
        rows.append(dict(zip(FRAME_COLUMNS, [
            str(doc.material_id), doc.formula_pretty, doc.chemsys, doc.nelements, doc.nsites,
            doc.band_gap, doc.energy_above_hull, doc.formation_energy_per_atom,
            doc.is_stable, doc.density,
            getattr(sym, "symbol", None), getattr(sym, "number", None),
        ])))
    return pd.DataFrame(rows, columns=FRAME_COLUMNS)


def main():
    if not DATA.is_dir():
        sys.exit("Run this from the repository root; Data/ was not found here.")

    api_key = os.getenv("MP_API_KEY", "").strip() or getpass("Materials Project API key: ").strip()
    if not api_key:
        sys.exit("An API key is required to build the saved copies.")

    sheets = {}

    with MPRester(api_key) as mpr:
        db_version = mpr.db_version
        print(f"Materials Project DB {db_version}\n")

        print("Section A queries")
        for sheet, conditions in SUMMARY_QUERIES.items():
            docs = mpr.materials.summary.search(fields=SUMMARY_FIELDS, all_fields=False,
                                                num_chunks=1, chunk_size=200, **conditions)
            sheets[sheet] = summary_to_frame(docs)
            print(f"  {sheet:16s} {len(sheets[sheet]):4d} rows")

        print("\nPreclass query")
        docs = mpr.materials.summary.search(formula="LiFePO4", fields=PRECLASS_FIELDS,
                                            all_fields=False, num_chunks=1, chunk_size=10)
        sheets["preclass_LiFePO4"] = pd.DataFrame(
            [{f: getattr(d, f) for f in PRECLASS_FIELDS} for d in docs],
            columns=PRECLASS_FIELDS)
        sheets["preclass_LiFePO4"]["material_id"] = \
            sheets["preclass_LiFePO4"]["material_id"].astype(str)
        print(f"  preclass_LiFePO4 {len(sheets['preclass_LiFePO4']):4d} rows")

        print("\nSection D assignment system")
        entries = mpr.get_entries_in_chemsys(
            ASSIGNMENT_ELEMENTS, compatible_only=True,
            additional_criteria={"thermo_types": [THERMO_TYPE]})
        dumpfn(entries, ASSIGNMENT_PATH)
        print(f"  {'-'.join(ASSIGNMENT_ELEMENTS):10s} {len(entries):5d} entries  "
              f"{ASSIGNMENT_PATH.stat().st_size / 1024:6.1f} KB")

    # A record of when and against what these copies were made.
    sheets["_provenance"] = pd.DataFrame([
        {"key": "mp_db_version", "value": db_version},
        {"key": "generated_utc", "value": pd.Timestamp.utcnow().isoformat()},
        {"key": "thermo_type", "value": THERMO_TYPE},
        {"key": "assignment_system", "value": "-".join(ASSIGNMENT_ELEMENTS)},
    ])

    with pd.ExcelWriter(XLSX, engine="openpyxl") as writer:
        for sheet, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet, index=False)

    print(f"\nWrote {XLSX} ({XLSX.stat().st_size / 1024:.1f} KB) with sheets: {list(sheets)}")
    print(f"Wrote {ASSIGNMENT_PATH} ({ASSIGNMENT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
