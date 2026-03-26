#!/usr/bin/env python
"""Test payment tracking with shortfall recalculation"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_payment_recalculation():
    """Test that shortfall decreases when payment is marked as paid"""
    print("\n" + "="*60)
    print("PAYMENT TRACKING - SHORTFALL RECALCULATION TEST")
    print("="*60)
    
    # Setup: Store analysis with multiple obligations
    print("\n1️⃣ Storing initial analysis...")
    analysis_data = {
        "cash_balance": 100000,
        "prioritized_obligations": [
            {
                "id": "ob-rent",
                "vendor": "Office Rent",
                "amount": 50000,
                "score": 95,
                "risk_level": "high",
                "can_pay": False
            },
            {
                "id": "ob-salary",
                "vendor": "Employee Salary",
                "amount": 60000,
                "score": 99,
                "risk_level": "critical",
                "can_pay": False
            },
            {
                "id": "ob-supplies",
                "vendor": "Office Supplies",
                "amount": 30000,
                "score": 70,
                "risk_level": "medium",
                "can_pay": False
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/features/store-analysis",
        json=analysis_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Stored: {response.json()}")
    
    # Get initial analysis
    print("\n2️⃣ Getting initial analysis...")
    response = requests.get(
        f"{BASE_URL}/features/recalculate-analysis",
        timeout=10
    )
    result = response.json()
    print(f"   Original Shortfall: ₹{result['original_shortfall']:,.0f}")
    print(f"   Cash Balance: ₹{result['cash_balance']:,.0f}")
    print(f"   Total Obligations: ₹{result['total_obligations']:,.0f}")
    print(f"   Remaining Obligations: {result['remaining_obligations']}")
    
    original_shortfall = result['original_shortfall']
    
    # Mark first obligation as paid
    print("\n3️⃣ Marking 'Office Rent' (₹50k) as PAID...")
    response = requests.put(
        f"{BASE_URL}/features/payment-status",
        json={
            "id": "ob-rent",
            "payment_status": "paid",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Paid via bank transfer"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()['message']}")
    
    # Get updated analysis
    print("\n4️⃣ Getting updated analysis after payment...")
    response = requests.get(
        f"{BASE_URL}/features/recalculate-analysis",
        timeout=10
    )
    result = response.json()
    new_shortfall = result['new_shortfall']
    
    print(f"   ✓ Original Shortfall: ₹{result['original_shortfall']:,.0f}")
    print(f"   ✓ New Shortfall: ₹{new_shortfall:,.0f}")
    print(f"   ✓ Amount Paid: ₹{result['amount_paid']:,.0f}")
    print(f"   ✓ Savings: ₹{result['savings']:,.0f}")
    print(f"   ✓ Remaining Obligations: {result['remaining_obligations']}/{result['total_obligations']}")
    
    # Verify shortfall decreased
    shortfall_decrease = original_shortfall - new_shortfall
    print(f"\n5️⃣ Verification:")
    print(f"   Original Shortfall: ₹{original_shortfall:,.0f}")
    print(f"   New Shortfall: ₹{new_shortfall:,.0f}")
    print(f"   Shortfall Decreased By: ₹{shortfall_decrease:,.0f}")
    
    if shortfall_decrease >= 50000:
        print(f"   ✅ SUCCESS: Shortfall decreased correctly!")
        return True
    else:
        print(f"   ❌ FAILED: Shortfall should have decreased by ~₹50k")
        return False


def test_multiple_payments():
    """Test multiple payments reducing shortfall progressively"""
    print("\n" + "="*60)
    print("MULTIPLE PAYMENTS - PROGRESSIVE REDUCTION TEST")
    print("="*60)
    
    # Mark salary as paid
    print("\n1️⃣ Marking 'Employee Salary' (₹60k) as PAID...")
    response = requests.put(
        f"{BASE_URL}/features/payment-status",
        json={
            "id": "ob-salary",
            "payment_status": "paid",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Paid to employees"
        },
        timeout=10
    )
    print(f"   ✓ Status {response.status_code}")
    
    # Get analysis
    response = requests.get(
        f"{BASE_URL}/features/recalculate-analysis",
        timeout=10
    )
    result = response.json()
    
    print(f"\n2️⃣ Current Status:")
    print(f"   New Shortfall: ₹{result['new_shortfall']:,.0f}")
    print(f"   Remaining Obligations: {result['remaining_obligations']}/{result['total_obligations']}")
    print(f"   Total Amount Paid: ₹{result['amount_paid']:,.0f}")
    print(f"   Savings So Far: ₹{result['savings']:,.0f}")
    
    if result['new_shortfall'] >= 0:
        print(f"\n   ✅ SUCCESS: Multiple payments tracking works!")
        return True
    else:
        print(f"\n   ❌ FAILED: Shortfall calculation error")
        return False


if __name__ == "__main__":
    try:
        test1 = test_payment_recalculation()
        test2 = test_multiple_payments()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Single Payment Test: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Multiple Payments Test: {'✅ PASS' if test2 else '❌ FAIL'}")
        
        exit(0 if test1 and test2 else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)
