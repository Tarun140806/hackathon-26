import os
import re

import pandas as pd


VALID_TRANSACTION_TYPES = {
	"immediate_credit",
	"immediate_debit",
	"due_credit",
	"due_debit",
}


def _find_column(columns, aliases):
	for alias in aliases:
		if alias in columns:
			return alias
	return None


def _to_float(value):
	if pd.isna(value):
		return None
	text = str(value).strip()
	if not text:
		return None

	# Keep digits, sign, and decimal point; remove currency signs and separators.
	cleaned = re.sub(r"[^0-9.\-+]", "", text.replace(",", ""))
	if cleaned in {"", "+", "-", ".", "+.", "-."}:
		return None

	try:
		return float(cleaned)
	except ValueError:
		return None


def _normalize_transaction_type(value):
	if pd.isna(value):
		return None
	text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
	return text if text in VALID_TRANSACTION_TYPES else None


def parse_bank_csv(file_path: str) -> dict:
	if not file_path or not os.path.exists(file_path):
		return {"cash_balance": 0.0, "transactions": []}

	try:
		df = pd.read_csv(file_path)
	except Exception:
		return {"cash_balance": 0.0, "transactions": []}

	if df.empty:
		return {"cash_balance": 0.0, "transactions": []}

	df.columns = [str(col).strip().lower() for col in df.columns]
	columns = set(df.columns)

	date_col = _find_column(columns, ["date", "transaction date"])
	desc_col = _find_column(columns, ["description", "narration", "details"])
	amount_col = _find_column(columns, ["amount"])
	debit_col = _find_column(columns, ["debit"])
	credit_col = _find_column(columns, ["credit"])
	balance_col = _find_column(columns, ["balance", "running balance", "closing balance"])
	type_col = _find_column(columns, ["type", "transaction_type", "transaction type"])
	due_date_col = _find_column(columns, ["due_date", "due date"])

	if not date_col or not desc_col or (not amount_col and not (debit_col or credit_col)):
		return {"cash_balance": 0.0, "transactions": []}

	transactions = []
	running_balance = 0.0
	last_balance = None

	for _, row in df.iterrows():
		raw_date = row.get(date_col)
		raw_description = row.get(desc_col)

		parsed_date = pd.to_datetime(raw_date, errors="coerce")
		if pd.isna(parsed_date):
			continue

		description = "" if pd.isna(raw_description) else str(raw_description).strip()
		if not description:
			continue

		amount = None
		if amount_col:
			amount = _to_float(row.get(amount_col))

		# If amount is unavailable for this row, fall back to credit - debit when present.
		if amount is None and (debit_col or credit_col):
			debit_value = _to_float(row.get(debit_col)) if debit_col else 0.0
			credit_value = _to_float(row.get(credit_col)) if credit_col else 0.0

			if debit_value is None:
				debit_value = 0.0
			if credit_value is None:
				credit_value = 0.0

			amount = credit_value - debit_value

		if amount is None:
			continue

		parsed_due_date = None
		if due_date_col:
			raw_due_date = row.get(due_date_col)
			parsed_due_date = pd.to_datetime(raw_due_date, errors="coerce")
			if pd.isna(parsed_due_date):
				parsed_due_date = None

		tx_type = _normalize_transaction_type(row.get(type_col)) if type_col else None
		if tx_type is None:
			if amount > 0:
				tx_type = "immediate_credit"
			elif amount < 0:
				tx_type = "immediate_debit"
			else:
				continue

		if tx_type.startswith("immediate"):
			running_balance += amount

		if balance_col:
			parsed_balance = _to_float(row.get(balance_col))
			if parsed_balance is not None:
				last_balance = parsed_balance

		tx_date = parsed_date
		if tx_type.startswith("due") and parsed_due_date is not None:
			tx_date = parsed_due_date

		transactions.append(
			{
				"type": tx_type,
				"date": tx_date.strftime("%Y-%m-%d"),
				"description": description,
				"vendor": description,
				"amount": abs(float(amount)),
			}
		)

	if not transactions:
		return {"cash_balance": 0.0, "transactions": []}

	cash_balance = float(last_balance) if last_balance is not None else float(running_balance)
	return {"cash_balance": cash_balance, "transactions": transactions}
