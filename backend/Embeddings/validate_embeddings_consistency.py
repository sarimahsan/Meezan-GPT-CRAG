#!/usr/bin/env python3
"""
Embedding consistency validator.

Checks:
- File and schema sanity
- Row count match between embeddings and manifest
- Duplicate IDs in manifest
- NaN/Inf values
- Norm distribution and normalization expectation
- Per-dimension variance health
- Random cosine similarity distribution
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate embedding consistency")
    parser.add_argument(
        "--embeddings",
        type=Path,
        default=Path("../Embeddings_data/bge_base_en_v1_5_embeddings.npy"),
        help="Path to embeddings .npy file",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("../Embeddings_data/bge_base_en_v1_5_manifest.jsonl"),
        help="Path to metadata manifest .jsonl file",
    )
    parser.add_argument(
        "--run-report",
        type=Path,
        default=Path("../Embeddings_data/bge_base_en_v1_5_run_report.json"),
        help="Optional run report JSON for expected dimension/normalization",
    )
    parser.add_argument(
        "--sample-pairs",
        type=int,
        default=3000,
        help="Number of random vector pairs used for cosine diagnostics",
    )
    parser.add_argument(
        "--norm-lower",
        type=float,
        default=0.95,
        help="Lower norm bound when normalized embeddings are expected",
    )
    parser.add_argument(
        "--norm-upper",
        type=float,
        default=1.05,
        help="Upper norm bound when normalized embeddings are expected",
    )
    parser.add_argument(
        "--near-dup-threshold",
        type=float,
        default=0.999,
        help="Cosine threshold considered near-duplicate",
    )
    return parser.parse_args()


def load_manifest_ids(manifest_path: Path) -> Tuple[List[str], int]:
    ids: List[str] = []
    total_rows = 0

    with manifest_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            total_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in manifest at line {line_no}: {exc}") from exc

            row_id = str(row.get("id", "")).strip()
            if not row_id:
                raise ValueError(f"Missing 'id' in manifest at line {line_no}")
            ids.append(row_id)

    return ids, total_rows


def find_duplicate_ids(ids: List[str]) -> int:
    seen = set()
    duplicates = 0
    for item in ids:
        if item in seen:
            duplicates += 1
        else:
            seen.add(item)
    return duplicates


def load_run_report(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def cosine_diagnostics(
    emb: np.ndarray,
    sample_pairs: int,
    near_dup_threshold: float,
    rng_seed: int = 42,
) -> Dict[str, float]:
    n = emb.shape[0]
    if n < 2:
        return {
            "pairs_used": 0,
            "cos_mean": float("nan"),
            "cos_std": float("nan"),
            "cos_p95": float("nan"),
            "cos_p99": float("nan"),
            "cos_max": float("nan"),
            "near_duplicate_pairs": 0,
        }

    rng = np.random.default_rng(rng_seed)
    pairs = max(1, min(sample_pairs, n * (n - 1) // 2))

    i_idx = rng.integers(0, n, size=pairs)
    j_idx = rng.integers(0, n, size=pairs)

    same = i_idx == j_idx
    while np.any(same):
        j_idx[same] = rng.integers(0, n, size=np.sum(same))
        same = i_idx == j_idx

    a = emb[i_idx]
    b = emb[j_idx]

    a_norm = np.linalg.norm(a, axis=1)
    b_norm = np.linalg.norm(b, axis=1)
    denom = a_norm * b_norm

    safe = denom > 0
    cos = np.zeros(pairs, dtype=np.float64)
    cos[safe] = np.sum(a[safe] * b[safe], axis=1) / denom[safe]

    return {
        "pairs_used": int(pairs),
        "cos_mean": float(np.mean(cos)),
        "cos_std": float(np.std(cos)),
        "cos_p95": float(np.quantile(cos, 0.95)),
        "cos_p99": float(np.quantile(cos, 0.99)),
        "cos_max": float(np.max(cos)),
        "near_duplicate_pairs": int(np.sum(cos >= near_dup_threshold)),
    }


def main() -> int:
    args = parse_args()

    critical_issues: List[str] = []
    warnings: List[str] = []

    if not args.embeddings.exists():
        print(f"FAIL: embeddings file not found: {args.embeddings}")
        return 1
    if not args.manifest.exists():
        print(f"FAIL: manifest file not found: {args.manifest}")
        return 1

    emb = np.load(args.embeddings, mmap_mode="r")

    if emb.ndim != 2:
        print(f"FAIL: embeddings must be 2D, got shape={emb.shape}")
        return 1

    rows, dim = emb.shape

    manifest_ids, manifest_rows = load_manifest_ids(args.manifest)
    duplicate_ids = find_duplicate_ids(manifest_ids)

    if rows != manifest_rows:
        critical_issues.append(
            f"Row mismatch: embeddings rows={rows} vs manifest rows={manifest_rows}"
        )

    if duplicate_ids > 0:
        critical_issues.append(f"Duplicate IDs in manifest: {duplicate_ids}")

    finite_mask = np.isfinite(emb)
    non_finite_count = int(finite_mask.size - np.count_nonzero(finite_mask))
    if non_finite_count > 0:
        critical_issues.append(f"Found non-finite values (NaN/Inf): {non_finite_count}")

    norms = np.linalg.norm(emb, axis=1)
    norm_min = float(np.min(norms))
    norm_max = float(np.max(norms))
    norm_mean = float(np.mean(norms))
    norm_p01 = float(np.quantile(norms, 0.01))
    norm_p99 = float(np.quantile(norms, 0.99))

    dim_var = np.var(emb, axis=0)
    dead_dims = int(np.sum(dim_var < 1e-12))
    if dead_dims > 0:
        warnings.append(f"Very low-variance dimensions: {dead_dims} of {dim}")

    report = load_run_report(args.run_report)
    expected_dim = report.get("embedding_dimension")
    expected_normalized = report.get("normalize_embeddings")

    if expected_dim is not None and expected_dim != dim:
        critical_issues.append(
            f"Dimension mismatch vs run report: expected={expected_dim} actual={dim}"
        )

    if expected_normalized is True:
        out_of_band = int(np.sum((norms < args.norm_lower) | (norms > args.norm_upper)))
        if out_of_band > 0:
            critical_issues.append(
                "Normalization mismatch: "
                f"{out_of_band} vectors outside [{args.norm_lower}, {args.norm_upper}]"
            )

    cos_stats = cosine_diagnostics(
        emb=emb,
        sample_pairs=args.sample_pairs,
        near_dup_threshold=args.near_dup_threshold,
    )

    if cos_stats["near_duplicate_pairs"] > max(5, int(0.02 * cos_stats["pairs_used"])):
        warnings.append(
            "High near-duplicate rate in random pair sample: "
            f"{cos_stats['near_duplicate_pairs']} / {cos_stats['pairs_used']}"
        )

    print("=" * 80)
    print("EMBEDDING CONSISTENCY REPORT")
    print("=" * 80)
    print(f"Embeddings file         : {args.embeddings}")
    print(f"Manifest file           : {args.manifest}")
    print(f"Run report              : {args.run_report} ({'found' if report else 'not found'})")
    print("-" * 80)
    print(f"Rows                    : {rows}")
    print(f"Dimension               : {dim}")
    print(f"DType                   : {emb.dtype}")
    print(f"Manifest rows           : {manifest_rows}")
    print(f"Duplicate manifest IDs  : {duplicate_ids}")
    print(f"Non-finite values       : {non_finite_count}")
    print("-" * 80)
    print(
        "Norms                  : "
        f"min={norm_min:.6f} p01={norm_p01:.6f} mean={norm_mean:.6f} "
        f"p99={norm_p99:.6f} max={norm_max:.6f}"
    )
    print(f"Low-variance dimensions : {dead_dims}")
    print("-" * 80)
    print(
        "Cosine sample stats     : "
        f"pairs={cos_stats['pairs_used']} "
        f"mean={cos_stats['cos_mean']:.6f} std={cos_stats['cos_std']:.6f} "
        f"p95={cos_stats['cos_p95']:.6f} p99={cos_stats['cos_p99']:.6f} "
        f"max={cos_stats['cos_max']:.6f}"
    )
    print(
        "Near-duplicate pairs    : "
        f"{cos_stats['near_duplicate_pairs']} (threshold={args.near_dup_threshold})"
    )

    print("-" * 80)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"- {w}")
    else:
        print("WARNINGS: none")

    if critical_issues:
        print("CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"- {issue}")
        print("RESULT: FAIL")
        return 1

    print("CRITICAL ISSUES: none")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
