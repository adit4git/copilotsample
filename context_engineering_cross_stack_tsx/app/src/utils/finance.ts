export function currency(n: number, locale = 'en-US', ccy = 'USD'): string {
  return new Intl.NumberFormat(locale, {style: 'currency', currency: ccy}).format(Number.isFinite(n)? n: 0)
}
export function futureValue(monthly: number, annualRatePct: number, years: number): number{
  const r = annualRatePct/100/12, n = Math.round(years*12)
  if(r===0) return monthly*n
  return monthly * (((1+r)**n - 1)/r)
}
export function loanPayment(principal: number, annualRatePct: number, years: number): number{
  const r = annualRatePct/100/12, n = Math.round(years*12)
  if(r===0) return principal/n
  const pow = (1+r)**n
  return principal * (r*pow)/(pow-1)
}
