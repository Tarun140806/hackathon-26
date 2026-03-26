"""
LLM Service using Google Gemini API
"""

import os
import google.generativeai as genai


# ----------------------------
# CONFIG
# ----------------------------

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️  Warning: GEMINI_API_KEY not set. Will use mock responses.")


# ----------------------------
# FORMAT HELPERS
# ----------------------------

def format_obligation(obligation: dict) -> str:
    return f"""
- Vendor: {obligation.get('vendor', 'Unknown')}
  Amount: ₹{obligation.get('amount', 0):,.0f}
  Due Date: {obligation.get('due_date', 'N/A')}
  Category: {obligation.get('category', 'Unknown')}
  Penalty if late: ₹{obligation.get('penalty_if_late', 0):,.0f}
  Flexibility: {obligation.get('flexibility', 'Medium')}
  Risk Level: {obligation.get('risk_level', 'Low')}
"""


# ----------------------------
# PROMPT BUILDER
# ----------------------------

def build_llm_prompt(obligations, cash_balance, prioritized_obligations):

    total_obligations = sum(o.get('amount', 0) for o in obligations)
    shortfall = max(0, total_obligations - cash_balance)

    unpaid = "\n".join([format_obligation(o) for o in obligations])

    priority_list = "\n".join([
        f"{i+1}. {o.get('vendor')} - ₹{o.get('amount', 0):,.0f} (Score: {o.get('score', 0)})"
        for i, o in enumerate(prioritized_obligations[:5])
    ])

    return f"""
You are a senior financial strategist and CFO-level advisor.
Your job is to provide EXTREMELY DETAILED, SPECIFIC, and ANALYTICAL financial guidance.

ANALYZE DEEPLY - DO NOT GIVE GENERIC ANSWERS.

FINANCIAL DATA:
- Cash Balance: ₹{cash_balance}
- Total Obligations: ₹{total_obligations}
- Shortfall: ₹{shortfall}

ALL OBLIGATIONS:
{unpaid}

PRIORITY ORDER:
{priority_list}

REQUIREMENTS FOR YOUR RESPONSE:
✓ MENTION EXACT VENDOR NAMES AND AMOUNTS in every section
✓ COMPARE AT LEAST 3 OBLIGATIONS with specific trade-offs
✓ INCLUDE SPECIFIC PENALTY AMOUNTS and consequences
✓ EXPLAIN FLEXIBILITY DIFFERENCES between vendors
✓ PROVIDE SPECIFIC TIMELINES (e.g., "within 5 business days")
✓ CALCULATE SPECIFIC CASH IMPACTS
✓ AVOID ALL GENERIC STATEMENTS - be concrete and analytical
✓ SHOW YOUR REASONING STEP-BY-STEP
✓ INCLUDE BEST-CASE AND WORST-CASE SCENARIOS with numbers
✓ MENTION SPECIFIC RISKS AND HOW TO MITIGATE THEM

---

OUTPUT FORMAT (STRICTLY FOLLOW - EACH SECTION MUST BE DETAILED AND SPECIFIC):

[SECTION 1: Email Draft]
Write to the TOP-PRIORITY vendor:
- Use exact vendor name and amount
- Give specific, believable reason (cash flow mismatch, delayed receivables, etc.)
- Offer specific timeline (e.g., "5-7 business days")
- Sound professional and human
- Length: 150-250 words

---

[SECTION 2: Prioritization Reasoning]
EXTREMELY DETAILED comparison:
- Compare AT LEAST 3 vendors with specific metrics
- For each: mention name, amount, penalty amount, flexibility level, risk level
- Explain WHY vendor A is paid before vendor B (specific trade-offs)
- Calculate specific cash impacts
- Show penalty risk numbers
- Mention flexibility trade-offs
- Length: 300-400 words (MUST BE DETAILED)

---

[SECTION 3: Chain-Reaction Analysis]
Step-by-step financial consequences with specific numbers:
- Day 1: What happens when you pay the top vendor (show remaining cash)
- Days 2-5: Specific operational consequences
- Days 7-14: BEST-CASE vs WORST-CASE with numbers
- 30-day outlook with specific actions and amounts
- Include specific penalty amounts avoided/incurred
- Show cash flow recovery timeline
- Length: 400-500 words (MUST BE DETAILED AND ANALYTICAL)

---

IMPORTANT:
- NO GENERIC STATEMENTS ALLOWED
- BE EXTREMELY SPECIFIC WITH NUMBERS AND VENDOR NAMES
- SHOW ALL CALCULATIONS
- EACH SECTION MUST BE DETAILED (not short)
- ANALYZE TRADE-OFFS EXPLICITLY
"""



# ----------------------------
# PARSER
# ----------------------------

def parse_llm_response(text: str):
    parts = text.split("---")

    return {
        "email_draft": parts[0].replace("[SECTION 1: Email Draft]", "").strip() if len(parts) > 0 else "",
        "reasoning": parts[1].replace("[SECTION 2: Prioritization Reasoning]", "").strip() if len(parts) > 1 else "",
        "chain_reaction": parts[2].replace("[SECTION 3: Chain-Reaction Analysis]", "").strip() if len(parts) > 2 else "",
    }


# ----------------------------
# MOCK FALLBACK
# ----------------------------

def generate_mock_response(obligations, cash_balance, prioritized_obligations):
    vendor = prioritized_obligations[0].get('vendor', 'Partner') if prioritized_obligations else "Partner"
    amount = prioritized_obligations[0].get('amount', 0) if prioritized_obligations else 0
    
    # Build detailed reasoning with multiple vendors comparison
    top_vendors = prioritized_obligations[:3] if len(prioritized_obligations) >= 3 else prioritized_obligations
    vendor_comparison = ""
    for i, ob in enumerate(top_vendors, 1):
        penalty = ob.get('penalty_if_late', 0)
        flex = ob.get('flexibility', 'medium')
        risk = ob.get('risk_level', 'low')
        vendor_comparison += f"\n{i}. {ob.get('vendor', 'Unknown')}: ₹{ob.get('amount', 0):,.0f} - Penalty Risk: ₹{penalty:,.0f}, Flexibility: {flex}, Risk Level: {risk}"

    return {
        "email_draft": f"""Dear {vendor},

Thank you for your continued partnership and support. We are writing to inform you of a temporary cash flow constraint due to delayed receivables from our key clients.

We have an outstanding payment of ₹{amount:,.0f} to your account (Invoice/PO reference: pending). While this payment is a priority, we are currently facing a liquidity gap of 5-7 business days.

We respectfully request an extension of payment terms to {(int(amount/10000) if amount > 50000 else 5)} business days from today. We assure you that this is a temporary situation and normal payment cycles will resume thereafter.

Here's our proposed timeline:
- Days 1-3: Collect receivables from ABC Corp and XYZ Ltd
- Days 4-5: Process internal reconciliation
- Days 5-7: Full payment settlement to your account

We value this relationship and assure you of our commitment to honoring all obligations. Please confirm receipt and advise if you need any additional documentation.

Best regards,
Finance Team
CashClear Inc.""",

        "reasoning": f"""PRIORITIZATION ANALYSIS:

Vendor Comparison (Top 3):{vendor_comparison}

Prioritization Logic:
1. PENALTY RISK: {vendor.split()[0]} has a high late penalty (₹{prioritized_obligations[0].get('penalty_if_late', 0):,.0f}), making it critical to pay first. This represents {(prioritized_obligations[0].get('penalty_if_late', 0)/amount*100 if amount > 0 else 0):.1f}% of the invoice value.

2. FLEXIBILITY ANALYSIS: {prioritized_obligations[0].get('vendor')} has {prioritized_obligations[0].get('flexibility', 'medium')} flexibility. Lower flexibility vendors (strict payment terms) must be prioritized to avoid relationship damage and operational disruption.

3. CASH FLOW GAP: Current shortfall is ₹{max(0, sum(o.get('amount', 0) for o in obligations) - cash_balance):,.0f}. By delaying lower-risk, higher-flexibility vendors by 5-7 days, we preserve critical working capital.

4. TRADE-OFF DECISIONS:
   - DELAY: Lower-risk utilities (Internet, Electricity) - ₹{sum(o.get('amount', 0) for o in obligations if 'Bill' in o.get('vendor', '')):.0f} (can absorb 7-day delay with minimal consequences)
   - PRIORITIZE: {vendor} - ₹{amount:,.0f} (high penalty risk, business-critical)
   - MEDIUM: {prioritized_obligations[1].get('vendor', 'Partner') if len(prioritized_obligations) > 1 else 'N/A'} - Balance between urgency and cash preservation

5. RISK MATRIX: 
   - High Risk (pay immediately): {prioritized_obligations[0].get('vendor')} 
   - Medium Risk (pay in 3-5 days): {prioritized_obligations[1].get('vendor', 'N/A') if len(prioritized_obligations) > 1 else 'N/A'}
   - Low Risk (can delay 7+ days): {prioritized_obligations[2].get('vendor', 'N/A') if len(prioritized_obligations) > 2 else 'N/A'}""",

        "chain_reaction": f"""FINANCIAL DECISION CHAIN-REACTION ANALYSIS:

IMMEDIATE ACTIONS (Day 1):
✓ Pay {vendor}: ₹{amount:,.0f}
✓ Remaining Cash: ₹{max(0, cash_balance - amount):,.0f}
✓ Risk Avoided: ₹{prioritized_obligations[0].get('penalty_if_late', 0):,.0f} in penalties

SHORT-TERM IMPACT (Days 2-5):
- Creditor Relationship: PROTECTED - Priority vendor receives timely payment, building trust
- Operational Risk: REDUCED - Avoid service disruption from high-priority vendor
- Cash Position: TIGHT - ₹{max(0, cash_balance - amount):,.0f} remaining for {len([o for o in obligations if o.get('vendor') != vendor]):.0f} other obligations
- Penalty Exposure: REDUCED - Avoided ₹{prioritized_obligations[0].get('penalty_if_late', 0):,.0f} late fee

MEDIUM-TERM OUTLOOK (Days 7-14):
BEST CASE:
- Receivables collected from clients: +₹{int(max(0, sum(o.get('amount', 0) for o in obligations) - cash_balance) * 1.2):,.0f}
- Process next batch of priority payments
- Return to normal payment cycle
- Monthly working capital restored

WORST CASE:
- Delayed receivables (10-14 days)
- Must negotiate with 2-3 vendors for extension
- Total delay penalty risk: ₹{sum(o.get('penalty_if_late', 0) for o in prioritized_obligations[1:3] if len(prioritized_obligations) > 1):,.0f}
- May require emergency credit line

30-DAY STRATEGIC OUTLOOK:
1. Current Month: Pay high-priority vendors (₹{amount:,.0f}), negotiate extensions for low-risk items
2. Week 2-3: Collect receivables and replenish cash (target: +₹{int(max(0, sum(o.get('amount', 0) for o in obligations) - cash_balance) * 1.5):,.0f})
3. Week 4+: Resume normal payment terms, rebuild creditor relationships
4. Monthly Impact: Avoid ₹{sum(o.get('penalty_if_late', 0) for o in prioritized_obligations[:2]):,.0f} in cumulative penalties

CRITICAL SUCCESS FACTORS:
✓ Communicate transparently with {vendor}
✓ Collect receivables within 5-7 days
✓ Avoid defaulting on top 3 vendors
✓ Preserve ₹{max(0, cash_balance * 0.15):,.0f} emergency buffer (15% of current cash)"""
    }


# ----------------------------
# MAIN FUNCTION
# ----------------------------

def generate_llm_output(obligations, cash_balance, prioritized_obligations):
    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("⚠️  No Gemini API key found, using mock responses")
            return generate_mock_response(obligations, cash_balance, prioritized_obligations)

        print("✓ Using Gemini API for LLM generation")
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = build_llm_prompt(obligations, cash_balance, prioritized_obligations)

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=2048,
                top_p=0.95,
            )
        )

        result = parse_llm_response(response.text)
        print("✓ Gemini API response received successfully")
        return result

    except Exception as e:
        print(f"❌ Gemini API Error: {type(e).__name__}: {e}")
        print("📋 Falling back to mock responses")
        return generate_mock_response(obligations, cash_balance, prioritized_obligations)


# ----------------------------
# TEST
# ----------------------------

if __name__ == "__main__":
    test_data = [
        {
            "vendor": "Electricity Board",
            "amount": 8000,
            "due_date": "2026-03-27",
            "penalty_if_late": 1000,
            "category": "utility",
            "flexibility": "low",
            "risk_level": "high"
        }
    ]

    result = generate_llm_output(test_data, 10000, test_data)

    print("\nEMAIL:\n", result["email_draft"])
    print("\nREASONING:\n", result["reasoning"])
    print("\nCHAIN:\n", result["chain_reaction"])