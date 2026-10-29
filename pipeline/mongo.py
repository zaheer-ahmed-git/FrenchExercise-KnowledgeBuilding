from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from pipeline.config import WORKFLOWS, Settings


def get_database(settings: Settings) -> Database:
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=15_000, appname="french-lesson-pipeline")
    return client[settings.mongo_db_name]


def get_collection(db: Database, workflow: str) -> Collection:
    collection = db[WORKFLOWS[workflow]]
    collection.create_index([("lessonId", ASCENDING)], unique=True)
    collection.create_index([("status", ASCENDING), ("createdAt", DESCENDING)])
    collection.create_index([("runId", ASCENDING)])
    return collection
