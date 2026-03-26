const BASE_URL = "http://localhost:8000"

async function parseResponse(response) {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json()
}

export async function uploadBankStatement(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      "http://127.0.0.1:8000/upload/bank-statement",
      {
        method: "POST",
        body: formData,
      }
    );

    if (!response.ok) {
      throw new Error("Upload failed");
    }

    return await response.json();
  } catch (error) {
    console.error("UPLOAD ERROR:", error);
    throw error;
  }
}

export async function uploadInvoice(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BASE_URL}/upload/invoice`, {
      method: 'POST',
      body: formData,
    })

    return await parseResponse(response)
  } catch (error) {
    throw error
  }
}

export async function analyzeObligations(cashBalance, obligations) {
  try {
    const response = await fetch(`${BASE_URL}/decision/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        cash_balance: cashBalance,
        obligations,
      }),
    })

    return await parseResponse(response)
  } catch (error) {
    throw error
  }
}

export async function exportPDF(analysisData) {
  try {
    const response = await fetch(`${BASE_URL}/features/export-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(analysisData),
    })

    if (!response.ok) {
      throw new Error('PDF export failed')
    }

    return await response.json()
  } catch (error) {
    console.error('PDF export error:', error)
    throw error
  }
}

export async function updatePaymentStatus(obligationId, status, paymentDate, notes) {
  try {
    const response = await fetch(`${BASE_URL}/features/payment-status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: obligationId,
        payment_status: status,
        payment_date: paymentDate,
        notes: notes,
      }),
    })

    return await parseResponse(response)
  } catch (error) {
    console.error('Payment status update error:', error)
    throw error
  }
}

export async function storeAnalysis(analysisData) {
  try {
    const response = await fetch(`${BASE_URL}/features/store-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(analysisData),
    })

    return await parseResponse(response)
  } catch (error) {
    console.error('Store analysis error:', error)
    throw error
  }
}

export async function recalculateAnalysis() {
  try {
    const response = await fetch(`${BASE_URL}/features/recalculate-analysis`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return await parseResponse(response)
  } catch (error) {
    console.error('Recalculate analysis error:', error)
    throw error
  }
}

export async function getPaymentTrackingSummary() {
  try {
    const response = await fetch(`${BASE_URL}/features/payment-tracking-summary`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return await parseResponse(response)
  } catch (error) {
    console.error('Payment tracking summary error:', error)
    throw error
  }
}

export { BASE_URL }