from datetime import date, datetime

from backend.utils.scoring import score_obligation

from backend.services.risk_analysis import apply_risk_analysis

def _to_float(value, default=0.0) -> float:
	try:
		if value is None:
			return float(default)
		return float(value)
	except (TypeError, ValueError):
		return float(default)


def _parse_due_date(value):
	if value is None:
		return None
	try:
		return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
	except (TypeError, ValueError):
		return None


def _build_due_credit_simulation(start_balance: float, due_credits: list[dict]) -> list[dict]:
	if not due_credits:
		return []

	balance = float(start_balance)
	ordered = sorted(due_credits, key=lambda item: item["date"])
	simulation = []

	for item in ordered:
		balance += float(item["amount"])
		simulation.append(
			{
				"date": item["date"].strftime("%Y-%m-%d"),
				"projected_balance": float(balance),
			}
		)

	return simulation


def run_decision_engine(cash_balance: float, obligations: list[dict], transactions: list[dict] | None = None) -> dict:
	current_balance = _to_float(cash_balance, default=0.0)
	input_obligations = [item.copy() for item in obligations if isinstance(item, dict)] if isinstance(obligations, list) else []
	input_transactions = transactions if isinstance(transactions, list) else []
	today = date.today()
	due_credits = []
	rejected_transactions = []

	for tx in input_transactions:
		if not isinstance(tx, dict):
			continue

		tx_type = str(tx.get("type") or "").strip().lower()
		amount = max(0.0, _to_float(tx.get("amount"), default=0.0))
		tx_date = _parse_due_date(tx.get("date")) or today
		vendor = str(tx.get("vendor") or "Transaction").strip() or "Transaction"

		if tx_type == "immediate_credit":
			current_balance += amount
			continue

		if tx_type == "immediate_debit":
			if amount > current_balance:
				rejected_transactions.append(
					{
						"type": tx_type,
						"amount": amount,
						"date": tx_date.strftime("%Y-%m-%d"),
						"vendor": vendor,
						"reason": "insufficient_cash_balance",
					}
				)
				continue
			current_balance -= amount
			continue

		if tx_type == "due_credit":
			due_credits.append({"amount": amount, "date": tx_date})
			continue

		if tx_type == "due_debit":
			input_obligations.append(
				{
					"id": tx.get("id") or f"tx-ob-{len(input_obligations) + 1}",
					"vendor": vendor,
					"description": tx.get("description") or vendor,
					"amount": amount,
					"amount_paid": _to_float(tx.get("amount_paid"), default=0.0),
					"due_date": tx_date.strftime("%Y-%m-%d"),
					"penalty_if_late": max(0.0, _to_float(tx.get("penalty_if_late"), default=0.0)),
					"flexibility": str(tx.get("flexibility") or "medium").strip().lower() or "medium",
				}
			)

	processed_obligations = []
	total_obligations = 0.0

	for item in input_obligations:
		obligation = item.copy() if isinstance(item, dict) else {}

		score = score_obligation(obligation)
		obligation["score"] = float(score)

		amount = _to_float(obligation.get("amount"), default=0.0)
		amount_paid = _to_float(obligation.get("amount_paid"), default=0.0)
		remaining = max(0.0, amount - amount_paid)
		penalty_if_late = max(0.0, _to_float(obligation.get("penalty_if_late"), default=0.0))

		due_date = _parse_due_date(obligation.get("due_date"))
		if due_date is None:
			status = "upcoming"
		elif due_date < today:
			status = "overdue"
		elif due_date == today:
			status = "due-today"
		else:
			status = "upcoming"
		obligation["status"] = status

		penalty_applied = penalty_if_late if status == "overdue" and remaining > 0 else 0.0
		amount_due = remaining + penalty_applied
		obligation["penalty_applied"] = float(penalty_applied)
		obligation["amount_due"] = float(amount_due)
		total_obligations += amount_due

		processed_obligations.append(obligation)

	processed_obligations.sort(
		key=lambda o: (
			-_to_float(o.get("score"), default=0.0),
			-_to_float(o.get("penalty_if_late"), default=0.0),
			str(o.get("vendor") or "").strip().lower(),
		)
	)
	processed_obligations = apply_risk_analysis(current_balance, processed_obligations)
	ending_balance = max(0.0, current_balance - total_obligations)
	simulation = _build_due_credit_simulation(ending_balance, due_credits)

	shortfall = max(0.0, total_obligations - current_balance)
	avg_daily_burn = total_obligations / 30.0 if total_obligations > 0 else 0.0
	days_to_zero = int(max(0.0, current_balance) / avg_daily_burn) if avg_daily_burn > 0 else 999
	total_can_pay = sum(1 for item in processed_obligations if item.get("can_pay") is True)
	total_deferred = max(0, len(processed_obligations) - total_can_pay)
	all_covered = shortfall == 0.0
	reasoning = (
		"All obligations can be covered with current cash balance."
		if all_covered
		else "Cash balance is insufficient to cover all obligations; prioritize high-score items first."
	)

	return {
		"cash_balance": float(ending_balance),
		"total_obligations": float(total_obligations),
		"shortfall": float(shortfall),
		"days_to_zero": int(days_to_zero),
		"prioritized_obligations": processed_obligations,
		"simulation": simulation,
		"rejected_transactions": rejected_transactions,
		"reasoning": reasoning,
		"summary": {
			"total_can_pay": int(total_can_pay),
			"total_deferred": int(total_deferred),
			"all_covered": bool(all_covered),
		},
	}
