/**
 * Background Service Worker
 * Handles API calls from content scripts (bypasses Mixed Content restrictions)
 */

const API_URL = 'http://localhost:8000/api/evaluate';

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'evaluate') {
    // Make API call on behalf of content script
    evaluateProduct(request.html, request.url)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    // Return true to indicate we'll respond asynchronously
    return true;
  }

  if (request.action === 'openSettings') {
    chrome.runtime.openOptionsPage();
  }

  return true;
});

/**
 * Call backend API to evaluate product
 */
async function evaluateProduct(html, url) {
  console.log('[Seams Background] Calling API...');

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ html, url })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const result = await response.json();

  if (result.error) {
    throw new Error(result.error);
  }

  return result;
}

console.log('[Seams] Service worker loaded');
