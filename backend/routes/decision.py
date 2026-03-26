from fastapi import APIRouter

from backend.models.schema import AnalyzeRequest
from backend.services.decision_engine import run_decision_engine
from backend.services.mongo_service import save_analysis_event


router = APIRouter()


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
	obligations = [item.model_dump() for item in request.obligations]
	transactions = [item.model_dump() for item in request.transactions]
	result = run_decision_engine(
		cash_balance=request.cash_balance,
		obligations=obligations,
		transactions=transactions,
	)
	analysis_id = save_analysis_event(request.cash_balance, obligations, result)
	if analysis_id:
		result["analysis_id"] = analysis_id
	return result
