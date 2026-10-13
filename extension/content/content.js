/**
 * Seams Content Script
 * Runs on product pages to extract, evaluate, and display quality ratings
 */

// Configuration
const API_URL = 'http://localhost:8000/api/evaluate';
const RETRY_DELAY = 2000; // ms

// State
let evaluationInProgress = false;
let lastEvaluatedUrl = null;

/**
 * Main execution function
 */
async function evaluateProduct() {
  // Prevent duplicate evaluations
  if (evaluationInProgress) {
    console.log('[Seams] Evaluation already in progress');
    return;
  }

  // Prevent re-evaluation of same page
  if (lastEvaluatedUrl === window.location.href) {
    console.log('[Seams] Already evaluated this URL');
    return;
  }

  // Check if this is a product page
  const detection = detectProductPage();

  if (!detection.isProduct) {
    console.log('[Seams] Not a product page (signals:', detection.signals, ')');
    return;
  }

  console.log('[Seams] Product page detected (confidence:', detection.confidence, ')');

  evaluationInProgress = true;
  lastEvaluatedUrl = window.location.href;

  try {
    // Show loading overlay
    injectLoadingOverlay();

    // Extract HTML body
    const html = document.documentElement.outerHTML;
    const url = window.location.href;

    // Call backend API via background service worker (bypasses Mixed Content)
    console.log('[Seams] Sending to background service worker...');
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'evaluate', html, url },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve(response);
          }
        }
      );
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    const result = response.data;
    console.log('[Seams] Evaluation result:', result);

    // Remove loading overlay
    removeOverlay();

    // Inject results overlay
    injectOverlay(result);

  } catch (error) {
    console.error('[Seams] Evaluation failed:', error);
    removeOverlay();
    showErrorOverlay(error.message);
  } finally {
    evaluationInProgress = false;
  }
}

/**
 * Show error overlay
 */
function showErrorOverlay(errorMessage) {
  if (document.getElementById('seams-overlay')) {
    return;
  }

  const overlay = document.createElement('div');
  overlay.id = 'seams-overlay';
  overlay.className = 'seams-extension-container';

  overlay.innerHTML = `
    <div class="seams-header">
      <div class="seams-header-title">Seams Quality Evaluation</div>
      <button class="seams-close-btn" onclick="document.getElementById('seams-overlay').remove()">✕</button>
    </div>
    <div class="seams-content">
      <div class="seams-error">
        <div class="seams-error-icon">⚠️</div>
        <div class="seams-error-title">Evaluation Failed</div>
        <div class="seams-error-message">${errorMessage}</div>
        <button class="seams-retry-btn" onclick="window.location.reload()">Retry</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
}

/**
 * Show loading overlay
 */
function injectLoadingOverlay() {
  if (document.getElementById('seams-overlay')) {
    return;
  }

  const overlay = document.createElement('div');
  overlay.id = 'seams-overlay';
  overlay.className = 'seams-extension-container';

  overlay.innerHTML = `
    <div class="seams-header">
      <div class="seams-header-title">Seams Quality Evaluation</div>
      <button class="seams-close-btn" onclick="document.getElementById('seams-overlay').remove()">✕</button>
    </div>
    <div class="seams-content">
      <div class="seams-loading-state">
        <div class="seams-spinner"></div>
        <div class="seams-loading-text">
          Analyzing product listing...<br>
          Extracting fabric specifications...<br>
          Calculating quality scores...
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
}

/**
 * Remove overlay
 */
function removeOverlay() {
  const existing = document.getElementById('seams-overlay');
  if (existing) {
    existing.remove();
  }
}

// Run evaluation after page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(evaluateProduct, 500); // Small delay to let page fully render
  });
} else {
  setTimeout(evaluateProduct, 500);
}

// Re-evaluate if URL changes (for SPAs)
let lastUrl = window.location.href;
new MutationObserver(() => {
  const currentUrl = window.location.href;
  if (currentUrl !== lastUrl) {
    lastUrl = currentUrl;
    lastEvaluatedUrl = null; // Allow re-evaluation
    setTimeout(evaluateProduct, 1000);
  }
}).observe(document, { subtree: true, childList: true });
