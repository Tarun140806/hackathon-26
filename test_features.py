#!/usr/bin/env python
"""Test script for new features (PDF Export, Payment Tracking, etc.)"""

import requests
import json
import base64
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_pdf_export():
    """Test PDF export feature"""
    print("\n✓ Testing PDF Export...")
    
    test_data = {
        "cash_balance": 100000,
        "total_obligations": 150000,
        "shortfall": 50000,
        "prioritized_obligations": [
            {
                "vendor": "Rent - Office Space",
                "amount": 50000,
                "score": 95,
                "risk_level": "high",
                "can_pay": False
            },
            {
                "vendor": "Vendor B - Supplies",
                "amount": 75000,
                "score": 85,
                "risk_level": "medium",
                "can_pay": False
            },
            {
                "vendor": "Employee Salary",
                "amount": 25000,
                "score": 99,
                "risk_level": "critical",
                "can_pay": False
            }
        ],
        "reasoning": "Critical analysis: With a shortfall of ₹50,000, prioritize employee salaries (critical), then rent (high risk), then supplies (lower impact).",
        "email_draft": "Dear Vendor,\n\nWe are temporarily facing a cash flow shortage. We request a payment extension by 15 days...",
        "chain_reaction": "Day 1: Pay salaries (₹25k) -> remaining ₹75k\nDay 5: Pay rent (₹50k) -> remaining ₹25k\nDay 10: Supplies can wait, negotiate extension"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/features/export-pdf",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "pdf_base64" in result:
                print(f"  ✓ PDF generated: {result['filename']}")
                print(f"  ✓ PDF size: {len(result['pdf_base64']) / 1024:.1f} KB")
                
                # Save PDF to file
                pdf_bytes = base64.b64decode(result['pdf_base64'])
                filename = result.get('filename', 'output.pdf')
                with open(filename, 'wb') as f:
                    f.write(pdf_bytes)
                print(f"  ✓ PDF saved to: {filename}")
                return True
            else:
                print(f"  ✗ Unexpected response: {result}")
                return False
        else:
            print(f"  ✗ API returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def test_payment_tracking():
    """Test payment status tracking"""
    print("\n✓ Testing Payment Status Tracking...")
    
    try:
        # Update payment status
        update_data = {
            "id": "ob-123",
            "payment_status": "paid",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Paid via bank transfer"
        }
        
        response = requests.put(
            f"{BASE_URL}/features/payment-status",
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✓ Payment status updated")
            
            # Get payment status
            response = requests.get(
                f"{BASE_URL}/features/payment-status/ob-123",
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                print(f"  ✓ Payment status retrieved: {status['status']}")
                
                # Get summary
                response = requests.get(
                    f"{BASE_URL}/features/payment-tracking-summary",
                    timeout=10
                )
                
                if response.status_code == 200:
                    summary = response.json()
                    print(f"  ✓ Payment summary: {summary['paid']} paid, {summary['pending']} pending")
                    return True
        
        print(f"  ✗ Request failed with status {response.status_code}")
        return False
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def test_recurring_obligations():
    """Test recurring obligations"""
    print("\n✓ Testing Recurring Obligations...")
    
    try:
        # Add recurring obligation
        recurring_data = {
            "id": "recurring-1",
            "vendor": "Monthly Rent",
            "amount": 50000,
            "frequency": "monthly",
            "next_occurrence": "2026-04-01",
            "penalty_if_late": 5000,
            "category": "critical",
            "flexibility": "low"
        }
        
        response = requests.post(
            f"{BASE_URL}/features/recurring-obligation",
            json=recurring_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✓ Recurring obligation added")
            
            # List recurring
            response = requests.get(
                f"{BASE_URL}/features/recurring-obligations",
                timeout=10
            )
            
            if response.status_code == 200:
                obligations = response.json()
                print(f"  ✓ Listed {len(obligations)} recurring obligations")
                return True
        
        print(f"  ✗ Request failed with status {response.status_code}")
        return False
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def run_tests():
    """Run all feature tests"""
    print("=" * 50)
    print("CASHCLEAR FEATURE TESTS")
    print("=" * 50)
    
    results = []
    
    # Test each feature
    results.append(("PDF Export", test_pdf_export()))
    results.append(("Payment Tracking", test_payment_tracking()))
    results.append(("Recurring Obligations", test_recurring_obligations()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
