import React, {useMemo, useState} from 'react'
import { futureValue, currency } from '../utils/finance'

export function SavingsCard(): JSX.Element{
  const [monthly, setMonthly] = useState<number>(500)
  const [rate, setRate] = useState<number>(5)
  const [years, setYears] = useState<number>(5)
  const fv = useMemo(()=>futureValue(monthly, rate, years), [monthly, rate, years])
  return (
    <div style={{border:'1px solid #ddd', borderRadius:12, padding:16}}>
      <h2>Savings</h2>
      <label>Monthly ($)<input type="number" value={monthly} onChange={e=>setMonthly(+e.target.value)} /></label>
      <label>Rate %<input type="number" value={rate} onChange={e=>setRate(+e.target.value)} /></label>
      <label>Years<input type="number" value={years} onChange={e=>setYears(+e.target.value)} /></label>
      <p><strong>Future Value:</strong> {currency(fv)}</p>
    </div>
  )
}
