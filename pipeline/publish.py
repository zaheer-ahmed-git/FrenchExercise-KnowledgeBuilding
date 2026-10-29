"""Publish a staged batch of lessons: TTS -> Blob -> MongoDB -> verify -> report.

All-or-nothing: documents are inserted as 'pending' and only flipped to
'published' after every lesson verifies. Any failure deletes this run's
blobs and documents.

Usage:
    python -m pipeline.publish --workflow quiz --staging lessons/staging/<run-folder>
    python -m pipeline.publish --workflow quiz --staging lessons/staging/<run-folder> --dry-run
"""

import argparse
import random
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from pipeline import blob as blob_store
from pipeline import mongo, tts
from pipeline.config import (
    AUDIO_CONTENT_TYPE,
    AUDIO_FORMAT,
    DEFAULT_SPEAKING_RATE,
    DURATION_TARGET_SEC,
    VOICE_ROTATION,
    WORKFLOWS,
    load_settings,
)
from pipeline.lessons import build_document, load_staging, shuffle_quiz_options
from pipeline.report import write_failure_report, write_success_report
from pipeline.validate import validate_batch, verify_stored_document


def _print_findings(findings) -> None:
    for warning in findings.warnings:
        print(f"  WARN  {warning}")
    for error in findings.errors:
        print(f"  ERROR {error}")


def _previously_used_sources(db) -> set[str]:
    urls: set[str] = set()
    for collection_name in WORKFLOWS.values():
        for doc in db[collection_name].find({"status": "published"}, {"sources.url": 1}):
            urls.update(s["url"] for s in doc.get("sources", []))
    return urls


def _rollback(collection, container, inserted_ids: list, uploaded_blobs: list[str]) -> list[str]:
    """Best-effort cleanup; each step is isolated so one failing service doesn't block the other."""
    log = []
    if inserted_ids:
        try:
            deleted = collection.delete_many({"_id": {"$in": inserted_ids}}).deleted_count
            log.append(f"Deleted {deleted}/{len(inserted_ids)} MongoDB document(s)")
        except Exception as exc:
            log.append(f"MANUAL CLEANUP NEEDED: could not delete MongoDB ids {inserted_ids}: {exc}")
    for blob_path in uploaded_blobs:
        try:
            removed = blob_store.delete_audio(container, blob_path)
            log.append(f"{'Deleted' if removed else 'Already absent'} blob `{blob_path}`")
        except Exception as exc:
            log.append(f"MANUAL CLEANUP NEEDED: could not delete blob `{blob_path}`: {exc}")
    return log


def run(workflow: str, staging_dir: Path, dry_run: bool) -> int:
    started_at = datetime.now(timezone.utc)
    run_id = f"{started_at:%Y-%m-%d-%H%M%S}-{workflow}"

    staged = load_staging(staging_dir)
    print(f"Run {run_id}: {len(staged)} staged lesson(s) from {staging_dir}")
    findings = validate_batch(workflow, [(path.name, data) for path, data in staged])
    _print_findings(findings)
    if findings.errors:
        print("Validation failed. Fix the staging JSON; no Azure or MongoDB calls were made.")
        return 1
    if dry_run:
        print("Dry run OK: staging files are valid.")
        return 0

    settings = load_settings()
    db = mongo.get_database(settings)
    db.client.admin.command("ping")
    collection = mongo.get_collection(db, workflow)
    container = blob_store.get_container(settings)
    container_public = blob_store.is_public(container)

    used_sources = _previously_used_sources(db)
    warnings = list(findings.warnings)
    for path, data in staged:
        reused = [s["url"] for s in data["sources"] if s["url"] in used_sources]
        if reused:
            warnings.append(f"{path.name}: sources already used in earlier lessons: {', '.join(reused)}")
            print(f"  WARN  {warnings[-1]}")

    uploaded_blobs: list[str] = []
    inserted_ids: list = []
    rng = random.Random()
    voice_offset = collection.count_documents({})

    try:
        docs = []
        for position, (path, data) in enumerate(staged):
            doc = build_document(workflow, data, run_id=run_id, created_at=started_at)
            if workflow == "quiz":
                shuffle_quiz_options(doc, rng)

            voice = data.get("voiceName") or VOICE_ROTATION[(voice_offset + position) % len(VOICE_ROTATION)]
            rate = data.get("speakingRate") or DEFAULT_SPEAKING_RATE
            print(f"[{position + 1}/{len(staged)}] {doc['titleFr']} -> TTS with {voice}")
            result = tts.synthesize(settings, doc["scriptFull"], voice, rate)

            blob_path = blob_store.build_blob_path(workflow, doc["lessonId"], started_at)
            audio_url = blob_store.upload_audio(container, blob_path, result.audio)
            uploaded_blobs.append(blob_path)

            doc["audio"] = {
                "url": audio_url,
                "blobPath": blob_path,
                "container": settings.storage_container,
                "isPublic": container_public,
                "contentType": AUDIO_CONTENT_TYPE,
                "format": AUDIO_FORMAT,
                "bytes": len(result.audio),
                "durationSec": result.duration_sec,
                "voiceName": voice,
                "speakingRate": rate,
                "ttsCharacters": result.characters,
                "ttsRequests": result.requests_made,
            }
            doc["_id"] = collection.insert_one(doc).inserted_id
            inserted_ids.append(doc["_id"])

            low, high = DURATION_TARGET_SEC
            if not low <= result.duration_sec <= high:
                warnings.append(f"{path.name}: audio is {result.duration_sec / 60:.1f} min (target 6-10 min)")
                print(f"  WARN  {warnings[-1]}")
            docs.append(doc)

        for doc in docs:
            stored = collection.find_one({"_id": doc["_id"]})
            if stored is None:
                raise RuntimeError(f"{doc['lessonId']}: document not found after insert")
            problems = verify_stored_document(stored)
            if problems:
                raise RuntimeError(f"{doc['lessonId']}: {'; '.join(problems)}")
            size = blob_store.blob_size(container, doc["audio"]["blobPath"])
            if size != doc["audio"]["bytes"]:
                raise RuntimeError(f"{doc['lessonId']}: blob size {size} != synthesized {doc['audio']['bytes']}")

        published_at = datetime.now(timezone.utc)
        update = collection.update_many(
            {"_id": {"$in": inserted_ids}}, {"$set": {"status": "published", "publishedAt": published_at}}
        )
        if update.modified_count != len(inserted_ids):
            raise RuntimeError(f"only {update.modified_count}/{len(inserted_ids)} documents were marked published")

    except BaseException as exc:  # includes Ctrl+C so an interrupted run still cleans up
        cleanup_log = _rollback(collection, container, inserted_ids, uploaded_blobs)
        error = "".join(traceback.format_exception(exc))
        report = write_failure_report(run_id=run_id, workflow=workflow, error=error, cleanup_log=cleanup_log)
        print(f"\nRUN FAILED: {exc}\nCleanup done. Failure report: {report}")
        return 1

    report = write_success_report(
        run_id=run_id,
        workflow=workflow,
        collection=collection.name,
        started_at=started_at,
        docs=docs,
        warnings=warnings,
        container_public=container_public,
    )
    print(f"\nRUN SUCCEEDED: {len(docs)} lesson(s) published to '{collection.name}'. Report: {report}")
    print(f"\nListen links ({'public' if container_public else f'valid {settings.audio_sas_hours}h, do not commit'}):")
    for doc in docs:
        url = (
            doc["audio"]["url"]
            if container_public
            else blob_store.signed_read_url(container, settings, doc["audio"]["blobPath"])
        )
        print(f"- {doc['titleFr']}: {url}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish staged French lessons")
    parser.add_argument("--workflow", required=True, choices=sorted(WORKFLOWS))
    parser.add_argument("--staging", required=True, type=Path, help="Folder containing one JSON file per lesson")
    parser.add_argument("--dry-run", action="store_true", help="Validate staging files only; no external calls")
    args = parser.parse_args()
    if not args.staging.is_dir():
        sys.exit(f"Staging folder not found: {args.staging}")
    sys.exit(run(args.workflow, args.staging, args.dry_run))


if __name__ == "__main__":
    main()
