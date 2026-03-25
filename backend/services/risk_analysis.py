def _to_float(value, default=0.0) -> float:
	try:
		if value is None:
			return float(default)
		return float(value)
	except (TypeError, ValueError):
		return float(default)


def apply_risk_analysis(cash_balance: float, obligations: list[dict]) -> list[dict]:
	remaining_cash = max(0.0, _to_float(cash_balance, default=0.0))
	input_obligations = obligations if isinstance(obligations, list) else []
	updated_obligations = []

	for item in input_obligations:
		obligation = item.copy() if isinstance(item, dict) else {}

		amount = _to_float(obligation.get("amount"), default=0.0)
		amount_paid = _to_float(obligation.get("amount_paid"), default=0.0)
		net_amount = max(0.0, amount - amount_paid)

		if net_amount == 0.0:
			obligation["can_pay"] = True
			obligation["risk_level"] = "low"
			updated_obligations.append(obligation)
			continue

		if remaining_cash >= net_amount:
			obligation["can_pay"] = True
			obligation["risk_level"] = "low"
			remaining_cash -= net_amount
		else:
			obligation["can_pay"] = False
			flexibility = str(obligation.get("flexibility", "medium") or "medium").strip().lower()
			if flexibility == "low":
				obligation["risk_level"] = "high"
			elif flexibility == "high":
				obligation["risk_level"] = "low"
			else:
				obligation["risk_level"] = "medium"

		updated_obligations.append(obligation)

	return updated_obligations
