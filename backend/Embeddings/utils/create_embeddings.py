from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

try:
    import torch
except ImportError as exc:
    raise SystemExit("PyTorch is required. Install with: pip install torch") from exc

try:
    from sentence_transformers import SentenceTransformer
except ImportError as exc:
    raise SystemExit(
        "sentence-transformers is required. Install with: pip install sentence-transformers"
    ) from exc

try:
    import psutil
except ImportError:
    psutil = None


LOGGER = logging.getLogger("embedding_pipeline")
DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"


@dataclass
class DocRecord:
    doc_id: str
    text: str
    metadata: Dict


@dataclass
class RunReport:
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    device: str
    model: str
    embedding_dimension: int
    total_documents: int
    total_characters: int
    avg_characters_per_doc: float
    batch_size: int
    normalize_embeddings: bool
    fp16: bool
    outputs: Dict[str, str]
    throughput_docs_per_sec: float
    throughput_chars_per_sec: float
    gpu_peak_memory_mb: float
    cpu_cores_used: int
    torch_num_threads: int
    input_sources: Dict[str, str]
    notes: List[str]


def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"embedding_run_{timestamp}.log"

    LOGGER.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    LOGGER.handlers.clear()
    LOGGER.addHandler(stream_handler)
    LOGGER.addHandler(file_handler)


def set_reproducibility(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def optimize_runtime(cpu_threads: Optional[int]) -> int:
    detected = os.cpu_count() or 4
    threads = cpu_threads if cpu_threads and cpu_threads > 0 else detected

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")
    os.environ.setdefault("OMP_NUM_THREADS", str(threads))
    os.environ.setdefault("MKL_NUM_THREADS", str(threads))

    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(max(1, threads // 2))
    except RuntimeError:
        pass

    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass

    return threads


def select_device(force_cpu: bool) -> str:
    if force_cpu:
        return "cpu"
    if torch.cuda.is_available():
        # Clear any leftover allocations before we start
        torch.cuda.empty_cache()
        gc.collect()
        return "cuda"
    return "cpu"


def load_docs_from_jsonl(path: Path) -> List[DocRecord]:
    records: List[DocRecord] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                LOGGER.warning("Skipping invalid JSONL row at line %d: %s", line_no, exc)
                continue

            text = str(row.get("text", "")).strip()
            if not text:
                continue

            doc_id = str(row.get("id") or f"jsonl_doc_{line_no}")
            metadata = row.get("metadata") or {}
            records.append(DocRecord(doc_id=doc_id, text=text, metadata=metadata))

    return records


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of max_chars length with optional overlap.
    BUG FIX: overlap must be < max_chars or start never advances → infinite loop.
    """
    # Guard: overlap must be strictly less than max_chars
    overlap = min(overlap, max_chars - 1)

    chunks = []
    start = 0
    text_length = len(text)
    step = max_chars - overlap  # always > 0 after the guard above

    while start < text_length:
        end = min(start + max_chars, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def load_docs_from_scraped_dir(path: Path) -> List[DocRecord]:
    """
    Load pre-chunked JSON files. Does NOT re-chunk here — chunking is done
    centrally in build_embeddings so we never double-chunk.
    """
    records: List[DocRecord] = []

    if not path.exists():
        LOGGER.warning("Scraped folder does not exist: %s", path)
        return records

    for file_path in sorted(path.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            LOGGER.warning("Skipping unreadable file %s: %s", file_path.name, exc)
            continue

        metadata = payload.get("metadata") or {}
        chunks = payload.get("chunks") or []
        title = metadata.get("title") or file_path.stem

        # If the file already has chunks, treat each chunk as one doc (no re-chunking)
        if chunks:
            for idx, chunk in enumerate(chunks):
                text = str(chunk).strip()
                if not text:
                    continue
                records.append(
                    DocRecord(
                        doc_id=f"{title}_chunk_{idx}",
                        text=text,
                        metadata={
                            "source_file": file_path.name,
                            "source_url": metadata.get("url"),
                            "source_title": title,
                            "chunk_index": idx,
                            "total_chunks": len(chunks),
                            "scraped_at": metadata.get("scraped_at"),
                            "pre_chunked": True,   # flag: skip re-chunking
                        },
                    )
                )
        else:
            # Flat text — will be chunked centrally
            text = str(payload.get("text", "")).strip()
            if text:
                records.append(
                    DocRecord(
                        doc_id=title,
                        text=text,
                        metadata={
                            "source_file": file_path.name,
                            "source_url": metadata.get("url"),
                            "source_title": title,
                            "scraped_at": metadata.get("scraped_at"),
                            "pre_chunked": False,
                        },
                    )
                )

    return records


def deduplicate_docs_by_id(docs: List[DocRecord]) -> List[DocRecord]:
    seen: set[str] = set()
    deduped: List[DocRecord] = []
    for doc in docs:
        if doc.doc_id in seen:
            continue
        seen.add(doc.doc_id)
        deduped.append(doc)

    dropped = len(docs) - len(deduped)
    if dropped > 0:
        LOGGER.warning("Dropped %d duplicate documents by doc_id", dropped)
    return deduped


def load_all_documents(
    input_jsonl: Optional[Path],
    scraped_dir: Optional[Path],
    combine_sources: bool,
) -> List[DocRecord]:
    docs: List[DocRecord] = []

    if input_jsonl and input_jsonl.exists():
        LOGGER.info("Loading prepared JSONL: %s", input_jsonl)
        docs.extend(load_docs_from_jsonl(input_jsonl))

        if scraped_dir and combine_sources:
            LOGGER.info("Combining with scraped JSON files from: %s", scraped_dir)
            docs.extend(load_docs_from_scraped_dir(scraped_dir))
    elif scraped_dir and scraped_dir.exists():
        LOGGER.info("Loading scraped JSON files from: %s", scraped_dir)
        docs.extend(load_docs_from_scraped_dir(scraped_dir))

    if not docs:
        raise ValueError("No input documents found. Check --input-jsonl or --input-dir.")

    docs = deduplicate_docs_by_id(docs)
    LOGGER.info("Loaded %d documents", len(docs))
    return docs


def _oom_like(exc: RuntimeError) -> bool:
    msg = str(exc).lower()
    return "out of memory" in msg or "cuda error: out of memory" in msg


def autotune_batch_size(
    model: SentenceTransformer,
    sample_texts: List[str],
    start_batch: int,
    max_batch: int,
    normalize_embeddings: bool,
    device: str,
) -> int:
    if device != "cuda":
        return max(8, min(start_batch, 64))  # conservative for CPU/RAM

    LOGGER.info("Auto-tuning batch size for available VRAM...")
    candidates: List[int] = []
    value = max(8, start_batch)
    while value <= max_batch:
        candidates.append(value)
        value *= 2

    best = candidates[0]

    for bs in candidates:
        try:
            torch.cuda.empty_cache()
            gc.collect()
            _ = model.encode(
                sample_texts[: min(len(sample_texts), bs)],
                batch_size=bs,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=normalize_embeddings,
            )
            torch.cuda.synchronize()
            best = bs
            LOGGER.info("Batch size %d passed", bs)
        except RuntimeError as exc:
            if _oom_like(exc):
                LOGGER.info("Batch size %d exceeded VRAM, stopping auto-tune", bs)
                torch.cuda.empty_cache()
                gc.collect()
                break
            raise

    LOGGER.info("Selected batch size: %d", best)
    return best


def batched(items: List[DocRecord], size: int) -> Iterable[List[DocRecord]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def write_metadata_manifest(path: Path, docs: List[DocRecord]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            row = {
                "id": d.doc_id,
                "chars": len(d.text),
                "metadata": d.metadata,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def chunk_docs(docs: List[DocRecord], max_chars: int = 1200, overlap: int = 50) -> List[DocRecord]:
    """
    Centralized chunking. Skips docs that are already pre-chunked
    (flagged by load_docs_from_scraped_dir).
    """
    chunked: List[DocRecord] = []
    for doc in docs:
        if doc.metadata.get("pre_chunked"):
            # Already chunked upstream — use as-is
            chunked.append(doc)
            continue

        chunks = chunk_text(doc.text, max_chars=max_chars, overlap=overlap)
        n = len(chunks)
        for idx, chunk in enumerate(chunks):
            chunked.append(
                DocRecord(
                    doc_id=f"{doc.doc_id}_chunk_{idx}",
                    text=chunk,
                    metadata={**doc.metadata, "chunk_index": idx, "total_chunks": n},
                )
            )

    return chunked


def build_embeddings(
    docs: List[DocRecord],
    model_name: str,
    output_embeddings_file: Path,
    output_manifest_file: Path,
    batch_size: int,
    max_batch_size: int,
    normalize_embeddings: bool,
    force_cpu: bool,
    fp16: bool,
    cpu_threads: Optional[int],
) -> RunReport:
    started = time.time()
    started_at = datetime.now().isoformat()

    set_reproducibility(42)
    threads_used = optimize_runtime(cpu_threads)
    device = select_device(force_cpu)

    LOGGER.info("Device selected: %s", device)

    # ── Chunk docs (centralized, no double-chunking) ──────────────────────────
    LOGGER.info("Chunking %d raw docs...", len(docs))
    docs = chunk_docs(docs, max_chars=1200, overlap=50)
    LOGGER.info("Total chunks after splitting: %d", len(docs))

    total_chars = sum(len(d.text) for d in docs)

    # ── Load model ────────────────────────────────────────────────────────────
    LOGGER.info("Loading model: %s", model_name)
    model = SentenceTransformer(model_name, device=device)

    if device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        if fp16:
            model.half()
            LOGGER.info("FP16 enabled for faster inference")

    # ── Auto-tune batch size ──────────────────────────────────────────────────
    if batch_size <= 0:
        sample = [d.text for d in docs[: min(512, len(docs))]]
        batch_size = autotune_batch_size(
            model=model,
            sample_texts=sample,
            start_batch=32,
            max_batch=max_batch_size,
            normalize_embeddings=normalize_embeddings,
            device=device,
        )

    emb_dim = model.get_sentence_embedding_dimension()
    LOGGER.info("Embedding dimension: %d", emb_dim)

    output_embeddings_file.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_file.parent.mkdir(parents=True, exist_ok=True)

    # ── Write manifest first (lightweight) ───────────────────────────────────
    write_metadata_manifest(output_manifest_file, docs)

    # ── Memory-mapped output — written in streaming batches ───────────────────
    # FIX: use mode="w+" only once to create the file, then close and reopen
    # as "r+" to avoid keeping the full array mapped in address space.
    matrix = np.lib.format.open_memmap(
        output_embeddings_file,
        mode="w+",
        dtype=np.float32,
        shape=(len(docs), emb_dim),
    )

    LOGGER.info("Encoding %d chunks with batch size %d", len(docs), batch_size)

    cursor = 0
    for batch_idx, batch in enumerate(batched(docs, batch_size)):
        batch_texts = [d.text for d in batch]

        try:
            emb = model.encode(
                batch_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=normalize_embeddings,
            )
        except RuntimeError as exc:
            if _oom_like(exc) and device == "cuda":
                # Halve batch size and retry once
                batch_size = max(1, batch_size // 2)
                LOGGER.warning("OOM! Retrying batch with halved batch size: %d", batch_size)
                torch.cuda.empty_cache()
                gc.collect()
                emb = model.encode(
                    batch_texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize_embeddings,
                )
            else:
                raise

        matrix[cursor : cursor + len(batch)] = emb.astype(np.float32, copy=False)
        cursor += len(batch)

        # Flush memmap slice to disk and free the numpy buffer
        matrix.flush()
        del emb

        if device == "cuda":
            torch.cuda.empty_cache()

        if batch_idx % 10 == 0:
            gc.collect()
            if psutil is not None:
                vm = psutil.virtual_memory()
                LOGGER.info(
                    "Batch %d/%d | RAM used: %.1f GB / %.1f GB",
                    batch_idx + 1,
                    (len(docs) + batch_size - 1) // batch_size,
                    (vm.total - vm.available) / 1024**3,
                    vm.total / 1024**3,
                )

    # Close memmap — this unmaps the file from address space
    del matrix
    gc.collect()

    gpu_peak_mb = 0.0
    if device == "cuda":
        gpu_peak_mb = torch.cuda.max_memory_allocated() / (1024**2)

    finished = time.time()
    duration = max(1e-8, finished - started)

    report = RunReport(
        status="success",
        started_at=started_at,
        finished_at=datetime.now().isoformat(),
        duration_seconds=duration,
        device=device,
        model=model_name,
        embedding_dimension=emb_dim,
        total_documents=len(docs),
        total_characters=total_chars,
        avg_characters_per_doc=(total_chars / len(docs)) if docs else 0.0,
        batch_size=batch_size,
        normalize_embeddings=normalize_embeddings,
        fp16=bool(fp16 and device == "cuda"),
        outputs={
            "embeddings_npy": str(output_embeddings_file.resolve()),
            "metadata_manifest_jsonl": str(output_manifest_file.resolve()),
        },
        throughput_docs_per_sec=len(docs) / duration,
        throughput_chars_per_sec=total_chars / duration,
        gpu_peak_memory_mb=gpu_peak_mb,
        cpu_cores_used=threads_used,
        torch_num_threads=torch.get_num_threads(),
        input_sources={},
        notes=[
            "Embeddings written as float32 .npy in row order matching metadata_manifest_jsonl",
            "Use the same model for query encoding during retrieval",
            "Double-chunking fix: pre-chunked scraped docs are flagged and skipped in chunk_docs()",
            "OOM recovery: batch size auto-halves on GPU OOM and retries",
        ],
    )

    return report


def save_reports(report: RunReport, report_json_file: Path, report_txt_file: Path) -> None:
    report_json_file.parent.mkdir(parents=True, exist_ok=True)
    report_txt_file.parent.mkdir(parents=True, exist_ok=True)

    report_json_file.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    lines = [
        "Embedding Run Report",
        "=" * 80,
        f"Status                 : {report.status}",
        f"Started At             : {report.started_at}",
        f"Finished At            : {report.finished_at}",
        f"Duration (sec)         : {report.duration_seconds:.3f}",
        f"Model                  : {report.model}",
        f"Device                 : {report.device}",
        f"Embedding Dimension    : {report.embedding_dimension}",
        f"Documents              : {report.total_documents}",
        f"Total Characters       : {report.total_characters}",
        f"Avg Chars / Doc        : {report.avg_characters_per_doc:.2f}",
        f"Batch Size             : {report.batch_size}",
        f"Normalize Embeddings   : {report.normalize_embeddings}",
        f"FP16                   : {report.fp16}",
        f"Throughput (docs/sec)  : {report.throughput_docs_per_sec:.2f}",
        f"Throughput (chars/sec) : {report.throughput_chars_per_sec:.2f}",
        f"GPU Peak Memory (MB)   : {report.gpu_peak_memory_mb:.2f}",
        f"CPU Cores Used         : {report.cpu_cores_used}",
        f"Torch Num Threads      : {report.torch_num_threads}",
        "",
        "Outputs:",
        f"- Embeddings (.npy): {report.outputs['embeddings_npy']}",
        f"- Metadata (.jsonl): {report.outputs['metadata_manifest_jsonl']}",
        "",
        "Notes:",
    ]
    lines.extend([f"- {n}" for n in report.notes])
    report_txt_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="High-throughput embedding creation")

    parser.add_argument("--input-jsonl", type=Path, default=Path("./RAGData/embeddings.jsonl"))
    parser.add_argument("--input-dir", type=Path, default=Path("./ScrappedData"))
    parser.add_argument("--output-dir", type=Path, default=Path("./Embeddings"))
    parser.add_argument("--output-prefix", type=str, default="bge_base_en_v1_5")
    parser.add_argument(
        "--combine-sources",
        action="store_true",
        help="Combine --input-jsonl and --input-dir inputs (deduplicated by doc_id)",
    )

    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=0, help="0 = auto-tune")
    parser.add_argument("--max-batch-size", type=int, default=128)  # raised for 15GB GPU
    parser.add_argument("--cpu-threads", type=int, default=0)

    parser.add_argument("--force-cpu", action="store_true")
    parser.add_argument("--no-fp16", action="store_true")
    parser.add_argument("--no-normalize", action="store_true")

    args, _ = parser.parse_known_args()
    return args


def main() -> None:
    args = parse_args()
    setup_logging(args.output_dir)

    LOGGER.info("=" * 90)
    LOGGER.info("Embedding pipeline started")
    LOGGER.info("=" * 90)

    input_jsonl = args.input_jsonl if args.input_jsonl and args.input_jsonl.exists() else None
    scraped_dir = args.input_dir if args.input_dir and args.input_dir.exists() else None

    docs = load_all_documents(
        input_jsonl=input_jsonl,
        scraped_dir=scraped_dir,
        combine_sources=args.combine_sources,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = args.output_prefix
    embeddings_file = output_dir / f"{stem}_embeddings.npy"
    manifest_file = output_dir / f"{stem}_manifest.jsonl"
    report_json_file = output_dir / f"{stem}_run_report.json"
    report_txt_file = output_dir / f"{stem}_run_report.txt"

    report = build_embeddings(
        docs=docs,
        model_name=args.model,
        output_embeddings_file=embeddings_file,
        output_manifest_file=manifest_file,
        batch_size=args.batch_size,
        max_batch_size=args.max_batch_size,
        normalize_embeddings=not args.no_normalize,
        force_cpu=args.force_cpu,
        fp16=not args.no_fp16,
        cpu_threads=args.cpu_threads if args.cpu_threads > 0 else None,
    )

    report.input_sources = {
        "input_jsonl": str(input_jsonl.resolve()) if input_jsonl else "",
        "input_dir": str(scraped_dir.resolve()) if scraped_dir else "",
    }

    if psutil is not None:
        vm = psutil.virtual_memory()
        report.notes.append(f"System RAM total GB: {vm.total / (1024 ** 3):.2f}")

    save_reports(report, report_json_file=report_json_file, report_txt_file=report_txt_file)

    LOGGER.info("Embedding pipeline completed successfully")
    LOGGER.info("Embeddings file: %s", embeddings_file.resolve())
    LOGGER.info("Manifest file  : %s", manifest_file.resolve())
    LOGGER.info("Report (JSON)  : %s", report_json_file.resolve())
    LOGGER.info("Report (TXT)   : %s", report_txt_file.resolve())


if __name__ == "__main__":
    main()