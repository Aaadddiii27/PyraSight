
from pathlib import Path
import random
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

# ============================================================
# PyraSight - Mesogeos Spatial Buffer Simulation
# Simulation only: no model training or artifact modification
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "Dataset"
    / "a.danger_forecasting-20261028T200958Z-1-001"
    / "a.danger_forecasting"
)

POSITIVE_FILE = DATA_DIR / "positives.csv"
NEGATIVE_FILE = DATA_DIR / "negatives.csv"

RANDOM_SEED = 42
BUFFER_KM = 25
EARTH_RADIUS_KM = 6371.0088

print("=== PyraSight Spatial Buffer Simulation ===")

# ------------------------------------------------------------
# 1. Load group metadata only
# ------------------------------------------------------------

def load_group_metadata(file_path, label):
    df = pd.read_csv(
        file_path,
        usecols=["sample", "x", "y", "time"]
    )

    df["time"] = pd.to_datetime(df["time"])

    groups = (
        df.groupby("sample")
        .agg(
            longitude=("x", "first"),
            latitude=("y", "first"),
            start_date=("time", "min"),
            end_date=("time", "max"),
            rows=("time", "size"),
            unique_coordinates=("x", "nunique"),
        )
        .reset_index()
    )

    groups["label"] = label

    if not (groups["rows"] == 30).all():
        raise ValueError(f"Unexpected group size in {file_path}")

    return groups


positive = load_group_metadata(POSITIVE_FILE, 1)
negative = load_group_metadata(NEGATIVE_FILE, 0)

groups = pd.concat(
    [positive, negative],
    ignore_index=True
)

print(f"Positive groups: {len(positive):,}")
print(f"Negative groups: {len(negative):,}")
print(f"Total groups: {len(groups):,}")

# ------------------------------------------------------------
# 2. Assign 1-degree geographic blocks
# ------------------------------------------------------------

groups["block_lon"] = np.floor(groups["longitude"]).astype(int)
groups["block_lat"] = np.floor(groups["latitude"]).astype(int)

groups["block"] = list(
    zip(groups["block_lon"], groups["block_lat"])
)

blocks = list(groups["block"].unique())

rng = random.Random(RANDOM_SEED)
rng.shuffle(blocks)

n_test = round(len(blocks) * 0.20)
n_validation = round(len(blocks) * 0.15)

test_blocks = set(blocks[:n_test])
validation_blocks = set(
    blocks[n_test:n_test + n_validation]
)
train_blocks = set(
    blocks[n_test + n_validation:]
)

groups["split"] = groups["block"].map(
    lambda b: (
        "test" if b in test_blocks
        else "validation" if b in validation_blocks
        else "train"
    )
)

# ------------------------------------------------------------
# 3. Display initial split
# ------------------------------------------------------------

def print_split(title, data):
    print(f"\n{title}")
    print("-" * 55)

    for split_name in ["train", "validation", "test"]:
        subset = data[data["split"] == split_name]

        print(
            f"{split_name:12s} "
            f"groups={len(subset):6,} | "
            f"fire={(subset['label'] == 1).sum():6,} | "
            f"no_fire={(subset['label'] == 0).sum():6,}"
        )


print_split("INITIAL SPATIAL SPLIT", groups)

# ------------------------------------------------------------
# 4. Build held-out location tree
# ------------------------------------------------------------

held_out = groups[
    groups["split"].isin(["validation", "test"])
].copy()

train = groups[groups["split"] == "train"].copy()

held_coords = np.radians(
    held_out[["latitude", "longitude"]].to_numpy()
)

train_coords = np.radians(
    train[["latitude", "longitude"]].to_numpy()
)

held_tree = BallTree(
    held_coords,
    metric="haversine"
)

distances, _ = held_tree.query(
    train_coords,
    k=1
)

nearest_km = distances[:, 0] * EARTH_RADIUS_KM

# ------------------------------------------------------------
# 5. Remove training groups within 25 km
# ------------------------------------------------------------

keep_mask = nearest_km >= BUFFER_KM

train_kept = train.loc[keep_mask].copy()
train_removed = train.loc[~keep_mask].copy()

# ------------------------------------------------------------
# 6. Build final simulated dataset
# ------------------------------------------------------------

final_groups = pd.concat(
    [
        train_kept,
        groups[groups["split"] == "validation"],
        groups[groups["split"] == "test"],
    ],
    ignore_index=True
)

# ------------------------------------------------------------
# 7. Final statistics
# ------------------------------------------------------------

print("\n" + "=" * 55)
print("25 KM BUFFER RESULTS")
print("=" * 55)

print(f"Original training groups : {len(train):,}")
print(f"Removed training groups  : {len(train_removed):,}")
print(f"Remaining training groups: {len(train_kept):,}")

print(
    f"Training groups removed  : "
    f"{len(train_removed) / max(1, len(train)) * 100:.2f}%"
)

print_split("FINAL SPLIT AFTER BUFFER", final_groups)

# ------------------------------------------------------------
# 8. Class availability checks
# ------------------------------------------------------------

print("\nCLASS AVAILABILITY CHECK")
print("-" * 55)

for split_name in ["train", "validation", "test"]:
    subset = final_groups[
        final_groups["split"] == split_name
    ]

    fire_count = int((subset["label"] == 1).sum())
    no_fire_count = int((subset["label"] == 0).sum())

    status = (
        "OK"
        if fire_count > 0 and no_fire_count > 0
        else "WARNING: missing class"
    )

    print(
        f"{split_name:12s}: "
        f"fire={fire_count:,}, "
        f"no_fire={no_fire_count:,} -> {status}"
    )

# ------------------------------------------------------------
# 9. Verify remaining training distance
# ------------------------------------------------------------

if len(train_kept) > 0:
    remaining_coords = np.radians(
        train_kept[["latitude", "longitude"]].to_numpy()
    )

    final_distances, _ = held_tree.query(
        remaining_coords,
        k=1
    )

    minimum_distance = (
        final_distances.min() * EARTH_RADIUS_KM
    )

    print(
        f"\nMinimum remaining train-to-held-out distance: "
        f"{minimum_distance:.2f} km"
    )

print("\nSIMULATION COMPLETE")
print("No model trained. No artifacts modified.")
