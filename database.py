from pymongo import MongoClient

from config import settings

client = MongoClient(settings.mongodb_uri)
db = client[settings.database_name]

contracts_collection = db["contracts"]
analyses_collection = db["analysis"]


def init_indexes() -> None:
    contracts_collection.create_index(
        "contract_id",
        unique=True
    )

    analyses_collection.create_index(
        "analysis_id",
        unique=True
    )