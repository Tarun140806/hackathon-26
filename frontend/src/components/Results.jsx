function Results({ analysisResult }) {
	if (!analysisResult) {
		return (
			<section className="rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
				<p className="text-slate-300">No results yet</p>
			</section>
		)
	}

	const {
		cash_balance,
		total_obligations,
		shortfall,
		days_to_zero,
		prioritized_obligations = [],
		reasoning,
	} = analysisResult

	return (
		<section className="space-y-5 rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
			<h2 className="text-2xl font-semibold text-white">Analysis Results</h2>

			<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
				<div className="rounded-lg bg-slate-950 p-4">
					<p className="text-xs uppercase tracking-wide text-slate-400">Cash Balance</p>
					<p className="mt-1 text-lg font-semibold text-white">{cash_balance ?? '-'}</p>
				</div>
				<div className="rounded-lg bg-slate-950 p-4">
					<p className="text-xs uppercase tracking-wide text-slate-400">Total Obligations</p>
					<p className="mt-1 text-lg font-semibold text-white">{total_obligations ?? '-'}</p>
				</div>
				<div className="rounded-lg bg-slate-950 p-4">
					<p className="text-xs uppercase tracking-wide text-slate-400">Shortfall</p>
					<p className="mt-1 text-lg font-semibold text-white">{shortfall ?? '-'}</p>
				</div>
				<div className="rounded-lg bg-slate-950 p-4">
					<p className="text-xs uppercase tracking-wide text-slate-400">Days to Zero</p>
					<p className="mt-1 text-lg font-semibold text-white">{days_to_zero ?? '-'}</p>
				</div>
			</div>

			<div>
				<h3 className="mb-2 text-lg font-medium text-white">Prioritized Obligations</h3>
				{prioritized_obligations.length === 0 ? (
					<p className="text-slate-300">No results yet</p>
				) : (
					<div className="space-y-2">
						{prioritized_obligations.map((item) => (
							<div
								key={item.id || `${item.vendor}-${item.amount}`}
								className="rounded-lg bg-slate-950 p-4"
							>
								<p className="font-semibold text-white">{item.vendor}</p>
								<p className="text-sm text-slate-300">Amount: {item.amount}</p>
								<p className="text-sm text-slate-300">Risk Level: {item.risk_level}</p>
								<p className="text-sm text-slate-300">Can Pay: {item.can_pay ? 'Yes' : 'No'}</p>
							</div>
						))}
					</div>
				)}
			</div>

			<div className="rounded-lg bg-slate-950 p-4">
				<h3 className="text-lg font-medium text-white">Reasoning</h3>
				<p className="mt-1 text-slate-300">{reasoning || 'No results yet'}</p>
			</div>
		</section>
	)
}

export default Results
