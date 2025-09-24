<template>
  <div class="pdf-viewer-wrapper">
    <!-- Primary viewer - iframe with selected strategy -->
    <div v-if="viewerType === 'iframe'" class="pdf-iframe-container">
      <embed
        ref="pdfFrame"
        :src="viewerSrc"
        :title="title || 'PDF Document'"
        :width="width"
        :height="height"
        :class="frameClass"
        frameborder="0"
        allowfullscreen
        @load="handleLoad"
        @error="handleError"
        :sandbox="sandboxMode ? 'allow-scripts allow-same-origin' : undefined"
        :loading="lazyLoad ? 'lazy' : 'eager'"
      />
    </div>

    <!-- Canvas viewer for PDF.js (advanced) -->
    <div v-else-if="viewerType === 'canvas'" class="pdf-canvas-container">
      <div class="pdf-controls" v-if="showControls">
        <button @click="previousPage" :disabled="currentPage <= 1">Previous</button>
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage >= totalPages">Next</button>
        <button @click="zoomIn">Zoom In</button>
        <button @click="zoomOut">Zoom Out</button>
      </div>
      <canvas ref="pdfCanvas" :style="{ transform: `scale(${scale})` }"></canvas>
    </div>

    <!-- Object/Embed fallback -->
    <div v-else-if="viewerType === 'object'" class="pdf-object-container">
      <object
        :data="src"
        :type="mimeType"
        :width="width"
        :height="height"
        :class="frameClass"
      >
        <embed
          :src="src"
          :type="mimeType"
          :width="width"
          :height="height"
        />
        <p>
          Your browser does not support embedded PDF files.
          <a :href="src" target="_blank">Download PDF</a>
        </p>
      </object>
    </div>

    <!-- Download fallback -->
    <div v-else class="pdf-download-container">
      <div class="pdf-download-card">
        <svg class="pdf-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <h3>{{ title || 'PDF Document' }}</h3>
        <p>{{ fileSize }} MB</p>
        <a
          :href="src"
          :download="downloadName"
          class="download-button"
        >
          Download PDF
        </a>
        <button
          v-if="canRetry"
          @click="retryWithFallback"
          class="retry-button"
        >
          Try Different Viewer
        </button>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="pdf-loading-overlay">
      <div class="spinner"></div>
      <span>Loading PDF...</span>
    </div>

    <!-- Error message -->
    <div v-if="error && !hideErrors" class="pdf-error-message">
      <p>{{ errorMessage }}</p>
      <button @click="retry" v-if="canRetry">Retry</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { DeviceDetector, DocumentViewer } from '@/utils/documentViewer'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: 'auto'
  },
  strategy: {
    type: String,
    default: 'auto'
  },
  fallbackStrategies: {
    type: Array,
    default: () => ['native', 'apiEndpoint', 'googleDocs', 'object', 'download']
  },
  showControls: {
    type: Boolean,
    default: false
  },
  lazyLoad: {
    type: Boolean,
    default: true
  },
  sandboxMode: {
    type: Boolean,
    default: false
  },
  hideErrors: {
    type: Boolean,
    default: false
  },
  frameClass: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['load', 'error', 'retry'])

// Reactive state
const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')
const currentStrategy = ref(0)
const viewerType = ref('iframe')
const viewerSrc = ref('')
const mimeType = ref('application/pdf')
const fileSize = ref(0)
const downloadName = ref('document.pdf')
const canRetry = computed(() => currentStrategy.value < props.fallbackStrategies.length - 1)

// PDF.js specific state
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1)
const pdfCanvas = ref(null)
const pdfFrame = ref(null)
let pdfDoc = null

// Initialize viewer
const initViewer = () => {
  loading.value = true
  error.value = false

  const strategy = props.strategy === 'auto'
    ? DocumentViewer.selectStrategy(props.src)
    : props.strategy

  applyStrategy(strategy)
}

// Apply viewer strategy
const applyStrategy = (strategy) => {
  // Override strategy for mobile devices
  if (shouldForceGoogleDocs() && strategy !== 'download') {
    strategy = 'googleDocs'
  }

  // Use DocumentViewer's responsive height if height is 'auto'
  const effectiveHeight = props.height === 'auto'
    ? DocumentViewer.getResponsiveHeight()
    : props.height

  const config = DocumentViewer.getViewerConfig(props.src, {
    strategy,
    height: effectiveHeight,
    className: props.frameClass
  })

  if (config.type === 'iframe') {
    viewerType.value = 'iframe'
    viewerSrc.value = config.src
  } else if (config.type === 'download') {
    viewerType.value = 'download'
    downloadName.value = config.fileName || 'document.pdf'
    // Get file size if possible
    fetchFileInfo()
  } else if (strategy === 'object') {
    viewerType.value = 'object'
  } else if (strategy === 'canvas' && window.pdfjsLib) {
    viewerType.value = 'canvas'
    loadPDFJS()
  }
}

// Fetch file information
const fetchFileInfo = async () => {
  try {
    const response = await fetch(`/api/method/lms.lms.api.get_document_info?file_url=${encodeURIComponent(props.src)}`)
    const data = await response.json()
    if (data.message) {
      fileSize.value = data.message.size_mb || 0
    }
  } catch (err) {
    console.error('Error fetching file info:', err)
  }
}

// Load PDF using PDF.js (if available)
const loadPDFJS = async () => {
  if (!window.pdfjsLib || !pdfCanvas.value) return

  try {
    const loadingTask = window.pdfjsLib.getDocument(props.src)
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    renderPage(1)
  } catch (err) {
    console.error('PDF.js error:', err)
    handleError()
  }
}

// Render PDF page (for PDF.js)
const renderPage = async (pageNum) => {
  if (!pdfDoc || !pdfCanvas.value) return

  const page = await pdfDoc.getPage(pageNum)
  const viewport = page.getViewport({ scale: scale.value })

  const canvas = pdfCanvas.value
  const context = canvas.getContext('2d')
  canvas.height = viewport.height
  canvas.width = viewport.width

  const renderContext = {
    canvasContext: context,
    viewport: viewport
  }

  await page.render(renderContext).promise
  currentPage.value = pageNum
  loading.value = false
}

// Navigation methods for PDF.js
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    renderPage(currentPage.value + 1)
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    renderPage(currentPage.value - 1)
  }
}

const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.25, 3)
  renderPage(currentPage.value)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.25, 0.5)
  renderPage(currentPage.value)
}

// Handle successful load
const handleLoad = () => {
  loading.value = false
  error.value = false
  emit('load')
}

// Handle load error
const handleError = () => {
  loading.value = false
  error.value = true
  errorMessage.value = 'Failed to load PDF document'
  emit('error', errorMessage.value)

  // Try next fallback strategy
  if (canRetry.value) {
    setTimeout(() => retryWithFallback(), 1000)
  }
}

// Retry with current strategy
const retry = () => {
  initViewer()
  emit('retry')
}

// Retry with next fallback strategy
const retryWithFallback = () => {
  if (canRetry.value) {
    currentStrategy.value++
    const nextStrategy = props.fallbackStrategies[currentStrategy.value]
    applyStrategy(nextStrategy)
  }
}

// Check if we're on mobile and adjust accordingly
const isMobileDevice = () => {
  return DeviceDetector.isMobile() || window.innerWidth <= 768
}

// Force Google Docs viewer for problematic mobile scenarios
const shouldForceGoogleDocs = () => {
  const isIOS = DeviceDetector.isIOS()
  const isAndroid = DeviceDetector.isAndroid()
  const isWebView = DeviceDetector.isWebView()

  // Force Google Docs for all mobile devices for better compatibility
  return isMobileDevice() || isIOS || isAndroid || isWebView
}

// Handle window resize
const handleResize = () => {
  if (viewerType.value === 'canvas' && pdfDoc) {
    renderPage(currentPage.value)
  }
  // Reapply strategy on resize to recalculate height for responsive viewers
  if (props.height === 'auto' && viewerType.value === 'iframe') {
    const newHeight = DocumentViewer.getResponsiveHeight()
    // Update iframe height if needed
    if (pdfFrame.value) {
      pdfFrame.value.style.height = newHeight
    }
  }
}

// Lifecycle hooks
onMounted(() => {
  initViewer()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (pdfDoc) {
    pdfDoc.destroy()
  }
})

// Watch for source changes
watch(() => props.src, () => {
  initViewer()
})
</script>

<style scoped>
.pdf-viewer-wrapper {
  position: relative;
  width: 100%;
  min-height: 200px;
}

.pdf-iframe-container,
.pdf-object-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pdf-iframe-container iframe,
.pdf-object-container object {
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-canvas-container {
  position: relative;
  width: 100%;
  overflow: auto;
  background: #f5f5f5;
  border-radius: 0.5rem;
  padding: 1rem;
}

.pdf-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem;
  background: white;
  border-radius: 0.25rem;
  margin-bottom: 1rem;
}

.pdf-controls button {
  padding: 0.25rem 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.pdf-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pdf-controls button:hover:not(:disabled) {
  background: #2563eb;
}

.pdf-download-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 2rem;
}

.pdf-download-card {
  text-align: center;
  max-width: 300px;
}

.pdf-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: #6b7280;
}

.download-button,
.retry-button {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  text-decoration: none;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}

.retry-button {
  background: #6b7280;
  margin-left: 0.5rem;
}

.download-button:hover {
  background: #2563eb;
}

.retry-button:hover {
  background: #4b5563;
}

.pdf-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.pdf-error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  padding: 2rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.pdf-error-message button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.pdf-error-message button:hover {
  background: #dc2626;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Responsive styles */
@media (max-width: 640px) {
  .pdf-iframe-container {
    width: 100%;
    overflow: hidden;
    -webkit-overflow-scrolling: touch;
  }

  .pdf-iframe-container iframe {
    min-height: 500px !important;
    height: 70vh !important;
    max-height: 80vh !important;
    width: 100% !important;
    border: none !important;
    display: block !important;
  }

  .pdf-controls {
    flex-wrap: wrap;
    font-size: 0.875rem;
  }

  .pdf-controls button {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
  }

  .pdf-download-card {
    padding: 1rem;
  }
}

/* Fix for iOS Safari */
@supports (-webkit-touch-callout: none) {
  .pdf-iframe-container iframe {
    -webkit-overflow-scrolling: touch;
    position: relative;
    z-index: 1;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .pdf-iframe-container iframe {
    min-height: 500px !important;
    height: 75vh !important;
  }
}

/* Landscape mode on mobile */
@media (max-width: 812px) and (orientation: landscape) {
  .pdf-iframe-container iframe {
    min-height: 400px !important;
    height: 85vh !important;
    max-height: 90vh !important;
  }
}
</style>