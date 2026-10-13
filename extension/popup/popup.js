/**
 * Extension Popup Logic
 */

// Load saved API URL
chrome.storage.sync.get(['apiUrl'], (result) => {
  if (result.apiUrl) {
    document.getElementById('apiUrl').value = result.apiUrl;
  }
});

// Save settings
document.getElementById('save').addEventListener('click', () => {
  const apiUrl = document.getElementById('apiUrl').value;

  chrome.storage.sync.set({ apiUrl }, () => {
    // Show saved confirmation
    const button = document.getElementById('save');
    const originalText = button.textContent;
    button.textContent = '✓ Saved!';
    button.style.background = '#10b981';

    setTimeout(() => {
      button.textContent = originalText;
      button.style.background = '#0ea5e9';
    }, 2000);
  });
});
