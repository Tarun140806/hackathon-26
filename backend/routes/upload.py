import os
import tempfile
from datetime import date

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.ingestion.csv_parser import parse_bank_csv
from backend.ingestion.ocr import parse_image_file
from backend.ingestion.pdf_parser import parse_pdf_file
from backend.services.mongo_service import save_upload_event


router = APIRouter(prefix="/upload", tags=["upload"])


def _to_obligations_from_transactions(transactions: list[dict]) -> list[dict]:
	obligations = []
	for tx in transactions:
		tx_type = str(tx.get("type") or "").strip().lower()
		amount = abs(float(tx.get("amount") or 0.0))
		is_debit_type = tx_type in {"immediate_debit", "due_debit", "debit"}

		# Support both typed transaction rows and legacy negative-amount rows.
		if not is_debit_type and float(tx.get("amount") or 0.0) >= 0:
			continue
		if amount <= 0:
			continue

		description = str(tx.get("description") or "Transaction").strip()
		obligations.append(
			{
				"id": f"imp-{len(obligations) + 1}",
				"vendor": description[:60] or "Transaction",
				"description": description,
				"amount": amount,
				"amount_paid": 0,
				"due_date": tx.get("date") or str(date.today()),
				"penalty_if_late": float(tx.get("penalty_if_late") or 0),
				"flexibility": "medium",
			}
		)

	return obligations


@router.post("/document")
async def upload_document(file: UploadFile = File(...)) -> dict:
	if not file.filename:
		raise HTTPException(status_code=400, detail="Missing file name")

	filename = file.filename.lower()
	_, ext = os.path.splitext(filename)

	allowed = {".csv", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
	if ext not in allowed:
		raise HTTPException(status_code=400, detail="Unsupported file type")

	with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
		tmp_path = tmp.name
		content = await file.read()
		tmp.write(content)

	try:
		if ext == ".csv":
			parsed = parse_bank_csv(tmp_path)
			transactions = parsed.get("transactions", [])
			obligations = _to_obligations_from_transactions(transactions)
			response_payload = {
				"source_type": "csv",
				"cash_balance": float(parsed.get("cash_balance", 0.0) or 0.0),
				"transactions": transactions,
				"obligations": obligations,
			}
			upload_id = save_upload_event(file.filename, "csv", response_payload)
			if upload_id:
				response_payload["upload_id"] = upload_id
			return response_payload

		if ext == ".pdf":
			parsed = parse_pdf_file(tmp_path, file.filename)
			response_payload = {
				"source_type": "pdf",
				"cash_balance": 0.0,
				"obligations": parsed,
			}
			upload_id = save_upload_event(file.filename, "pdf", response_payload)
			if upload_id:
				response_payload["upload_id"] = upload_id
			return response_payload

		parsed = parse_image_file(tmp_path, file.filename)
		response_payload = {
			"source_type": "image",
			"cash_balance": 0.0,
			"obligations": parsed,
		}
		upload_id = save_upload_event(file.filename, "image", response_payload)
		if upload_id:
			response_payload["upload_id"] = upload_id
		return response_payload
	finally:
		if os.path.exists(tmp_path):
			os.unlink(tmp_path)
