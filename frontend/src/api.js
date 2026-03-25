const BASE_URL = "http://localhost:8000"

async function parseResponse(response) {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json()
}

export async function uploadBankStatement(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BASE_URL}/upload/bank-statement`, {
      method: 'POST',
      body: formData,
    })

    return await parseResponse(response)
  } catch (error) {
    throw error
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

export { BASE_URL }