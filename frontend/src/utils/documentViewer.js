/**
 * Document Viewer Utility
 * Comprehensive device detection and document viewing strategies
 */

// Device detection utilities
export const DeviceDetector = {
  // Check if running in a mobile device
  isMobile() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;

    // Enhanced mobile detection with more patterns
    const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile|CriOS|FxiOS|EdgiOS|SamsungBrowser|UCBrowser|MiuiBrowser|HuaweiBrowser|Silk|Kindle|Googlebot-Mobile/i;
    const isMobileUA = mobileRegex.test(userAgent);

    // Check viewport meta tag (mobile sites usually have this)
    const viewport = document.querySelector('meta[name="viewport"]');
    const hasViewportMeta = viewport && viewport.content.includes('width=device-width');

    // Check screen size - consider both width and height
    const isMobileWidth = window.innerWidth <= 768;
    const isMobileHeight = window.innerHeight <= 1024;
    const isSmallScreen = isMobileWidth || (window.innerWidth <= 1024 && isMobileHeight);

    // Check touch capability
    const hasTouch = 'ontouchstart' in window ||
                    navigator.maxTouchPoints > 0 ||
                    navigator.msMaxTouchPoints > 0;

    // Check orientation API (mobile devices have this)
    const hasOrientation = window.orientation !== undefined;

    // Return true if definitely mobile UA, or if small screen with touch
    return isMobileUA || (isSmallScreen && hasTouch) || (hasViewportMeta && hasTouch) || hasOrientation;
  },

  // Check if running in a tablet
  isTablet() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    const isIPad = /iPad/i.test(userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isAndroidTablet = /Android/i.test(userAgent) && !/Mobile/i.test(userAgent);
    const screenWidth = window.innerWidth;

    return (isIPad || isAndroidTablet) || (screenWidth >= 768 && screenWidth <= 1024 && this.hasTouch());
  },

  // Check if device is iOS
  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
           (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  },

  // Check if device is Android
  isAndroid() {
    return /Android/i.test(navigator.userAgent);
  },

  // Check if running in WebView
  isWebView() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;

    // React Native WebView
    if (window.ReactNativeWebView) return true;

    // Android WebView
    if (userAgent.includes('wv')) return true;

    // iOS WebView
    if (/(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(userAgent)) return true;

    // Facebook/Instagram in-app browser
    if (userAgent.includes('FBAN') || userAgent.includes('FBAV') || userAgent.includes('Instagram')) return true;

    return false;
  },

  // Check browser type
  getBrowser() {
    const userAgent = navigator.userAgent;

    if (userAgent.includes('Chrome')) return 'chrome';
    if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) return 'safari';
    if (userAgent.includes('Firefox')) return 'firefox';
    if (userAgent.includes('Edge')) return 'edge';
    if (userAgent.includes('Opera') || userAgent.includes('OPR')) return 'opera';

    return 'unknown';
  },

  // Check if browser supports inline PDF viewing
  supportsPDFViewing() {
    // iOS Safari doesn't support inline PDF viewing well
    if (this.isIOS() && this.getBrowser() === 'safari') return false;

    // Older Android browsers have issues
    if (this.isAndroid()) {
      const match = navigator.userAgent.match(/Android\s+(\d+)/);
      const androidVersion = match ? parseInt(match[1]) : 0;
      if (androidVersion < 5) return false;
    }

    // WebView environments often have issues
    if (this.isWebView()) return false;

    return true;
  },

  // Check if device has touch capability
  hasTouch() {
    return 'ontouchstart' in window ||
           navigator.maxTouchPoints > 0 ||
           navigator.msMaxTouchPoints > 0;
  },

  // Get device type
  getDeviceType() {
    if (this.isMobile()) return 'mobile';
    if (this.isTablet()) return 'tablet';
    return 'desktop';
  },

  // Get viewport dimensions
  getViewport() {
    return {
      width: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0),
      height: Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
    };
  }
};

// PDF Viewer strategies
export const PDFViewerStrategies = {
  // Native iframe viewer (for desktop and capable browsers)
  native(url, options = {}) {
    const { height = '700px', className = '' } = options;
    return {
      type: 'iframe',
      src: `${url}#toolbar=0&navpanes=0&scrollbar=1&view=FitH`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy'
      }
    };
  },

  // Google Docs Viewer (universal fallback)
  googleDocs(url, options = {}) {
    const { height = '600px', className = '' } = options;
    const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
    return {
      type: 'iframe',
      src: `https://docs.google.com/viewer?url=${encodeURIComponent(fullUrl)}&embedded=true`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy'
      }
    };
  },

  // Microsoft Office Online Viewer (alternative)
  microsoftViewer(url, options = {}) {
    const { height = '600px', className = '' } = options;
    const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
    return {
      type: 'iframe',
      src: `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(fullUrl)}`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy'
      }
    };
  },

  // ViewerJS (open source alternative)
  viewerJS(url, options = {}) {
    const { height = '600px', className = '' } = options;
    return {
      type: 'iframe',
      src: `/ViewerJS/#${url}`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy'
      }
    };
  },

  // PDF.js viewer (most compatible)
  pdfJS(url, options = {}) {
    const { height = '600px', className = '' } = options;
    return {
      type: 'iframe',
      src: `/pdfjs/web/viewer.html?file=${encodeURIComponent(url)}`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy'
      }
    };
  },

  // API endpoint for mobile (with proper headers)
  apiEndpoint(url, options = {}) {
    const { height = '500px', className = '' } = options;
    return {
      type: 'iframe',
      src: `/api/method/lms.lms.api.serve_pdf_inline?file_url=${encodeURIComponent(url)}`,
      height: height,
      className: className,
      attributes: {
        frameborder: '0',
        allowfullscreen: true,
        loading: 'lazy',
        scrolling: 'yes'
      }
    };
  },

  // Download link with preview (last resort)
  downloadLink(url, options = {}) {
    const { fileName = 'document.pdf', buttonText = 'Download PDF' } = options;
    return {
      type: 'download',
      url: url,
      fileName: fileName,
      buttonText: buttonText,
      preview: true
    };
  }
};

// Main document viewer selector
export const DocumentViewer = {
  // Select best viewer strategy based on device and document type
  selectStrategy(url, documentType = 'pdf') {
    const device = DeviceDetector.getDeviceType();
    const browser = DeviceDetector.getBrowser();
    const supportsPDF = DeviceDetector.supportsPDFViewing();
    const isWebView = DeviceDetector.isWebView();
    const isMobile = DeviceDetector.isMobile();

    // For WebView environments, prioritize Google Docs
    if (isWebView) {
      return 'googleDocs';
    }

    // For mobile devices - prioritize Google Docs for better compatibility
    if (isMobile) {
      // Google Docs viewer works best across all mobile browsers
      return 'googleDocs';
    }

    // For iOS devices specifically
    if (DeviceDetector.isIOS()) {
      // iOS Safari and Chrome work best with Google Docs
      return 'googleDocs';
    }

    // For Android devices
    if (DeviceDetector.isAndroid()) {
      // Modern Android browsers can use Google Docs reliably
      return 'googleDocs';
    }

    // For tablets - try native first if supported
    if (device === 'tablet') {
      if (supportsPDF && !DeviceDetector.isIOS()) {
        return 'native';
      }
      return 'googleDocs';
    }

    // For desktop - native viewer works best
    if (device === 'desktop') {
      // Desktop browsers handle native PDF viewing well
      return 'native';
    }

    // Default fallback is Google Docs for universal compatibility
    return 'googleDocs';
  },

  // Get responsive height based on device
  getResponsiveHeight(device = null) {
    const deviceType = device || DeviceDetector.getDeviceType();
    const viewport = DeviceDetector.getViewport();
    const isPortrait = viewport.height > viewport.width;

    switch (deviceType) {
      case 'mobile':
        // Enhanced mobile height calculation
        // Consider orientation and ensure better visibility
        if (isPortrait) {
          // Portrait mode: use more vertical space
          const portraitHeight = viewport.height * 0.75;
          // Minimum 500px, maximum 70vh for better visibility
          return `${Math.max(500, Math.min(portraitHeight, viewport.height * 0.7))}px`;
        } else {
          // Landscape mode: use less vertical space to avoid scrolling
          const landscapeHeight = viewport.height * 0.85;
          // Minimum 400px, maximum 85vh
          return `${Math.max(400, Math.min(landscapeHeight, viewport.height * 0.85))}px`;
        }

      case 'tablet':
        // Tablets get more space
        const tabletHeight = viewport.height * (isPortrait ? 0.75 : 0.8);
        // Minimum 600px for better readability
        return `${Math.max(600, Math.min(tabletHeight, 800))}px`;

      case 'desktop':
      default:
        // Desktop gets optimal height
        const desktopHeight = viewport.height * 0.8;
        // Generous height for desktop viewing
        return `${Math.max(700, Math.min(desktopHeight, 900))}px`;
    }
  },

  // Get viewer configuration
  getViewerConfig(url, options = {}) {
    const strategy = options.strategy || this.selectStrategy(url, options.documentType);
    const height = options.height || this.getResponsiveHeight();

    const strategies = {
      native: () => PDFViewerStrategies.native(url, { ...options, height }),
      googleDocs: () => PDFViewerStrategies.googleDocs(url, { ...options, height }),
      microsoftViewer: () => PDFViewerStrategies.microsoftViewer(url, { ...options, height }),
      viewerJS: () => PDFViewerStrategies.viewerJS(url, { ...options, height }),
      pdfJS: () => PDFViewerStrategies.pdfJS(url, { ...options, height }),
      apiEndpoint: () => PDFViewerStrategies.apiEndpoint(url, { ...options, height }),
      downloadLink: () => PDFViewerStrategies.downloadLink(url, options)
    };

    return strategies[strategy] ? strategies[strategy]() : strategies.googleDocs();
  },

  // Check if URL needs to be proxied (for CORS issues)
  needsProxy(url) {
    // If URL is relative, no proxy needed
    if (!url.startsWith('http')) return false;

    // Check if same origin
    try {
      const urlObj = new URL(url);
      return urlObj.origin !== window.location.origin;
    } catch {
      return false;
    }
  }
};

// Export utilities for other document types
export const DocumentTypeHandlers = {
  // Handle Word documents
  word(url, options = {}) {
    const device = DeviceDetector.getDeviceType();

    if (device === 'mobile' || device === 'tablet') {
      return PDFViewerStrategies.microsoftViewer(url, options);
    }

    return PDFViewerStrategies.microsoftViewer(url, options);
  },

  // Handle Excel documents
  excel(url, options = {}) {
    return PDFViewerStrategies.microsoftViewer(url, options);
  },

  // Handle PowerPoint documents
  powerpoint(url, options = {}) {
    return PDFViewerStrategies.microsoftViewer(url, options);
  },

  // Handle images
  image(url, options = {}) {
    return {
      type: 'image',
      src: url,
      className: options.className || 'w-full h-auto',
      attributes: {
        loading: 'lazy',
        alt: options.alt || 'Document image'
      }
    };
  }
};

// Utility to detect document type from URL
export function getDocumentType(url) {
  const extension = url.split('.').pop().toLowerCase();

  const typeMap = {
    pdf: 'pdf',
    doc: 'word',
    docx: 'word',
    xls: 'excel',
    xlsx: 'excel',
    ppt: 'powerpoint',
    pptx: 'powerpoint',
    jpg: 'image',
    jpeg: 'image',
    png: 'image',
    gif: 'image',
    webp: 'image'
  };

  return typeMap[extension] || 'unknown';
}