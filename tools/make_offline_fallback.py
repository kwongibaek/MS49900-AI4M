#!/usr/bin/env python3
"""Build the offline copies the notebooks fall back to when the MP API is unavailable.

Run this once, from the repository root, with a Materials Project API key:

    MP_API_KEY=your_key python tools/make_offline_fallback.py

It writes two things into Data/:

    Hands_on_session1_data.xlsx   one sheet per summary.search query in the notebooks
    pd_entries/<System>.json.gz   entries for each candidate system in the section D assignment

Re-run it whenever the queries in the notebooks change, or to refresh against a
newer Materials Project release.
"""
import gzip
import json
import os
import sys
from getpass import getpass
from pathlib import Path

import pandas as pd
from monty.serialization import dumpfn
from mp_api.client import MPRester

DATA = Path("Data")
XLSX = DATA / "Hands_on_session1_data.xlsx"
PD_DIR = DATA / "pd_entries"

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

# Candidate systems for the section D assignment --------------------------------
CANDIDATE_SYSTEMS = [
    ["Li", "Co", "O"], ["Li", "Mn", "O"], ["Li", "Ni", "O"], ["Li", "Ti", "O"],
    ["Li", "Al", "O"], ["Na", "Fe", "O"], ["Na", "Mn", "O"], ["Na", "Co", "O"],
    ["Mg", "Fe", "O"], ["Zn", "Fe", "O"], ["Ca", "Ti", "O"], ["Ba", "Ti", "O"],
]
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
        sys.exit("An API key is required to build the offline copies.")

    PD_DIR.mkdir(exist_ok=True)
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

        print("\nSection D candidate systems")
        for elements in CANDIDATE_SYSTEMS:
            system = "-".join(elements)
            entries = mpr.get_entries_in_chemsys(
                elements, compatible_only=True,
                additional_criteria={"thermo_types": [THERMO_TYPE]})
            path = PD_DIR / f"{system}.json.gz"
            dumpfn(entries, path)
            print(f"  {system:10s} {len(entries):5d} entries  {path.stat().st_size/1024:6.1f} KB")

    # A record of when and against what these copies were made.
    sheets["_provenance"] = pd.DataFrame([
        {"key": "mp_db_version", "value": db_version},
        {"key": "generated_utc", "value": pd.Timestamp.utcnow().isoformat()},
        {"key": "thermo_type", "value": THERMO_TYPE},
    ])

    with pd.ExcelWriter(XLSX, engine="openpyxl") as writer:
        for sheet, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet, index=False)

    print(f"\nWrote {XLSX} ({XLSX.stat().st_size/1024:.1f} KB) with sheets: {list(sheets)}")
    total = sum(p.stat().st_size for p in PD_DIR.glob('*.json.gz'))
    print(f"Wrote {len(list(PD_DIR.glob('*.json.gz')))} files to {PD_DIR} ({total/1024:.1f} KB total)")


if __name__ == "__main__":
    main()
