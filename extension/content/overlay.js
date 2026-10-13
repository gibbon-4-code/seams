/**
 * Overlay UI Injection
 * Injects evaluation results as floating badge overlay (from tshirt-evaluator-ui-mockup.html)
 */

/**
 * Inject overlay with evaluation results
 * @param {{extraction: object, evaluation: object}} data
 */
function injectOverlay(data) {
  const { extraction, evaluation } = data;

  // Remove existing overlay
  const existing = document.getElementById('seams-overlay');
  if (existing) {
    existing.remove();
  }

  // Create overlay container
  const overlay = document.createElement('div');
  overlay.id = 'seams-overlay';
  overlay.className = 'seams-extension-container';

  // Map quality tier to badge class and text
  const tierMap = {
    'excellent': { class: 'excellent', text: '✓ Excellent Quality - Highly Recommended' },
    'good': { class: 'good', text: '✓ Good Quality - Recommended Buy' },
    'average': { class: 'average', text: '⚠ Average Quality - Consider Alternatives' },
    'fair': { class: 'average', text: '⚠ Fair Quality - Consider Alternatives' },
    'poor': { class: 'poor', text: '⚠ Poor Quality - Not Recommended' },
    'unknown': { class: 'average', text: '? Quality Unknown - Insufficient Data' }
  };

  const tier = tierMap[evaluation.quality_tier] || tierMap['unknown'];

  // Build HTML
  overlay.innerHTML = `
    <div class="seams-header">
      <div class="seams-header-title">Seams Quality Evaluation</div>
      <button class="seams-close-btn" onclick="document.getElementById('seams-overlay').remove()">✕</button>
    </div>

    <div class="seams-content">
      <div class="seams-overall-badge ${tier.class}">
        ${tier.text}
      </div>

      <!-- Product Info -->
      ${buildProductInfo(extraction)}

      <!-- Key Specs Chips -->
      ${buildKeySpecsChips(evaluation)}

      <!-- TRANSPARENCY SCORE (6th metric) -->
      ${evaluation.transparency_score !== undefined ? buildMetricSection(
        '🔍', 'Transparency Score',
        evaluation.transparency_score, 10,
        'Hiding details', 'Full disclosure',
        evaluation.explanations.transparency
      ) : ''}

      <!-- Dynamic metrics from evaluator -->
      ${buildDynamicMetrics(evaluation)}

      <!-- Warnings -->
      ${buildWarnings(evaluation.warnings)}

      <!-- Ask Customer Service -->
      ${buildAskCS(evaluation.ask_customer_service)}

      <!-- Cost Per Wear Summary -->
      ${buildSummary(evaluation)}

      <!-- Care Impact Calculator -->
      ${buildCareImpact(evaluation)}

      <!-- Failure Modes (jeans) -->
      ${buildFailureModes(evaluation.failure_modes)}
    </div>
  `;

  document.body.appendChild(overlay);
}

/**
 * Build product info section
 */
function buildProductInfo(extraction) {
  const price = extraction.price
    ? `${extraction.price.currency || ''} ${extraction.price.amount || ''}`
    : 'Price unknown';

  const placeholderEmoji = extraction.garment_type === 'jeans' ? '👖' :
                           extraction.garment_type === 'hoodie' ? '🧥' : '👕';
  const image = extraction.images && extraction.images[0]
    ? `<img src="${extraction.images[0]}" class="seams-product-image" alt="Product">`
    : `<div class="seams-product-image seams-product-image-placeholder">${placeholderEmoji}</div>`;

  return `
    <div class="seams-listing-info">
      ${image}
      <div class="seams-product-details">
        <div class="seams-product-name">${extraction.product_name || 'Product'}</div>
        <div class="seams-product-price">${price}</div>
      </div>
    </div>
  `;
}

/**
 * Build key specs chips
 */
function buildKeySpecsChips(evaluation) {
  if (!evaluation.metadata) return '';

  const metadata = evaluation.metadata;
  const chips = [];

  if (evaluation.garment_type === 'jeans') {
    // --- Jeans-specific chips ---

    // Denim weight
    if (metadata.denim_weight_oz) {
      chips.push({ text: `${metadata.denim_weight_oz}oz`, class: metadata.denim_weight_oz >= 14 ? 'highlight' : '' });
    }

    // Selvage
    if (metadata.construction_features?.selvage) {
      chips.push({ text: 'Selvage', class: 'highlight' });
    }

    // Chain stitch
    if (metadata.construction_features?.chain_stitch) {
      chips.push({ text: 'Chain stitch', class: 'highlight' });
    }

    // Fit type
    if (metadata.fit_type && metadata.fit_type !== 'unknown') {
      chips.push({ text: metadata.fit_type.charAt(0).toUpperCase() + metadata.fit_type.slice(1), class: '' });
    }

    // Treatment
    if (metadata.treatment && metadata.treatment !== 'unknown') {
      const treatmentClass = metadata.treatment === 'raw' ? 'highlight' :
                             metadata.treatment === 'distressed' ? 'warning' : '';
      chips.push({ text: metadata.treatment.charAt(0).toUpperCase() + metadata.treatment.slice(1), class: treatmentClass });
    }

    // Mill
    if (metadata.mill) {
      chips.push({ text: metadata.mill.charAt(0).toUpperCase() + metadata.mill.slice(1), class: 'highlight' });
    }

    // Gender
    if (metadata.gender === 'women') {
      chips.push({ text: "Women's", class: '' });
    }
  } else if (evaluation.garment_type === 'hoodie') {
    // --- Hoodie-specific chips ---

    // GSM / weight
    if (metadata.gsm) {
      const gsmClass = metadata.gsm >= 400 ? 'highlight' : metadata.gsm < 280 ? 'warning' : '';
      chips.push({ text: `${Math.round(metadata.gsm)} GSM`, class: gsmClass });
    }

    // Fleece type
    if (metadata.fleece_type && metadata.fleece_type !== 'unknown') {
      const fleeceClass = metadata.fleece_type === 'french_terry' ? 'highlight' : '';
      chips.push({ text: metadata.fleece_type.replace('_', ' '), class: fleeceClass });
    }

    // Hoodie type (only show non-default)
    if (metadata.hoodie_type && metadata.hoodie_type !== 'pullover' && metadata.hoodie_type !== 'unknown') {
      chips.push({ text: metadata.hoodie_type.replace('_', ' '), class: '' });
    }

    // Special construction
    if (metadata.special_construction?.reverse_weave) {
      chips.push({ text: 'Reverse Weave', class: 'highlight' });
    }
    if (metadata.special_construction?.garment_dyed) {
      chips.push({ text: 'Garment-dyed', class: 'highlight' });
    }

    // Construction highlights
    if (metadata.construction_features?.side_seamed) {
      chips.push({ text: 'Side-seamed', class: 'highlight' });
    }

    // Origin
    if (metadata.origin) {
      chips.push({ text: `Made in ${metadata.origin.charAt(0).toUpperCase() + metadata.origin.slice(1)}`, class: 'highlight' });
    }

  } else {
    // --- T-shirt chips ---

    // Cotton type
    if (metadata.cotton_type && metadata.cotton_type !== 'carded') {
      chips.push({
        text: metadata.cotton_type.replace('_', ' '),
        class: 'highlight'
      });
    } else if (metadata.cotton_type === 'carded' || metadata.cotton_description?.includes('Unspecified')) {
      chips.push({
        text: 'Unspecified cotton',
        class: 'warning'
      });
    }

    // Construction
    if (metadata.construction_features?.side_seamed) {
      chips.push({ text: 'Side-seamed', class: 'highlight' });
    } else if (metadata.construction_features?.tubular) {
      chips.push({ text: 'Tubular', class: 'warning' });
    }

    // GSM
    if (metadata.gsm) {
      chips.push({ text: `${Math.round(metadata.gsm)} GSM`, class: '' });
    }

    // Preshrunk
    if (metadata.construction_features?.preshrunk) {
      chips.push({ text: 'Preshrunk', class: 'highlight' });
    }
  }

  if (chips.length === 0) return '';

  return `
    <div class="seams-key-specs">
      ${chips.map(chip => `
        <span class="seams-spec-chip ${chip.class}">
          ${chip.text}
        </span>
      `).join('')}
    </div>
  `;
}

/**
 * Build metric section with slider
 */
function buildMetricSection(icon, label, score, maxScore, leftLabel, rightLabel, explanation) {
  const percentage = (score / maxScore) * 100;
  const tierClass = percentage >= 80 ? 'excellent' :
                    percentage >= 60 ? 'good' :
                    percentage >= 40 ? 'average' : 'poor';

  const uniqueId = 'seams-metric-' + Math.random().toString(36).substr(2, 9);

  return `
    <div class="seams-metric-section">
      <div class="seams-metric-header">
        <div class="seams-metric-label">
          <span class="seams-metric-icon">${icon}</span>
          ${label}
        </div>
        <button class="seams-see-why-button" onclick="
          const exp = document.getElementById('${uniqueId}');
          exp.classList.toggle('open');
          this.querySelector('.seams-chevron').classList.toggle('open');
        ">
          <span class="seams-score-value">${score}/${maxScore}</span>
          <span class="seams-chevron">▼</span>
        </button>
      </div>
      <div class="seams-slider-container">
        <div class="seams-slider-fill ${tierClass}" style="width: ${percentage}%;"></div>
      </div>
      <div class="seams-slider-labels">
        <span>${leftLabel}</span>
        <span>${rightLabel}</span>
      </div>
      <div class="seams-metric-explanation" id="${uniqueId}">
        ${explanation}
      </div>
    </div>
  `;
}

/**
 * Build dynamic metrics from metric_definitions (works for both t-shirts and jeans)
 */
function buildDynamicMetrics(evaluation) {
  // Fallback metric definitions for older API responses without metric_definitions
  const TSHIRT_DEFAULTS = [
    { key: 'shrinkage', icon: '💧', label: 'Will it shrink?', left_label: 'High risk', right_label: 'Low risk', max_score: 5 },
    { key: 'pilling', icon: '🧶', label: 'Will it pill?', left_label: 'High pilling', right_label: 'No pilling', max_score: 5 },
    { key: 'longevity', icon: '⏱️', label: 'How long will it last?', left_label: '6 months', right_label: '3+ years', max_score: 5 },
    { key: 'value', icon: '💰', label: 'Value for money', left_label: 'Poor value', right_label: 'Excellent value', max_score: 5 },
    { key: 'care', icon: '🧺', label: 'Care difficulty', left_label: 'High maintenance', right_label: 'Easy care', max_score: 5 },
  ];

  const metrics = evaluation.metric_definitions || TSHIRT_DEFAULTS;

  return metrics.map(metric => {
    const score = evaluation.scores[metric.key];
    if (score === null || score === undefined) return '';
    return buildMetricSection(
      metric.icon, metric.label,
      score, metric.max_score,
      metric.left_label, metric.right_label,
      evaluation.explanations[metric.key] || ''
    );
  }).join('');
}

/**
 * Build warnings section
 */
function buildWarnings(warnings) {
  if (!warnings || warnings.length === 0) return '';

  return `
    <div class="seams-warnings">
      ${warnings.map(warning => `
        <div class="seams-warning">${warning}</div>
      `).join('')}
    </div>
  `;
}

/**
 * Build "Ask Customer Service" section
 */
function buildAskCS(questions) {
  if (!questions || questions.length === 0) return '';

  return `
    <div class="seams-ask-cs">
      <div class="seams-ask-cs-title">❓ Questions to ask customer service:</div>
      <ul class="seams-ask-cs-list">
        ${questions.map(q => `<li>${q}</li>`).join('')}
      </ul>
    </div>
  `;
}

/**
 * Build summary section
 */
function buildSummary(evaluation) {
  if (!evaluation.cost_per_wear || !evaluation.estimated_washes) return '';

  const currency = ''; // Could extract from price
  const cpw = evaluation.cost_per_wear.toFixed(2);
  const washes = evaluation.estimated_washes;

  return `
    <div class="seams-summary-section">
      <div class="seams-summary-highlight">
        <strong>Cost per wear:</strong> ${currency}${cpw} (${washes} estimated washes)
      </div>
    </div>
  `;
}

/**
 * Build care impact section showing how washing methods affect longevity
 */
function buildCareImpact(evaluation) {
  if (!evaluation.care_impact || !evaluation.care_impact.scenarios) return '';

  const { scenarios, recommendations, savings } = evaluation.care_impact;
  const toggleId = 'seams-care-toggle-' + Math.random().toString(36).substr(2, 9);

  // Color mapping for impact levels
  const impactClass = {
    'Best': 'best',
    'Good': 'good',
    'Standard': 'standard',
    'Worst': 'worst'
  };

  // Build scenarios rows
  const scenarioRows = scenarios.map(s => {
    const cls = impactClass[s.impact] || 'standard';
    const cpw = s.cost_per_wear !== undefined ? `$${s.cost_per_wear}/wear` : '';
    return `
      <div class="seams-care-scenario ${cls}">
        <div class="seams-care-scenario-method">${s.method}</div>
        <div class="seams-care-scenario-stats">
          <span class="seams-care-scenario-washes">${s.washes} washes</span>
          ${cpw ? `<span class="seams-care-scenario-cpw">${cpw}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');

  // Build savings banner
  const savingsBanner = savings ? `
    <div class="seams-care-savings">
      ${savings.summary}
    </div>
  ` : '';

  // Build recommendations
  const recsHtml = recommendations && recommendations.length > 0 ? `
    <ul class="seams-care-recommendations">
      ${recommendations.map(r => `<li>${r}</li>`).join('')}
    </ul>
  ` : '';

  return `
    <div class="seams-care-impact">
      <button class="seams-care-toggle" onclick="
        const body = document.getElementById('${toggleId}');
        body.classList.toggle('open');
        this.querySelector('.seams-chevron').classList.toggle('open');
      ">
        <span class="seams-care-toggle-label">Make it last</span>
        <span class="seams-chevron">&#9660;</span>
      </button>
      <div class="seams-care-body" id="${toggleId}">
        ${savingsBanner}
        <div class="seams-care-scenarios">
          ${scenarioRows}
        </div>
        ${recsHtml}
      </div>
    </div>
  `;
}

/**
 * Build failure modes section (jeans-specific)
 */
function buildFailureModes(failureModes) {
  if (!failureModes || failureModes.length === 0) return '';

  const riskColors = {
    'high': 'poor',
    'medium': 'average',
    'low': 'good'
  };

  return `
    <div class="seams-failure-modes">
      <div class="seams-failure-modes-title">Wear & Tear Risks</div>
      ${failureModes.map(mode => `
        <div class="seams-failure-mode">
          <span class="seams-failure-mode-name">${mode.mode}</span>
          <span class="seams-failure-mode-risk ${riskColors[mode.risk] || 'average'}">${mode.risk}</span>
        </div>
        <div class="seams-failure-mode-note">${mode.note}</div>
      `).join('')}
    </div>
  `;
}
