import React from 'react'
import { SavingsCard } from './SavingsCard'
import { LoanCard } from './LoanCard'

export function App(): JSX.Element{
  return (
    <div style={{fontFamily:'ui-sans-serif, system-ui', padding:24}}>
      <h1>FinCalc — TSX</h1>
      <p>Demo app used to show how context engineering guides Copilot Agent Mode.</p>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:24}}>
        <SavingsCard/>
        <LoanCard/>
      </div>
    </div>
  )
}
