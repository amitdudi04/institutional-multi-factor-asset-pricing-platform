"""One-pass Phase 3 source authority inventory; no empirical refits."""

import json
from pathlib import Path

import pyarrow.parquet as pq

from institutional_factor_platform.data.lineage import LifecycleState
from institutional_factor_platform.data.storage import authenticate_dataset_evidence, sha256_file
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.ml.publication import MLRepository
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path(r"G:\4- Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform")
CACHE = ROOT.parent / "phase3/source_gate.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    prior = read(ROOT / "outputs/audit/phase2c/PHASE2C_SOURCE_MANIFEST.json")
    anchors = {p["publication_id"]: p["manifest_hash"] for p in prior["publications"]}
    records, publications = {}, []

    def record(path, checksum=None):
        path = Path(path)
        if str(path) in records:
            return
        stat = path.stat()
        value = dict(
            path=str(path),
            sha256=checksum or sha256_file(path),
            bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
        )
        if path.suffix == ".parquet":
            value.update(rows=pq.read_metadata(path).num_rows, schema=str(pq.read_schema(path)))
        records[str(path)] = value

    # Each authenticator checks its artifacts once. Do not hash their bytes again here.
    for base, fid in [
        (ROOT, "factor-4ddee9ac6fb45cedfd62a2cc68676b58"),
        (ARCHIVE, "factor-5a73616f131fca2102fa2ca4141ad64f"),
    ]:
        manifest = FactorRepository(base, base / "data/factor_manifests").authenticate(fid)
        if fid in anchors:
            assert manifest.content_hash() == anchors[fid]
        publications.append(manifest.model_dump(mode="json"))
        record(base / manifest.artifact_path, manifest.artifact_checksum)
        record(base / manifest.portfolio_artifact_path, manifest.portfolio_artifact_checksum)
        for parent in manifest.parents:
            if parent.dataset_id in {p.get("dataset_id") for p in publications}:
                continue
            path = ARCHIVE / "data/manifests" / parent.run_id / "dataset.json"
            pm = authenticate_dataset_evidence(
                parent.dataset_id, path, ARCHIVE, required_state=LifecycleState.FINALIZED
            )
            assert pm.output_checksum == parent.artifact_checksum
            publications.append(pm.model_dump(mode="json"))
            record(ARCHIVE / pm.parquet_path, pm.output_checksum)
            record(path)
    for base, ids in [
        (
            ROOT,
            [
                "asset-pricing-d60bee7310b34976c80372a0f0f29e21",
                "asset-pricing-8c2396179c4b509796b2cab043ec31d2",
            ],
        ),
        (ARCHIVE, ["asset-pricing-c0a72fae5349f1048e18557250da1927"]),
    ]:
        repository = AssetPricingRepository(base, base / "data/asset_pricing_manifests")
        for pid in ids:
            manifest = repository.authenticate(pid)
            if pid in anchors:
                assert manifest.content_hash() == anchors[pid]
            publications.append(manifest.model_dump(mode="json"))
            for artifact in manifest.artifacts:
                record(base / artifact.path, artifact.checksum)
    portfolio_repo = PortfolioRepository(ARCHIVE, ARCHIVE / "data/portfolio_manifests")
    portfolio = []
    for path in sorted((ARCHIVE / "data/portfolio_manifests").glob("*/portfolio-manifest.json")):
        raw = read(path)
        manifest = portfolio_repo.authenticate(raw["publication_id"])
        portfolio.append(manifest.model_dump(mode="json"))
        record(path)
        record(path.parent / "portfolio-publication.json")
        for artifact in manifest.artifacts:
            record(ARCHIVE / artifact.path, artifact.checksum)
    ml_repo = MLRepository(ARCHIVE, ARCHIVE / "data/ml_manifests")
    ml, archive_inventory = [], []
    for path in sorted((ARCHIVE / "data/ml_manifests").glob("*/ml-manifest.json")):
        raw = read(path)
        archive_inventory.append(
            dict(publication_id=raw["publication_id"], git_commit=raw["git_commit"])
        )
        # Paper's 91 monthly dates / 17-fold final design, not earlier daily experiments.
        if not raw["git_commit"].startswith("81404c85"):
            continue
        manifest = ml_repo.authenticate(raw["publication_id"])
        value = manifest.model_dump(mode="json")
        card = read(ARCHIVE / next(a.path for a in manifest.artifacts if a.name == "model_card"))
        value["family"] = card["family"]
        assert len(card["folds"]) == 17 and card["target"]["horizon"] == 21
        ml.append(value)
        record(path)
        record(path.parent / "ml-publication.json")
        for artifact in manifest.artifacts:
            record(ARCHIVE / artifact.path, artifact.checksum)
    assert len(ml) == 8 and len({m["family"] for m in ml}) == 8
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(
        (
            json.dumps(
                dict(
                    archive=str(ARCHIVE),
                    baseline=prior["base_commit"],
                    accepted_base="277c95bd4ba7279e6863bc3acc026d406a8ad482",
                    upstream=publications,
                    portfolio=portfolio,
                    ml=ml,
                    other_ml_inventory=archive_inventory,
                    authenticated_files=list(records.values()),
                    status="PASS",
                ),
                indent=2,
            )
            + "\n"
        ).encode()
    )
    print(
        f"PASS: {len(portfolio)} portfolios, {len(ml)} final-design ML publications; "
        f"{len(records)} distinct authenticated artifacts; prior numerical work reused"
    )


if __name__ == "__main__":
    main()
