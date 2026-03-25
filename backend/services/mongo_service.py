import os
from datetime import datetime, timezone

from pymongo import MongoClient


_client = None
_db = None


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def get_db():
	global _client, _db
	if _db is not None:
		return _db

	mongo_uri = os.getenv("MONGODB_URI", "").strip()
	db_name = os.getenv("MONGODB_DB", "cashclear")
	if not mongo_uri:
		return None

	try:
		_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
		_client.admin.command("ping")
		_db = _client[db_name]
		return _db
	except Exception:
		_client = None
		_db = None
		return None


def save_upload_event(file_name: str, source_type: str, result_payload: dict) -> str | None:
	db = get_db()
	if db is None:
		return None

	document = {
		"created_at": _utc_now_iso(),
		"file_name": file_name,
		"source_type": source_type,
		"result": result_payload,
	}
	inserted = db.uploads.insert_one(document)
	return str(inserted.inserted_id)


def save_analysis_event(cash_balance: float, obligations: list[dict], analysis_result: dict) -> str | None:
	db = get_db()
	if db is None:
		return None

	document = {
		"created_at": _utc_now_iso(),
		"cash_balance": cash_balance,
		"obligations": obligations,
		"result": analysis_result,
	}
	inserted = db.analyses.insert_one(document)
	analysis_id = str(inserted.inserted_id)

	prioritized = analysis_result.get("prioritized_obligations", [])
	if isinstance(prioritized, list) and prioritized:
		items = []
		for item in prioritized:
			if not isinstance(item, dict):
				continue
			row = item.copy()
			row["analysis_id"] = analysis_id
			row["created_at"] = _utc_now_iso()
			items.append(row)
		if items:
			db.obligations.insert_many(items)

	return analysis_id
