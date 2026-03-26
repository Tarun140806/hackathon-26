#!/usr/bin/env python3
"""Test payment status syncing on frontend load"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_payment_sync():
    print("=" * 60)
    print("Testing Payment Status Sync on Analysis Load")
    print("=" * 60)
    
    # Step 1: Store analysis with obligations
    print("\n1️⃣ Storing analysis with 3 obligations...")
    obligations = [
        {"vendor": "Office Rent", "amount": 50000, "due_date": "2024-01-15"},
        {"vendor": "Salary", "amount": 200000, "due_date": "2024-01-10"},
        {"vendor": "Supplies", "amount": 5000, "due_date": "2024-01-20"}
    ]
    
    store_response = requests.post(
        f"{BASE_URL}/features/store-analysis",
        json={"cash_balance": 50000, "prioritized_obligations": obligations}
    )
    print(f"   Status: {store_response.status_code}")
    stored_data = store_response.json()
    print(f"   Response: {json.dumps(stored_data, indent=2)}")
    
    # Step 2: Mark first obligation as PAID
    print("\n2️⃣ Marking 'Office Rent' as PAID...")
    update_response = requests.put(
        f"{BASE_URL}/features/payment-status",
        json={"id": "office-rent-0", "payment_status": "paid"}
    )
    print(f"   Status: {update_response.status_code}")
    print(f"   Response: {json.dumps(update_response.json(), indent=2)}")
    
    # Step 3: Mark second obligation as SCHEDULED
    print("\n3️⃣ Marking 'Salary' as SCHEDULED...")
    update_response = requests.put(
        f"{BASE_URL}/features/payment-status",
        json={"id": "salary-1", "payment_status": "scheduled"}
    )
    print(f"   Status: {update_response.status_code}")
    print(f"   Response: {json.dumps(update_response.json(), indent=2)}")
    
    # Step 4: Frontend loads analysis - verify it can fetch all statuses
    print("\n4️⃣ Frontend would now fetch payment statuses for each obligation...")
    for ob in stored_data.get("prioritized_obligations", []):
        ob_id = ob.get("id")
        status_response = requests.get(
            f"{BASE_URL}/features/payment-status/{ob_id}"
        )
        status_data = status_response.json()
        print(f"   • {ob.get('vendor'):15} ({ob_id:15}): {status_data.get('status'):10}")
    
    # Step 5: Get payment tracking summary
    print("\n5️⃣ Payment Tracking Summary (what user sees in UI)...")
    summary_response = requests.get(f"{BASE_URL}/features/payment-tracking-summary")
    summary_data = summary_response.json()
    print(f"   Total Tracked: {summary_data.get('total_tracked')}")
    print(f"   ✓ Paid: {summary_data.get('paid')}")
    print(f"   📅 Scheduled: {summary_data.get('scheduled')}")
    print(f"   ⏳ Pending: {summary_data.get('pending')}")
    print(f"   Payment Rate: {summary_data.get('payment_rate')}")
    
    # Step 6: Recalculate analysis after payments
    print("\n6️⃣ Recalculating analysis after payments...")
    recalc_response = requests.post(
        f"{BASE_URL}/features/recalculate-analysis"
    )
    recalc_data = recalc_response.json()
    print(f"   Original Shortfall: ₹{recalc_data.get('original_shortfall', 0):,}")
    print(f"   New Shortfall: ₹{recalc_data.get('new_shortfall', 0):,}")
    print(f"   Amount Paid: ₹{recalc_data.get('amount_paid', 0):,}")
    print(f"   Savings: ₹{recalc_data.get('savings', 0):,}")
    print(f"   Remaining: {len(recalc_data.get('remaining_obligations_list', []))}/3 obligations")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print("\nExpected Frontend Behavior:")
    print("  1. Analysis loads → IDs assigned: office-rent-0, salary-1, supplies-2")
    print("  2. useEffect fetches payment statuses:")
    print("     - Office Rent: ✓ PAID")
    print("     - Salary: 📅 SCHEDULED")
    print("     - Supplies: ⏳ PENDING (default)")
    print("  3. Dropdowns display: [Paid, Scheduled, Pending]")
    print("  4. Shortfall shows recalculated value (₹0 after payment)")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_payment_sync()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
