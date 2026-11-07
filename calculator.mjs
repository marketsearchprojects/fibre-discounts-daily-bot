const moneyFields = ['firstPrice', 'laterPrice', 'extras', 'upfront', 'switching', 'reward', 'reimbursement'];
const round = value => Math.round((value + Number.EPSILON) * 100) / 100;

export function calculate(input, includeRewards = false) {
  const p = {};
  for (const key of ['months', 'initialMonths', ...moneyFields]) {
    if (input[key] === '' || input[key] === null || input[key] === undefined) throw new Error('Complete every number field.');
    p[key] = Number(input[key]);
    if (!Number.isFinite(p[key]) || p[key] < 0) throw new Error('Use finite, non-negative numbers.');
  }
  if (!Number.isInteger(p.months) || p.months < 1 || p.months > 120) throw new Error('Use a whole comparison period from 1 to 120 months.');
  if (!Number.isInteger(p.initialMonths) || p.initialMonths > p.months) throw new Error('The first-price period must be a whole number between zero and the comparison period.');
  for (const key of moneyFields) {
    if (p[key] > 1000000 || Math.abs(p[key] * 100 - Math.round(p[key] * 100)) > 0.00001) throw new Error('Use pounds and pence, with at most two decimal places, up to £1,000,000.');
  }
  const gross = round(p.initialMonths * p.firstPrice + (p.months - p.initialMonths) * p.laterPrice + p.months * p.extras + p.upfront + p.switching);
  const conditionalNet = round(gross - p.reward - p.reimbursement);
  const total = includeRewards ? conditionalNet : gross;
  return { ...p, gross, conditionalNet, total, monthly: round(total / p.months), includeRewards };
}

export function comparisonCsv(a, b) {
  const fields = ['months', 'initialMonths', ...moneyFields, 'gross', 'conditionalNet', 'includeRewards', 'total', 'monthly'];
  const header = ['offer', ...fields].join(',');
  return [header, ...[a, b].map((offer, i) => [`Offer ${i === 0 ? 'A' : 'B'}`, ...fields.map(key => offer[key])].join(','))].join('\r\n') + '\r\n';
}

if (typeof document !== 'undefined') {
  const form = document.getElementById('comparison');
  const error = document.getElementById('error');
  const download = document.getElementById('download');
  const currency = value => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(value);
  let comparison;
  function render() {
    try {
      const data = new FormData(form);
      const months = data.get('months');
      const include = data.has('include-rewards');
      comparison = ['a', 'b'].map(prefix => calculate(Object.fromEntries([['months', months], ...['initialMonths', ...moneyFields].map(key => [key, data.get(`${prefix}-${key}`)])]), include));
      for (const [i, offer] of comparison.entries()) {
        const prefix = i === 0 ? 'a' : 'b';
        document.getElementById(`${prefix}-total`).textContent = currency(offer.total);
        document.getElementById(`${prefix}-detail`).textContent = `${currency(offer.monthly)} monthly equivalent over ${offer.months} months. Gross commitment: ${currency(offer.gross)}.`;
      }
      document.getElementById('result-heading').textContent = include ? 'Conditional scenario · assumes entered rewards and reimbursements are received' : 'Gross commitment · rewards not deducted';
      const difference = round(comparison[0].total - comparison[1].total);
      document.getElementById('difference').textContent = difference === 0 ? 'The offers have equal cost over this comparison period.' : `Offer ${difference > 0 ? 'B' : 'A'} costs ${currency(Math.abs(difference))} less over the comparison period${include ? ', if the entered rewards and reimbursements are received' : ''}.`;
      error.hidden = true;
      document.querySelector('.results').hidden = false;
      download.disabled = false;
    } catch (e) {
      comparison = null;
      error.textContent = e.message;
      error.hidden = false;
      document.querySelector('.results').hidden = true;
      download.disabled = true;
    }
  }
  form.addEventListener('input', render);
  form.addEventListener('submit', event => event.preventDefault());
  download.addEventListener('click', () => {
    if (!comparison) return;
    const url = URL.createObjectURL(new Blob([comparisonCsv(...comparison)], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'broadband-cost-comparison.csv';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
  render();
}
