from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


CategoryType = Literal["critical", "high", "medium", "low"]
FlexibilityType = Literal["low", "medium", "high"]
RelationshipType = Literal["close", "neutral", "new"]
FrequencyType = Literal["one-time", "weekly", "monthly"]
RiskLevelType = Literal["high", "medium", "low"]
StatusType = Literal["overdue", "due-today", "upcoming"]
PaymentStatusType = Literal["pending", "scheduled", "paid", "overdue"]
TransactionType = Literal[
	"immediate_credit",
	"immediate_debit",
	"due_credit",
	"due_debit",
]


CRITICAL_KEYWORDS = ("gst", "tds", "tax", "emi", "loan", "electricity", "utility")
HIGH_KEYWORDS = ("rent", "salary", "wages", "payroll")


class EngineBaseModel(BaseModel):
	class Config:
		arbitrary_types_allowed = True


class Obligation(EngineBaseModel):
	id: Optional[str] = None
	vendor: Optional[str] = None
	description: Optional[str] = None
	category: Optional[CategoryType] = None

	amount: float = 0.0
	amount_paid: float = 0.0
	due_date: Optional[str] = None
	penalty_if_late: float = 0.0

	flexibility: Optional[FlexibilityType] = None
	relationship: Optional[RelationshipType] = None
	recurring: bool = False
	frequency: Optional[FrequencyType] = None
	currency: str = "INR"

	can_pay: Optional[bool] = None
	risk_level: Optional[RiskLevelType] = None
	score: Optional[int] = None
	payment_status: PaymentStatusType = "pending"
	payment_date: Optional[str] = None
	notes: Optional[str] = None
	status: Optional[StatusType] = None
	email_draft: Optional[str] = None

	@model_validator(mode="after")
	def auto_classify_category(self) -> "Obligation":
		description_text = (self.description or "").lower()
		if any(keyword in description_text for keyword in CRITICAL_KEYWORDS):
			self.category = "critical"
		elif any(keyword in description_text for keyword in HIGH_KEYWORDS):
			self.category = "high"
		elif self.category is None:
			self.category = "low"
		return self


class Transaction(EngineBaseModel):
	type: TransactionType
	amount: float = 0.0
	date: str
	vendor: Optional[str] = None
	penalty_if_late: float = 0.0
	flexibility: Optional[FlexibilityType] = None


class AnalyzeRequest(EngineBaseModel):
	cash_balance: float
	obligations: List[Obligation] = Field(default_factory=list)
	transactions: List[Transaction] = Field(default_factory=list)


class SimulationDay(EngineBaseModel):
	date: str
	projected_balance: float


class ObligationResult(Obligation):
	score: int = 0
	status: StatusType = "upcoming"
	can_pay: bool = False
	risk_level: RiskLevelType = "low"
	category: CategoryType = "low"
	email_draft: Optional[str] = None


class DecisionSummary(EngineBaseModel):
	total_can_pay: int
	total_deferred: int
	all_covered: bool


class AnalyzeResponse(EngineBaseModel):
	cash_balance: float
	total_obligations: float
	shortfall: float
	days_to_zero: Optional[int] = None
	prioritized_obligations: List[ObligationResult] = Field(default_factory=list)
	simulation: List[SimulationDay] = Field(default_factory=list)
	reasoning: str
	summary: DecisionSummary
	email_draft: Optional[str] = None
	chain_reaction: Optional[str] = None


class PaymentStatusUpdate(EngineBaseModel):
	id: str
	payment_status: PaymentStatusType
	payment_date: Optional[str] = None
	notes: Optional[str] = None


class RecurringObligation(EngineBaseModel):
	id: str
	vendor: str
	amount: float
	frequency: FrequencyType
	next_occurrence: str
	penalty_if_late: float = 0.0
	category: Optional[CategoryType] = None
	flexibility: Optional[FlexibilityType] = None


class WhatIfScenario(EngineBaseModel):
	scenario_name: str
	cash_balance_adjustment: float
	description: Optional[str] = None


class PDFExportRequest(EngineBaseModel):
	cash_balance: float
	total_obligations: float
	shortfall: float
	reasoning: str
	email_draft: Optional[str] = None
	chain_reaction: Optional[str] = None
	prioritized_obligations: List[Obligation] = Field(default_factory=list)
