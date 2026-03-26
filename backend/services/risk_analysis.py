def _to_float(value, default=0.0) -> float:
	try:
		if value is None:
			return float(default)
		return float(value)
	except (TypeError, ValueError):
		return float(default)


RISK_PRIORITY = {"low": 1, "medium": 2, "high": 3}


def _normalize_risk(value) -> str | None:
	if value is None:
		return None
	text = str(value).strip().lower()
	return text if text in RISK_PRIORITY else None


def _max_risk_level(*levels: str | None) -> str:
	valid_levels = [level for level in levels if level in RISK_PRIORITY]
	if not valid_levels:
		return "low"
	return max(valid_levels, key=lambda level: RISK_PRIORITY[level])


def apply_risk_analysis(cash_balance: float, obligations: list[dict]) -> list[dict]:
	remaining_cash = max(0.0, _to_float(cash_balance, default=0.0))
	input_obligations = obligations if isinstance(obligations, list) else []
	updated_obligations = []

	for item in input_obligations:
		obligation = item.copy() if isinstance(item, dict) else {}
		provided_risk = _normalize_risk(obligation.get("risk_level"))

		amount_due = obligation.get("amount_due")
		if amount_due is not None:
			net_amount = max(0.0, _to_float(amount_due, default=0.0))
		else:
			amount = _to_float(obligation.get("amount"), default=0.0)
			amount_paid = _to_float(obligation.get("amount_paid"), default=0.0)
			net_amount = max(0.0, amount - amount_paid)

		if net_amount == 0.0:
			obligation["can_pay"] = True
			obligation["risk_level"] = _max_risk_level("low", provided_risk)
			updated_obligations.append(obligation)
			continue

		if remaining_cash >= net_amount:
			obligation["can_pay"] = True
			computed_risk = "low"
			remaining_cash -= net_amount
		else:
			obligation["can_pay"] = False
			flexibility = str(obligation.get("flexibility", "medium") or "medium").strip().lower()
			if flexibility == "low":
				computed_risk = "high"
			elif flexibility == "high":
				computed_risk = "low"
			else:
				computed_risk = "medium"

		obligation["risk_level"] = _max_risk_level(computed_risk, provided_risk)

		updated_obligations.append(obligation)

	return updated_obligations
