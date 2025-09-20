async function main(){
  try {
    const d = await (await fetch('data/metrics.json')).json();
    const items = [
      ['Repo', d.repo],
      ['Stars', d.stars],
      ['Merged PRs (7d)', d.merged_prs_week],
      ['Commit Streak (days)', d.commit_streak_days],
      ['Errors Prevented (30d)', d.errors_prevented_month],
      ['False Positive Rate', percent(d.false_positive_rate)],
      ['MTTR (min)', d.mttr_minutes],
      ['Money Saved (30d)', currency(d.money_saved_usd_month)],
      ['Live Customers', d.customers_live],
      ['Uptime %', percent(d.uptime_pct)]
    ];
    document.getElementById('grid').innerHTML = items.map(([k,v]) => card(k,v)).join('');
    document.getElementById('updated').textContent = `Updated: ${d.timestamp}`;
  } catch(e) {
    document.getElementById('grid').innerHTML = '<div class="card">No data yet. Run the metrics workflow.</div>';
  }
}
function card(k,v){ return `<div class="card"><div class="muted">${k}</div><div style="font-size:1.8rem;font-weight:600">${v ?? '—'}</div></div>`; }
function percent(x){ return (x==null) ? '—' : (Math.round(x*1000)/10)+'%'; }
function currency(x){ return (x==null) ? '—' : Intl.NumberFormat(undefined,{style:'currency',currency:'USD',maximumFractionDigits:0}).format(x); }
main();
