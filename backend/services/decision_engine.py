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


def run_decision_engine(cash_balance: float, obligations: list[dict]) -> dict:
	current_balance = max(0.0, _to_float(cash_balance, default=0.0))
	input_obligations = obligations if isinstance(obligations, list) else []
	today = date.today()

	processed_obligations = []
	total_obligations = 0.0

	for item in input_obligations:
		obligation = item.copy() if isinstance(item, dict) else {}

		score = score_obligation(obligation)
		obligation["score"] = float(score)

		amount = _to_float(obligation.get("amount"), default=0.0)
		amount_paid = _to_float(obligation.get("amount_paid"), default=0.0)
		remaining = max(0.0, amount - amount_paid)
		total_obligations += remaining

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

		processed_obligations.append(obligation)

	processed_obligations.sort(
		key=lambda o: (
			-_to_float(o.get("score"), default=0.0),
			-_to_float(o.get("penalty_if_late"), default=0.0),
			str(o.get("vendor") or "").strip().lower(),
		)
	)
	processed_obligations = apply_risk_analysis(current_balance, processed_obligations)

	shortfall = max(0.0, total_obligations - current_balance)
	avg_daily_burn = total_obligations / 30.0 if total_obligations > 0 else 0.0
	days_to_zero = int(current_balance / avg_daily_burn) if avg_daily_burn > 0 else 999
	total_can_pay = sum(1 for item in processed_obligations if item.get("can_pay") is True)
	total_deferred = max(0, len(processed_obligations) - total_can_pay)
	all_covered = shortfall == 0.0
	reasoning = (
		"All obligations can be covered with current cash balance."
		if all_covered
		else "Cash balance is insufficient to cover all obligations; prioritize high-score items first."
	)

	return {
		"cash_balance": float(current_balance),
		"total_obligations": float(total_obligations),
		"shortfall": float(shortfall),
		"days_to_zero": int(days_to_zero),
		"prioritized_obligations": processed_obligations,
		"simulation": [],
		"reasoning": reasoning,
		"summary": {
			"total_can_pay": int(total_can_pay),
			"total_deferred": int(total_deferred),
			"all_covered": bool(all_covered),
		},
	}
