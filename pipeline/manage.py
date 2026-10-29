"""Maintenance commands for agents and the user.

    python -m pipeline.manage check                      # verify .env, MongoDB, Blob, Azure Speech
    python -m pipeline.manage smoke                      # tiny real TTS -> Blob -> Mongo round trip, then cleanup
    python -m pipeline.manage recent [--workflow quiz] [--limit 20]
    python -m pipeline.manage link --lesson-id <id>      # fresh listen link
    python -m pipeline.manage delete --lesson-id <id> [--yes]
    python -m pipeline.manage delete --run-id <run> [--yes]
    python -m pipeline.manage delete --date 2026-10-28 [--workflow quiz] [--yes]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from pipeline import blob as blob_store
from pipeline import mongo, tts
from pipeline.config import VOICE_ROTATION, WORKFLOWS, load_settings


def _collections(db, workflow: str | None):
    names = [workflow] if workflow else list(WORKFLOWS)
    return [mongo.get_collection(db, name) for name in names]


def cmd_check(_args) -> int:
    settings = load_settings()
    ok = True

    try:
        db = mongo.get_database(settings)
        db.client.admin.command("ping")
        counts = {name: db[coll].count_documents({"status": "published"}) for name, coll in WORKFLOWS.items()}
        print(f"MongoDB      OK  database '{settings.mongo_db_name}', published lessons: {counts}")
    except Exception as exc:
        ok = False
        print(f"MongoDB      FAIL {exc}")

    try:
        container = blob_store.get_container(settings)
        public = blob_store.is_public(container)
        print(f"Blob         OK  container '{settings.storage_container}' (public access: {'on' if public else 'off'})")
    except Exception as exc:
        ok = False
        print(f"Blob         FAIL {exc}")

    try:
        voices = {v["ShortName"] for v in tts.list_voices(settings)}
        missing = [v for v in VOICE_ROTATION if v not in voices]
        if missing:
            ok = False
            print(f"Azure Speech FAIL voices unavailable in region '{settings.speech_region}': {missing}")
        else:
            print(f"Azure Speech OK  region '{settings.speech_region}', {len(voices)} fr-FR voices available")
    except Exception as exc:
        ok = False
        print(f"Azure Speech FAIL {exc}")

    return 0 if ok else 1


def cmd_smoke(_args) -> int:
    """Exercise TTS -> Blob -> MongoDB -> verify -> cleanup with a tiny clip (about 150 billed characters)."""
    settings = load_settings()
    db = mongo.get_database(settings)
    collection = mongo.get_collection(db, "quiz")
    container = blob_store.get_container(settings)
    now = datetime.now(timezone.utc)
    lesson_id = f"smoke-{now:%Y%m%d%H%M%S}"
    blob_path = f"smoke/{lesson_id}.mp3"
    script = (
        "Bonjour ! Ceci est un test du service de synthèse vocale.\n\n"
        "Si vous entendez cette phrase, la chaîne de publication fonctionne."
    )

    inserted_id = None
    uploaded = False
    try:
        result = tts.synthesize(settings, script, VOICE_ROTATION[0])
        blob_store.upload_audio(container, blob_path, result.audio)
        uploaded = True
        inserted_id = collection.insert_one(
            {"lessonId": lesson_id, "status": "smoke", "createdAt": now, "audio": {"blobPath": blob_path}}
        ).inserted_id
        size = blob_store.blob_size(container, blob_path)
        assert size == len(result.audio), "blob size mismatch"
        assert collection.find_one({"_id": inserted_id}) is not None, "document not readable"
        print(
            f"Smoke OK: {result.requests_made} TTS request(s), {len(result.audio)} bytes, "
            f"~{result.duration_sec}s audio, blob and document verified"
        )
        return 0
    except Exception as exc:
        print(f"Smoke FAIL: {exc}")
        return 1
    finally:
        if inserted_id is not None:
            collection.delete_one({"_id": inserted_id})
        if uploaded:
            blob_store.delete_audio(container, blob_path)
        print("Smoke test artifacts cleaned up.")


def cmd_recent(args) -> int:
    db = mongo.get_database(load_settings())
    for collection in _collections(db, args.workflow):
        print(f"\n== {collection.name} ==")
        cursor = collection.find({"status": "published"}).sort("createdAt", -1).limit(args.limit)
        for doc in cursor:
            print(f"- {doc['createdAt']:%Y-%m-%d} | {doc['difficulty']} | {doc['titleFr']}  ({doc['lessonId']})")
            for source in doc.get("sources", []):
                print(f"    source: {source['url']}")
    return 0


def _find_lesson(db, lesson_id: str):
    for collection in _collections(db, None):
        doc = collection.find_one({"lessonId": lesson_id})
        if doc:
            return collection, doc
    return None, None


def cmd_link(args) -> int:
    settings = load_settings()
    db = mongo.get_database(settings)
    _, doc = _find_lesson(db, args.lesson_id)
    if not doc:
        print(f"Lesson not found: {args.lesson_id}")
        return 1
    container = blob_store.get_container(settings, create=False)
    if doc["audio"].get("isPublic"):
        print(doc["audio"]["url"])
    else:
        print(blob_store.signed_read_url(container, settings, doc["audio"]["blobPath"]))
    return 0


def cmd_delete(args) -> int:
    settings = load_settings()
    db = mongo.get_database(settings)
    if args.lesson_id:
        query = {"lessonId": args.lesson_id}
    elif args.run_id:
        query = {"runId": args.run_id}
    else:
        day = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        query = {"createdAt": {"$gte": day, "$lt": day + timedelta(days=1)}}

    targets = [(c, d) for c in _collections(db, args.workflow) for d in c.find(query)]
    if not targets:
        print("No matching lessons.")
        return 0
    for collection, doc in targets:
        print(f"- [{collection.name}] {doc['titleFr']} ({doc['lessonId']}) blob={doc.get('audio', {}).get('blobPath')}")
    if not args.yes:
        print(f"\n{len(targets)} lesson(s) would be deleted. Re-run with --yes to confirm.")
        return 0

    container = blob_store.get_container(settings, create=False)
    for collection, doc in targets:
        blob_path = doc.get("audio", {}).get("blobPath")
        if blob_path:
            blob_store.delete_audio(container, blob_path)
        collection.delete_one({"_id": doc["_id"]})
    print(f"Deleted {len(targets)} lesson(s) and their audio.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="French lesson maintenance")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check")
    sub.add_parser("smoke")

    recent = sub.add_parser("recent")
    recent.add_argument("--workflow", choices=sorted(WORKFLOWS))
    recent.add_argument("--limit", type=int, default=20)

    link = sub.add_parser("link")
    link.add_argument("--lesson-id", required=True)

    delete = sub.add_parser("delete")
    target = delete.add_mutually_exclusive_group(required=True)
    target.add_argument("--lesson-id")
    target.add_argument("--run-id")
    target.add_argument("--date", help="YYYY-MM-DD (UTC creation date)")
    delete.add_argument("--workflow", choices=sorted(WORKFLOWS))
    delete.add_argument("--yes", action="store_true")

    args = parser.parse_args()
    handlers = {
        "check": cmd_check,
        "smoke": cmd_smoke,
        "recent": cmd_recent,
        "link": cmd_link,
        "delete": cmd_delete,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
