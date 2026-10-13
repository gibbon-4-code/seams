/**
 * Product Page Detection Library
 * Detects if current page is a product page using multiple signals
 */

const PRODUCT_PAGE_SIGNALS = {
  // Schema.org Product markup
  schemaProduct: () => {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        // Check for Product type directly or in @graph array
        if (data['@type'] === 'Product') {
          return true;
        }
        if (Array.isArray(data['@graph'])) {
          if (data['@graph'].some(item => item['@type'] === 'Product')) {
            return true;
          }
        }
      } catch (e) {
        // Invalid JSON, skip
      }
    }
    return false;
  },

  // OpenGraph product tags
  openGraph: () => {
    return !!document.querySelector('meta[property="og:type"][content="product"]');
  },

  // E-commerce UI patterns
  addToCart: () => {
    const patterns = [
      '[class*="add-to-cart" i]',
      '[class*="addtocart" i]',
      '[id*="add-to-cart" i]',
      '[id*="addToCart" i]',
      'button[class*="buy" i]',
      'button[class*="purchase" i]',
      'button[class*="add-to-bag" i]'
    ];
    return patterns.some(pattern => document.querySelector(pattern));
  },

  // Price indicators
  price: () => {
    const patterns = [
      '[class*="price" i]',
      '[itemprop="price"]',
      '[data-price]',
      '.product-price',
      '[class*="product-price" i]'
    ];
    return patterns.some(pattern => document.querySelector(pattern));
  },

  // Product images
  productImage: () => {
    const patterns = [
      '[class*="product" i] img',
      '[itemprop="image"]',
      '.product-image',
      '[class*="product-image" i]'
    ];
    return patterns.some(pattern => document.querySelector(pattern));
  },

  // URL patterns
  urlPattern: () => {
    const patterns = [
      /\/product[s]?\//i,
      /\/item[s]?\//i,
      /\/p\//i,
      /\/dp\//i,  // Amazon
      /\/collections\/.*\/products\//i,  // Shopify
      /\/shop\/.*\/product\//i,
      /\/catalogue\/.*\/product\//i
    ];
    return patterns.some(pattern => pattern.test(window.location.pathname));
  }
};

/**
 * Detect if current page is a product page
 * @returns {{isProduct: boolean, confidence: string, signals: number}}
 */
function detectProductPage() {
  const signals = Object.values(PRODUCT_PAGE_SIGNALS).map(fn => fn());
  const signalCount = signals.filter(Boolean).length;

  // Require at least 2 signals for confidence
  return {
    isProduct: signalCount >= 2,
    confidence: signalCount >= 3 ? 'high' : signalCount === 2 ? 'medium' : 'low',
    signals: signalCount
  };
}
