import React, {useMemo, useState} from 'react'
import { loanPayment, currency } from '../utils/finance'

export function LoanCard(): JSX.Element{
  const [principal, setPrincipal] = useState<number>(10000)
  const [rate, setRate] = useState<number>(6)
  const [years, setYears] = useState<number>(3)
  const pmt = useMemo(()=>loanPayment(principal, rate, years), [principal, rate, years])
  return (
    <div style={{border:'1px solid #ddd', borderRadius:12, padding:16}}>
      <h2>Loan</h2>
      <label>Principal ($)<input type="number" value={principal} onChange={e=>setPrincipal(+e.target.value)} /></label>
      <label>Rate %<input type="number" value={rate} onChange={e=>setRate(+e.target.value)} /></label>
      <label>Years<input type="number" value={years} onChange={e=>setYears(+e.target.value)} /></label>
      <p><strong>Monthly Payment:</strong> {currency(pmt)}</p>
    </div>
  )
}
