/**
 * Seams web demo: runs the Python engine (tools/) in the browser with Pyodide
 * and renders results with the browser extension's overlay (overlay.js).
 */

const TOOL_MODULES = [
  '__init__', 'pipeline', 'product_extractor', 'materials_parser',
  'garment_detector', 'tshirt_evaluator', 'hoodie_evaluator', 'jeans_evaluator',
];

const SAMPLES = {
  premium_tee: {
    name: 'Heavyweight Organic Crew T-Shirt', brand: 'Example Basics', price: 32, currency: 'USD',
    materials: '100% combed and ring-spun organic cotton. 6.0 oz (200 GSM) jersey, 30 singles. ' +
      'Side-seamed construction with shoulder-to-shoulder taping and double-needle hems. Preshrunk.',
  },
  budget_tee: {
    name: 'Everyday Crew Neck Tee', brand: '', price: 6, currency: 'GBP',
    materials: '65% polyester, 35% cotton. Machine wash.',
  },
  hoodie: {
    name: 'Heavyweight Pullover Hoodie', brand: 'Example Basics', price: 85, currency: 'USD',
    materials: '100% cotton loopback French terry, 450 GSM. Double-layer hood, ribbed cuffs and hem ' +
      'with spandex, flatlock seams, kangaroo pocket. Garment dyed and preshrunk.',
  },
  jeans: {
    name: 'Straight Fit Selvedge Jeans', brand: '', price: 180, currency: 'USD',
    materials: '100% cotton 14.5oz raw selvedge denim. Chain-stitched hems, copper rivets, ' +
      'bar tacks at stress points. Unsanforized, made in Japan.',
  },
  stretch_jeans: {
    name: 'Skinny Fit Jeans', brand: '', price: 35, currency: 'GBP',
    materials: '78% cotton, 20% polyester, 2% elastane. 9oz stretch denim.',
  },
};

const EXAMPLE_PAGE = `<!DOCTYPE html>
<html><head><title>Classic Pullover Hoodie | Example Store</title>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"Classic Pullover Hoodie",
 "brand":{"@type":"Brand","name":"Example Store"},
 "material":"80% cotton, 20% polyester",
 "description":"Midweight 300 GSM brushed fleece. Single-layer hood with drawstring, kangaroo pocket, ribbed cuffs.",
 "offers":{"@type":"Offer","price":"45.00","priceCurrency":"USD"}}
<\/script></head>
<body><h1>Classic Pullover Hoodie</h1><p>$45.00</p></body></html>`;

const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const rawEl = document.getElementById('raw');
const detailsForm = document.getElementById('details-form');
const htmlForm = document.getElementById('html-form');

let pyodide = null;
let scrollToResult = false; // only after the visitor asks for a result

function setStatus(message, { spinner = false, error = false } = {}) {
  statusEl.hidden = !message;
  statusEl.classList.toggle('error', error);
  statusEl.querySelector('.spinner').hidden = !spinner;
  statusEl.querySelector('p').textContent = message || '';
}

async function loadEngine() {
  pyodide = await loadPyodide();
  await pyodide.loadPackage(['beautifulsoup4', 'lxml']);

  // Copy the engine's Python modules into Pyodide's virtual filesystem
  pyodide.FS.mkdirTree('/seams/tools');
  await Promise.all(TOOL_MODULES.map(async (name) => {
    const res = await fetch(`tools/${name}.py`);
    if (!res.ok) throw new Error(`Could not load tools/${name}.py`);
    pyodide.FS.writeFile(`/seams/tools/${name}.py`, await res.text());
  }));

  pyodide.runPython(`
import sys, json
sys.path.insert(0, "/seams")
from tools.pipeline import evaluate_details, evaluate_html

def run_details(args_json):
    a = json.loads(args_json)
    return json.dumps(evaluate_details(a["name"], a["materials"], a["price"], a["currency"], a["brand"]))

def run_html(html):
    return json.dumps(evaluate_html(html, None))
`);
}

function runPython(fnName, arg) {
  return JSON.parse(pyodide.globals.get(fnName)(arg));
}

function render(result) {
  if (!result.extraction.product_name && !result.extraction.materials_text) {
    setStatus("Couldn't find a product name or materials in that page. Try the \"Describe a product\" tab instead.", { error: true });
    resultEl.innerHTML = '';
    rawEl.hidden = true;
    return;
  }
  setStatus('');
  injectOverlay(result); // from overlay.js — appends #seams-overlay to <body>
  const overlay = document.getElementById('seams-overlay');
  resultEl.replaceChildren(overlay);

  const notes = result.extraction.notes || [];
  if (result.extraction.method && result.extraction.method !== 'manual') {
    const meta = document.createElement('p');
    meta.className = 'extraction-meta';
    meta.textContent = `Detected ${result.extraction.garment_type} · extracted via ${result.extraction.method}` +
      ` (${result.extraction.confidence} confidence)` + (notes.length ? ` · ${notes.join('; ')}` : '');
    resultEl.prepend(meta);
  }

  rawEl.hidden = false;
  rawEl.querySelector('pre').textContent = JSON.stringify(result, null, 2);
  if (scrollToResult && window.matchMedia('(max-width: 860px)').matches) {
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function safely(fn) {
  try {
    render(fn());
  } catch (err) {
    console.error(err);
    setStatus(`Something went wrong evaluating that product: ${err.message.split('\n').slice(-2).join(' ')}`, { error: true });
  }
}

detailsForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const f = new FormData(detailsForm);
  const price = f.get('price') === '' ? null : Number(f.get('price'));
  safely(() => runPython('run_details', JSON.stringify({
    name: f.get('name').trim(), brand: f.get('brand').trim(),
    materials: f.get('materials').trim(), price, currency: f.get('currency'),
  })));
});

htmlForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const html = new FormData(htmlForm).get('html');
  if (!html.trim()) return;
  safely(() => runPython('run_html', html));
});

document.querySelectorAll('[data-sample]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const s = SAMPLES[btn.dataset.sample];
    for (const [key, value] of Object.entries(s)) {
      detailsForm.elements[key === 'materials' ? 'materials' : key].value = value ?? '';
    }
    if (pyodide) detailsForm.requestSubmit();
  });
});

document.getElementById('load-example-page').addEventListener('click', () => {
  htmlForm.elements.html.value = EXAMPLE_PAGE;
  if (pyodide) htmlForm.requestSubmit();
});

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((t) => {
      t.classList.toggle('active', t === tab);
      t.setAttribute('aria-selected', t === tab);
    });
    document.querySelectorAll('.tab-panel').forEach((p) => { p.hidden = p.dataset.panel !== tab.dataset.tab; });
  });
});

loadEngine()
  .then(() => {
    document.querySelectorAll('button.primary').forEach((b) => { b.disabled = false; b.textContent = 'Evaluate'; });
    setStatus('Pick an example or enter a product to see its scores.');
    // Show something straight away
    document.querySelector('[data-sample="premium_tee"]').click();
    scrollToResult = true;
  })
  .catch((err) => {
    console.error(err);
    setStatus(`Couldn't load the Python engine: ${err.message}. Check your connection and reload.`, { error: true });
  });
