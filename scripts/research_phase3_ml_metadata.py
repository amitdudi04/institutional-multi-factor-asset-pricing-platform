"""Republish metric-only corrections without repeating validated ML fits."""

import json
import math
import subprocess
from pathlib import Path

import pandas as pd

from institutional_factor_platform.ml.evaluation import (
    block_bootstrap_ic,
    ranking_metrics,
    regression_metrics,
)
from institutional_factor_platform.ml.publication import publish_bundle
from institutional_factor_platform.ml.service import _metric_stability

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "phase3"


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main():
    path = WORK / "corrected_ml.json"
    original = json.loads(path.read_bytes())
    snapshot = WORK / "corrected_ml_before_constant_metric_fix.json"
    if snapshot.exists():
        original = json.loads(snapshot.read_bytes())
    else:
        snapshot.write_bytes(path.read_bytes())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    rows = []
    for row in original:
        manifest = row["corrected"]
        by = {a["name"]: a for a in manifest["artifacts"]}
        predictions = pd.read_parquet(ROOT / by["predictions"]["path"])
        docs = {
            name: json.loads((ROOT / by[name]["path"]).read_bytes())
            for name in ["evaluation", "comparison", "model_card", "lineage"]
        }
        for fold in docs["evaluation"]["folds"]:
            p = predictions.loc[predictions.fold.eq(fold["fold"])]
            metrics = dict(
                regression_metrics(p.target.to_numpy(float), p.prediction.to_numpy(float))
            )
            metrics.update(ranking_metrics(p))
            fold["metrics"] = metrics
        docs["comparison"]["selected_model_bootstrap_ic"] = block_bootstrap_ic(
            predictions, block_length=3, resamples=100, seed=17
        )
        docs["comparison"]["fold_metric_stability"] = _metric_stability(docs["evaluation"]["folds"])
        docs["model_card"]["folds"] = docs["evaluation"]["folds"]
        docs["model_card"]["metrics"] = docs["evaluation"]["folds"][-1]["metrics"]
        docs["lineage"].update(
            training_source_commit=manifest["git_commit"],
            analytics_source_commit=commit,
            preceding_publication=manifest["publication_id"],
            correction=(
                "Undefined constant-forecast correlations are unavailable, "
                "not NaN/zero; no model refit"
            ),
        )
        contents = {}
        for name, artifact in by.items():
            if artifact["media_type"] == "application/json":
                value = docs.get(name, json.loads((ROOT / artifact["path"]).read_bytes()))
                content = (json.dumps(sanitize(value), sort_keys=True, indent=2) + "\n").encode()
            else:
                content = (ROOT / artifact["path"]).read_bytes()
            contents[name] = (content, artifact["media_type"], tuple(artifact["columns"]))
        values = {
            k: v
            for k, v in manifest.items()
            if k not in {"schema_version", "publication_id", "created_at", "artifacts"}
        }
        values["git_commit"] = commit
        corrected = publish_bundle(
            ROOT, Path("data/ml"), Path("data/ml_manifests"), values, contents
        )
        rows.append(
            dict(
                family=row["family"],
                original_id=row["original_id"],
                intermediate_id=manifest["publication_id"],
                corrected=corrected.model_dump(mode="json"),
            )
        )
        print(row["family"], corrected.publication_id, flush=True)
    path.write_bytes((json.dumps(rows, indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
