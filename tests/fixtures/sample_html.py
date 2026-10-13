"""
Sample HTML fixtures for testing (no network calls).
"""

# Clean JSON-LD example
JSONLD_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Wool Blend Jacket - Test Brand</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Wool Blend Textured Jacket",
        "brand": {
            "@type": "Brand",
            "name": "Test Brand"
        },
        "description": "Premium wool blend jacket with textured finish",
        "image": "https://example.com/images/jacket1.jpg",
        "offers": {
            "@type": "Offer",
            "price": "89.99",
            "priceCurrency": "GBP",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</head>
<body>
    <h1>Wool Blend Textured Jacket</h1>
    <p class="brand">Test Brand</p>
    <p class="price">£89.99</p>
    <div class="composition">
        <h3>Composition</h3>
        <p>Shell: 60% Wool, 40% Polyester. Lining: 100% Polyester</p>
    </div>
    <div class="care">
        <h3>Care Instructions</h3>
        <p>Dry clean only</p>
    </div>
</body>
</html>
"""

# OpenGraph example (no JSON-LD)
OPENGRAPH_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cotton Canvas Jacket</title>
    <meta property="og:title" content="Cotton Canvas Padded Jacket" />
    <meta property="og:description" content="Premium cotton canvas jacket" />
    <meta property="og:image" content="https://example.com/images/jacket2.jpg" />
    <meta property="product:brand" content="Canvas Co" />
    <meta property="product:price:amount" content="65.00" />
    <meta property="product:price:currency" content="GBP" />
</head>
<body>
    <h1>Cotton Canvas Padded Jacket</h1>
    <p class="materials">
        Materials: Outer: 100% Cotton. Padding: 100% Polyester. Lining: 100% Cotton
    </p>
    <p class="origin">Made in China</p>
</body>
</html>
"""

# Heuristic example (minimal structured data)
HEURISTIC_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Designer Jacket - Fashion Store</title>
</head>
<body>
    <div class="product-page">
        <h1>Herringbone Wool Jacket</h1>
        <div class="brand-name">Fashion House</div>
        <div class="product-price">£125.00</div>
        <div class="product-details">
            <h4>Fabric Information</h4>
            <p>Shell: 70% Wool, 25% Polyamide, 5% Elastane</p>
            <p>Lining: 100% Viscose</p>
        </div>
        <div class="care-info">
            <p>Washing: Machine wash at 30°C. Do not tumble dry.</p>
        </div>
        <img src="https://example.com/jacket3.jpg" alt="Product Image" class="product-image" />
    </div>
</body>
</html>
"""

# Minimal data example (test low confidence)
MINIMAL_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jacket Product Page</title>
</head>
<body>
    <h1>Generic Jacket</h1>
    <p>A nice jacket for everyday wear.</p>
    <img src="https://example.com/generic.jpg" />
</body>
</html>
"""

# Multi-offer example (multiple sizes/colors)
MULTI_OFFER_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Color Jacket</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Classic Bomber Jacket",
        "brand": {
            "@type": "Brand",
            "name": "Urban Wear"
        },
        "offers": [
            {
                "@type": "Offer",
                "price": "79.99",
                "priceCurrency": "GBP",
                "color": "Black",
                "size": "M"
            },
            {
                "@type": "Offer",
                "price": "79.99",
                "priceCurrency": "GBP",
                "color": "Navy",
                "size": "M"
            },
            {
                "@type": "Offer",
                "price": "79.99",
                "priceCurrency": "GBP",
                "color": "Black",
                "size": "L"
            }
        ]
    }
    </script>
</head>
<body>
    <h1>Classic Bomber Jacket</h1>
    <p>Available in multiple colors and sizes</p>
    <div class="materials">
        Shell: 100% Nylon. Fill: 80% Down, 20% Feather. Lining: 100% Polyester
    </div>
</body>
</html>
"""

# Materials with non-100% sum example
MATERIALS_DISCREPANCY_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jacket With Partial Materials</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Partial Materials Jacket",
        "brand": "Test Co",
        "offers": {
            "@type": "Offer",
            "price": "45.00",
            "priceCurrency": "GBP"
        }
    }
    </script>
</head>
<body>
    <div class="composition">
        Shell: 60% Cotton, 35% Polyester
        Lining: 100% Polyester
    </div>
</body>
</html>
"""

# Empty/malformed example
EMPTY_SAMPLE = """
<!DOCTYPE html>
<html>
<head><title>Empty</title></head>
<body></body>
</html>
"""

# ASOS JavaScript config example
ASOS_JS_CONFIG_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>ASOS Wool Blend Jacket</title>
    <script type="text/javascript">
    window.asos = window.asos || {};
    window.asos.pdp = window.asos.pdp || {};
    window.asos.pdp.config = {};
    window.asos.pdp.config.productDescription = {
        "productDescriptionVisible": true,
        "productDescription": "Plain design<br>Spread collar<br>Button placket",
        "sizeAndFit": "Model's height: 173cm / 5' 8''<br/>Model is wearing: S - UK 8-10",
        "careInfo": "Dry clean only",
        "aboutMe": "Shell: 78% Polyester, 21% Wool, 1% Acrylic. Lining: 100% Polyester"
    };
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "ASOS DESIGN wool blend jacket",
        "brand": {
            "@type": "Brand",
            "name": "ASOS DESIGN"
        },
        "offers": {
            "@type": "Offer",
            "price": "63.00",
            "priceCurrency": "GBP"
        }
    }
    </script>
</head>
<body>
    <h1>ASOS DESIGN wool blend jacket</h1>
</body>
</html>
"""
