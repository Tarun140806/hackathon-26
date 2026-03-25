import os
from datetime import date


def parse_pdf_file(file_path: str, original_name: str | None = None) -> list[dict]:
	name = original_name or os.path.basename(file_path)
	vendor = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip() or "PDF Document"

	# Placeholder extraction: document is imported and converted into a reviewable obligation.
	return [
		{
			"id": "pdf-1",
			"vendor": vendor[:60],
			"description": f"Imported from PDF: {name}",
			"amount": 0,
			"amount_paid": 0,
			"due_date": str(date.today()),
			"penalty_if_late": 0,
			"flexibility": "medium",
		}
	]
