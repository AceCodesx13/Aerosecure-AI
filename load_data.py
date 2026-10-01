"""
AeroSecure AI - Data Loader

The C-MAPSS files ship with no column headers, just 26 space-separated numbers
per row. This adds the names and joins the engine data to our parts inventory.

Join: unit_number in C-MAPSS == unit_number in parts_inventory.csv
      (engine 47 -> part AER-0047)

Usage:
    python load_data.py
    python load_data.py --dataset FD002 --data-dir ./data
"""

import argparse
import os
import pandas as pd

# 26 columns, per the C-MAPSS readme.
COLUMNS = (
    ["unit_number", "time_cycles"]
    + [f"op_setting_{i}" for i in range(1, 4)]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def load_cmapss(path):
    """Read a raw C-MAPSS file and attach column names."""
    df = pd.read_csv(path, sep=r"\s+", header=None)

    # Some files have trailing whitespace that creates empty columns.
    df = df.dropna(axis=1, how="all")
    df.columns = COLUMNS[: df.shape[1]]
    return df


def add_rul(df):
    """
    Add remaining useful life.

    Training files run each engine until it fails, so the last cycle we see
    is the failure point. RUL at any row = last cycle for that engine minus
    the current cycle.
    """
    last_cycle = df.groupby("unit_number")["time_cycles"].max()
    df = df.merge(
        last_cycle.rename("max_cycles"),
        left_on="unit_number",
        right_index=True,
    )
    df["RUL"] = df["max_cycles"] - df["time_cycles"]
    return df.drop(columns=["max_cycles"])


def add_maintenance_flag(df, threshold=30):
    """
    Turn RUL into the yes/no target for a classifier.

    1 = this engine needs maintenance within `threshold` cycles.
    """
    df[f"needs_maintenance_{threshold}"] = (df["RUL"] <= threshold).astype(int)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Load C-MAPSS data and join it to the parts inventory."
    )
    parser.add_argument("--dataset", default="FD001",
                        help="Which C-MAPSS set to load (default FD001).")
    parser.add_argument("--data-dir", default=".",
                        help="Folder holding the train_FDxxx.txt files.")
    parser.add_argument("--parts", default="parts_inventory.csv",
                        help="Parts inventory CSV from generate_parts_data.py.")
    parser.add_argument("--threshold", type=int, default=30,
                        help="Cycles ahead to flag as needing maintenance.")
    parser.add_argument("--output", default="merged_data.csv",
                        help="Where to write the joined file.")
    args = parser.parse_args()

    train_path = os.path.join(args.data_dir, f"train_{args.dataset}.txt")
    if not os.path.exists(train_path):
        raise SystemExit(f"Can't find {train_path}")

    engines = load_cmapss(train_path)
    engines = add_rul(engines)
    engines = add_maintenance_flag(engines, args.threshold)

    print(f"{args.dataset}: {len(engines):,} rows, "
          f"{engines['unit_number'].nunique()} engines")

    if os.path.exists(args.parts):
        parts = pd.read_csv(args.parts)
        merged = engines.merge(parts, on="unit_number", how="left")

        unmatched = merged["part_number"].isna().sum()
        if unmatched:
            print(f"Warning: {unmatched} rows had no matching part. "
                  f"Parts file may not cover every engine.")
        else:
            print(f"Joined to {len(parts)} parts, every engine matched.")

        merged.to_csv(args.output, index=False)
        print(f"Wrote {args.output} ({len(merged.columns)} columns)")
    else:
        print(f"No parts file at {args.parts}, writing engine data only.")
        engines.to_csv(args.output, index=False)
        print(f"Wrote {args.output}")

    flagged = engines[f"needs_maintenance_{args.threshold}"].mean()
    print(f"Rows flagged as needing maintenance within "
          f"{args.threshold} cycles: {flagged:.1%}")


if __name__ == "__main__":
    main()
