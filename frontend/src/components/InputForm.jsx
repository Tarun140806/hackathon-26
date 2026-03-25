import { useState } from 'react'

function InputForm({ onCashBalance, onAddObligation, onAnalyze }) {
	const [cashBalance, setCashBalance] = useState('')
	const [vendor, setVendor] = useState('')
	const [amount, setAmount] = useState('')
	const [dueDate, setDueDate] = useState('')
	const [penaltyIfLate, setPenaltyIfLate] = useState('')
	const [flexibility, setFlexibility] = useState('medium')

	const handleCashBalanceChange = (event) => {
		const value = event.target.value
		setCashBalance(value)
		onCashBalance(Number(value || 0))
	}

	const handleAddObligation = (event) => {
		event.preventDefault()

		if (!vendor || !amount || !dueDate) {
			return
		}

		onAddObligation({
			id: `ob-${Date.now()}`,
			vendor,
			amount: Number(amount),
			due_date: dueDate,
			penalty_if_late: Number(penaltyIfLate || 0),
			flexibility,
		})

		setVendor('')
		setAmount('')
		setDueDate('')
		setPenaltyIfLate('')
		setFlexibility('medium')
	}

	return (
		<section className="rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
			<h2 className="mb-4 text-xl font-semibold text-white">Input Financial Data</h2>

			<div className="mb-5">
				<label className="text-sm text-slate-200">
					Cash Balance
					<input
						type="number"
						value={cashBalance}
						onChange={handleCashBalanceChange}
						className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
						placeholder="230000"
					/>
				</label>
			</div>

			<form onSubmit={handleAddObligation} className="grid gap-3 sm:grid-cols-2">
				<input
					value={vendor}
					onChange={(event) => setVendor(event.target.value)}
					className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
					placeholder="Vendor"
					required
				/>
				<input
					type="number"
					value={amount}
					onChange={(event) => setAmount(event.target.value)}
					className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
					placeholder="Amount"
					required
				/>
				<input
					type="date"
					value={dueDate}
					onChange={(event) => setDueDate(event.target.value)}
					className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
					required
				/>
				<input
					type="number"
					value={penaltyIfLate}
					onChange={(event) => setPenaltyIfLate(event.target.value)}
					className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
					placeholder="Penalty if late"
				/>
				<select
					value={flexibility}
					onChange={(event) => setFlexibility(event.target.value)}
					className="sm:col-span-2 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none ring-cyan-500/40 focus:ring"
				>
					<option value="low">low</option>
					<option value="medium">medium</option>
					<option value="high">high</option>
				</select>

				<div className="sm:col-span-2 mt-2 flex flex-wrap gap-3">
					<button
						type="submit"
						className="rounded-lg bg-cyan-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-cyan-600"
					>
						Add Obligation
					</button>

					<button
						type="button"
						onClick={onAnalyze}
						className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-600"
					>
						Analyze
					</button>
				</div>
			</form>
		</section>
	)
}

export default InputForm
