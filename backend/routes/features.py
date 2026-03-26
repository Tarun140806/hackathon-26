from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from backend.models.schema import (
    PaymentStatusUpdate,
    RecurringObligation,
    WhatIfScenario,
    AnalyzeRequest,
    Obligation,
)
from backend.services.decision_engine import run_decision_engine
from backend.services.llm_service import generate_llm_output

router = APIRouter(prefix="/features", tags=["features"])

# In-memory storage for demo (replace with database in production)
payment_tracking = {}
recurring_obligations = {}
current_obligations = []  # Track current obligations for recalculation
current_cash_balance = 0  # Track current cash balance


# ===== PAYMENT STATUS TRACKING =====
@router.put("/payment-status")
def update_payment_status(update: PaymentStatusUpdate) -> dict:
    """Update payment status for an obligation - recalculates shortfall"""
    global current_obligations, current_cash_balance
    
    payment_tracking[update.id] = {
        "status": update.payment_status,
        "payment_date": update.payment_date,
        "notes": update.notes,
        "updated_at": datetime.now().isoformat(),
    }
    
    # Find and update the obligation in current_obligations
    for ob in current_obligations:
        if ob.get("id") == update.id:
            ob["payment_status"] = update.payment_status
            ob["payment_date"] = update.payment_date
            ob["notes"] = update.notes
            break
    
    # Calculate impact of payment
    amount_paid = 0
    for ob in current_obligations:
        if ob.get("id") == update.id:
            amount_paid = ob.get("amount", 0)
            break
    
    # If marked as paid, adjust cash balance
    if update.payment_status == "paid":
        current_cash_balance += amount_paid  # Assume we're recording a payment that happened
    
    return {
        "success": True,
        "message": f"Payment status updated to {update.payment_status}",
        "cash_balance_adjusted": update.payment_status == "paid",
        "amount_adjusted": amount_paid if update.payment_status == "paid" else 0
    }


@router.get("/payment-status/{obligation_id}")
def get_payment_status(obligation_id: str) -> dict:
    """Get payment status for an obligation"""
    if obligation_id not in payment_tracking:
        return {"status": "pending", "payment_date": None, "notes": None}
    return payment_tracking[obligation_id]


@router.get("/payment-tracking-summary")
def get_payment_tracking_summary() -> dict:
    """Get summary of all payments tracked"""
    total = len(payment_tracking)
    paid = sum(1 for p in payment_tracking.values() if p["status"] == "paid")
    scheduled = sum(1 for p in payment_tracking.values() if p["status"] == "scheduled")
    pending = sum(1 for p in payment_tracking.values() if p["status"] == "pending")
    overdue = sum(1 for p in payment_tracking.values() if p["status"] == "overdue")

    return {
        "total_tracked": total,
        "paid": paid,
        "scheduled": scheduled,
        "pending": pending,
        "overdue": overdue,
        "payment_rate": f"{(paid / total * 100):.1f}%" if total > 0 else "0%",
    }


@router.post("/store-analysis")
def store_analysis(data: dict) -> dict:
    """Store current analysis state for recalculation"""
    global current_obligations, current_cash_balance
    
    current_cash_balance = data.get("cash_balance", 0)
    obligations = data.get("prioritized_obligations", [])
    
    # Ensure each obligation has an ID (generate if missing)
    for i, ob in enumerate(obligations):
        if not ob.get("id"):
            # Generate ID from vendor name + index
            vendor = ob.get("vendor", f"obligation-{i}").replace(" ", "-").lower()
            ob["id"] = f"{vendor}-{i}"
    
    current_obligations = obligations
    
    return {
        "success": True,
        "message": "Analysis state stored",
        "cash_balance": current_cash_balance,
        "obligations_count": len(current_obligations),
        "generated_ids": [ob.get("id") for ob in current_obligations]
    }


@router.get("/recalculate-analysis")
def recalculate_analysis() -> dict:
    """Get recalculated analysis after payment updates"""
    global current_obligations, current_cash_balance
    
    if not current_obligations:
        return {
            "original_shortfall": 0,
            "new_shortfall": 0,
            "cash_balance": current_cash_balance,
            "amount_paid": 0,
            "total_obligations": 0,
            "remaining_obligations": 0,
            "remaining_obligations_list": [],
            "payment_stats": {"total_tracked": 0, "paid": 0, "still_pending": 0},
            "savings": 0
        }
    
    # Calculate original totals
    original_total = sum(ob.get("amount", 0) for ob in current_obligations)
    original_shortfall = max(0, original_total - current_cash_balance)
    
    # Filter out paid obligations
    remaining_obligations = [
        ob for ob in current_obligations 
        if payment_tracking.get(ob.get("id"), {}).get("status") != "paid"
    ]
    
    # Recalculate shortfall with remaining obligations
    total_remaining = sum(ob.get("amount", 0) for ob in remaining_obligations)
    new_shortfall = max(0, total_remaining - current_cash_balance)
    
    # Calculate total paid
    paid_amount = original_total - total_remaining
    
    # Calculate savings
    savings = original_shortfall - new_shortfall
    
    # Get payment counts
    total_tracked = len(current_obligations)
    paid_count = sum(1 for p in payment_tracking.values() if p.get("status") == "paid")
    
    return {
        "original_shortfall": original_shortfall,
        "new_shortfall": new_shortfall,
        "cash_balance": current_cash_balance,
        "amount_paid": paid_amount,
        "total_obligations": total_tracked,
        "remaining_obligations": len(remaining_obligations),
        "remaining_obligations_list": remaining_obligations,
        "payment_stats": {
            "total_tracked": total_tracked,
            "paid": paid_count,
            "still_pending": len(remaining_obligations),
        },
        "savings": savings
    }


# ===== RECURRING OBLIGATIONS =====
@router.post("/recurring-obligation")
def add_recurring_obligation(recurring: RecurringObligation) -> dict:
    """Add a recurring obligation"""
    recurring_obligations[recurring.id] = recurring.model_dump()
    return {"success": True, "message": "Recurring obligation added", "id": recurring.id}


@router.get("/recurring-obligations")
def list_recurring_obligations() -> list:
    """List all recurring obligations"""
    return list(recurring_obligations.values())


@router.post("/generate-recurring")
def generate_recurring_obligations(month: str = None) -> dict:
    """Generate recurring obligations for a month"""
    if not month:
        month = datetime.now().strftime("%Y-%m")

    generated = []
    for recurring in recurring_obligations.values():
        next_date = datetime.fromisoformat(recurring["next_occurrence"])
        if next_date.strftime("%Y-%m") == month:
            generated.append(
                Obligation(
                    id=f"rec-{recurring['id']}-{month}",
                    vendor=recurring["vendor"],
                    amount=recurring["amount"],
                    due_date=next_date.strftime("%Y-%m-%d"),
                    penalty_if_late=recurring["penalty_if_late"],
                    category=recurring.get("category"),
                    flexibility=recurring.get("flexibility"),
                    recurring=True,
                    frequency=recurring["frequency"],
                )
            )

    return {"generated_count": len(generated), "obligations": [o.model_dump() for o in generated]}


# ===== WHAT-IF SCENARIOS =====
@router.post("/what-if-analyze")
def what_if_analyze(scenario: WhatIfScenario, request: AnalyzeRequest) -> dict:
    """Analyze impact of what-if scenario"""
    # Adjust cash balance
    adjusted_cash = request.cash_balance + scenario.cash_balance_adjustment
    adjusted_request = AnalyzeRequest(
        cash_balance=adjusted_cash,
        obligations=request.obligations,
        transactions=request.transactions,
    )

    # Run analysis with adjusted cash
    result = run_decision_engine(
        cash_balance=adjusted_cash,
        obligations=[o.model_dump() for o in request.obligations],
        transactions=[t.model_dump() for t in request.transactions],
    )

    # Generate LLM outputs
    llm_output = generate_llm_output(
        obligations=[o.model_dump() for o in request.obligations],
        cash_balance=adjusted_cash,
        prioritized_obligations=result.get("prioritized_obligations", []),
    )

    return {
        "scenario_name": scenario.scenario_name,
        "original_cash_balance": request.cash_balance,
        "adjusted_cash_balance": adjusted_cash,
        "adjustment": scenario.cash_balance_adjustment,
        "original_shortfall": max(
            0,
            sum(o.amount for o in request.obligations) - request.cash_balance,
        ),
        "adjusted_shortfall": result.get("shortfall", 0),
        "analysis": result,
        "llm_output": llm_output,
    }


@router.post("/compare-scenarios")
def compare_scenarios(scenarios: list[WhatIfScenario], request: AnalyzeRequest) -> dict:
    """Compare multiple what-if scenarios"""
    comparisons = []
    for scenario in scenarios:
        result = what_if_analyze(scenario, request)
        comparisons.append(result)

    return {
        "total_scenarios": len(scenarios),
        "comparisons": comparisons,
        "best_scenario": min(
            comparisons, key=lambda x: x["adjusted_shortfall"]
        )["scenario_name"],
    }


# ===== PDF EXPORT =====
@router.post("/export-pdf")
def export_pdf(data: dict) -> dict:
    """Generate PDF export of analysis"""
    try:
        from io import BytesIO
        from datetime import datetime
        import base64
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
            PageBreak,
            KeepTogether,
        )

        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1e40af"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#1e40af"),
            spaceAfter=12,
            spaceBefore=12,
        )
        normal_style = styles["BodyText"]
        normal_style.fontSize = 10
        normal_style.leading = 14

        # Document content
        story = []

        # Title
        story.append(
            Paragraph("CashClear Financial Analysis Report", title_style)
        )
        story.append(
            Paragraph(
                f"<i>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</i>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Summary section
        story.append(Paragraph("Financial Summary", heading_style))
        summary_data = [
            ["Metric", "Amount"],
            ["Cash Balance", f"₹{data.get('cash_balance', 0):,.0f}"],
            ["Total Obligations", f"₹{data.get('total_obligations', 0):,.0f}"],
            ["Shortfall", f"₹{data.get('shortfall', 0):,.0f}"],
        ]
        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Prioritized obligations section
        story.append(Paragraph("Prioritized Obligations", heading_style))
        obligations = data.get("prioritized_obligations", [])
        if obligations:
            ob_data = [["Rank", "Vendor", "Amount", "Score", "Risk", "Pay?"]]
            for i, ob in enumerate(obligations, 1):
                ob_data.append(
                    [
                        str(i),
                        ob.get("vendor", "-"),
                        f"₹{ob.get('amount', 0):,.0f}",
                        str(ob.get("score", "-")),
                        ob.get("risk_level", "-").upper(),
                        "Yes" if ob.get("can_pay") else "No",
                    ]
                )
            ob_table = Table(ob_data, colWidths=[0.6*inch, 1.5*inch, 1.2*inch, 0.6*inch, 0.6*inch, 0.5*inch])
            ob_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
                    ]
                )
            )
            story.append(ob_table)
            story.append(Spacer(1, 0.3 * inch))
        else:
            story.append(Paragraph("No obligations data available", normal_style))
            story.append(Spacer(1, 0.3 * inch))

        # Reasoning
        story.append(Paragraph("Financial Analysis & Reasoning", heading_style))
        reasoning = data.get("reasoning", "No reasoning available")
        story.append(Paragraph(reasoning, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # Email Draft
        if data.get("email_draft"):
            story.append(PageBreak())
            story.append(Paragraph("Recommended Payment Communication", heading_style))
            story.append(Paragraph(data.get("email_draft"), normal_style))
            story.append(Spacer(1, 0.2 * inch))

        # Chain Reaction Analysis
        if data.get("chain_reaction"):
            story.append(PageBreak())
            story.append(Paragraph("Chain-Reaction Impact Analysis", heading_style))
            story.append(Paragraph(data.get("chain_reaction"), normal_style))

        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)

        # Convert to base64 for transmission
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

        return {
            "success": True,
            "message": "PDF generated successfully",
            "pdf_base64": pdf_base64,
            "filename": f"cashclear_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "contentType": "application/pdf",
        }

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="reportlab library not installed. Run: pip install reportlab",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
