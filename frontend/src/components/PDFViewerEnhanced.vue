<template>
  <div class="pdf-viewer-enhanced">
    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mb-4"></div>
        <p class="text-gray-600">Loading PDF document...</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <svg class="w-12 h-12 mx-auto mb-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <h3 class="text-lg font-semibold text-red-800 mb-2">Failed to load PDF</h3>
      <p class="text-red-600 mb-4">{{ errorMessage }}</p>
      <div class="flex gap-3 justify-center">
        <button
          @click="retryLoad"
          class="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-700 transition-colors"
        >
          Retry
        </button>
        <a
          v-if="downloadUrl"
          :href="downloadUrl"
          download
          class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
        >
          Download PDF
        </a>
      </div>
    </div>

    <!-- PDF Content -->
    <div v-else-if="pdf && !loading && !error" class="pdf-content" :class="{ 'fullscreen-mode': isFullscreen }">
      <!-- Fullscreen Exit Button -->
      <button
        v-if="isFullscreen"
        @click="exitFullscreen"
        class="fullscreen-exit-btn"
        title="Exit fullscreen (Esc)"
      >
        <svg class="exit-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Mobile Fullscreen Navigation -->
      <div v-if="isFullscreen" class="mobile-fullscreen-nav">
        <button
          @click="previousPage"
          :disabled="page <= 1"
          class="mobile-nav-btn mobile-nav-prev"
          :class="{ disabled: page <= 1 }"
        >
          <svg class="mobile-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="mobile-page-indicator">
          {{ page }} / {{ pages }}
        </div>

        <button
          @click="nextPage"
          :disabled="page >= pages"
          class="mobile-nav-btn mobile-nav-next"
          :class="{ disabled: page >= pages }"
        >
          <svg class="mobile-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <!-- Navigation Controls -->
      <div class="pdf-controls">
        <div class="pdf-controls-inner">
          <!-- Page Navigation -->
          <div class="control-group page-nav">
            <button
              @click="previousPage"
              :disabled="page <= 1"
              class="control-btn"
              :class="{ disabled: page <= 1 }"
              title="Previous page"
            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            <div class="page-indicator">
              <input
                type="number"
                v-model.number="page"
                @change="goToPage"
                :min="1"
                :max="pages"
                class="page-input"
              />
              <span class="page-separator">/</span>
              <span class="page-total">{{ pages }}</span>
            </div>

            <button
              @click="nextPage"
              :disabled="page >= pages"
              class="control-btn"
              :class="{ disabled: page >= pages }"
              title="Next page"
            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <!-- Divider -->
          <div class="controls-divider"></div>

          <!-- Zoom Controls -->
          <div class="control-group zoom-controls">
            <button
              @click="zoomOut"
              :disabled="scale <= 0.5"
              class="control-btn"
              :class="{ disabled: scale <= 0.5 }"
              title="Zoom out"
            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
              </svg>
            </button>

            <select
              v-model="scale"
              @change="updateScale"
              class="zoom-select"
            >
              <option :value="0.5">50%</option>
              <option :value="0.6">60%</option>
              <option :value="0.7">70%</option>
              <option :value="0.8">80%</option>
              <option :value="0.9">90%</option>
              <option :value="1">100%</option>
              <option :value="1.1">110%</option>
              <option :value="1.2">120%</option>
              <option :value="1.3">130%</option>
              <option :value="1.4">140%</option>
              <option :value="1.5">150%</option>
              <option :value="1.6">160%</option>
              <option :value="1.7">170%</option>
              <option :value="1.8">180%</option>
              <option :value="1.9">190%</option>
              <option :value="2">200%</option>
              <option :value="2.5">250%</option>
              <option :value="3">300%</option>
            </select>

            <button
              @click="zoomIn"
              :disabled="scale >= 3"
              class="control-btn"
              :class="{ disabled: scale >= 3 }"
              title="Zoom in"
            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>

          <!-- Divider -->
          <div class="controls-divider"></div>

          <!-- Additional Controls -->
          <div class="control-group action-controls">
            <button
              @click="toggleFullscreen"
              class="control-btn"
              title="Fullscreen"
            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>

            <a
              v-if="downloadUrl"
              :href="downloadUrl"
              download
              class="control-btn"
              style="display: none !important;"
              title="Download PDF"

            >
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- PDF Viewer -->
      <div
        ref="pdfContainer"
        class="pdf-page-container bg-gray-100"
        :style="containerStyle"
        @wheel="handleWheel"
      >
        <div class="pdf-page-wrapper">
          <VuePDF
            :pdf="pdf"
            :page="page"
            :scale="numericScale"
            @loaded="onPageLoaded"
            @error="onPageError"
            class="pdf-page mx-auto"
            :style="pageStyle"
          />
        </div>
      </div>

      <!-- Page Info Footer -->
      <div v-if="showFooter" class="pdf-footer">
        <div class="footer-content">
          <span class="footer-page-info">Page {{ page }} of {{ pages }}</span>
          <span v-if="documentName" class="footer-divider">•</span>
          <span v-if="documentName" class="footer-document-name">{{ documentName }}</span>
        </div>
      </div>
    </div>

    <!-- Fallback to original viewer if needed -->
    <div v-else-if="useFallback" class="pdf-fallback">
      <PDFViewer
        :src="src"
        :title="documentName"
        :width="width"
        :height="height"
        @load="$emit('load')"
        @error="$emit('error', $event)"
      />
    </div>

    <!-- Debug info (remove in production) -->
    <div v-if="false" class="debug-info p-4 bg-gray-100 text-xs">
      <div>Loading: {{ loading }}</div>
      <div>Error: {{ error }}</div>
      <div>PDF: {{ pdf ? 'loaded' : 'null' }}</div>
      <div>Pages: {{ pages }}</div>
      <div>URL: {{ pdfUrl }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, watchEffect, nextTick } from 'vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import PDFViewer from './PDFViewer.vue'
import { DeviceDetector } from '@/utils/documentViewer'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  initialPage: {
    type: Number,
    default: 1
  },
  showControls: {
    type: Boolean,
    default: true
  },
  showFooter: {
    type: Boolean,
    default: true
  },
  documentName: {
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
  minHeight: {
    type: String,
    default: '500px'
  },
  maxHeight: {
    type: String,
    default: '80vh'
  },
  fallbackOnError: {
    type: Boolean,
    default: true
  },
  downloadUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['load', 'error', 'page-change'])

// PDF state
const page = ref(props.initialPage)
const scale = ref(1)
const numericScale = computed(() => {
  return parseFloat(scale.value) || 1
})
const fitParent = computed(() => false) // We'll handle fitting manually
const resize = ref(false)
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const useFallback = ref(false)
const pdfContainer = ref(null)
const isFullscreen = ref(false)

// Initialize PDF URL
const pdfUrl = computed(() => {
  // Handle relative URLs
  if (props.src.startsWith('/')) {
    return `${window.location.origin}${props.src}`
  }
  return props.src
})

// Use PDF hook with current URL
const { pdf, pages, info } = usePDF(pdfUrl, {
  onError: (err) => {
    console.error('PDF loading error:', err)
    handleError(err)
  }
})


// Watch for PDF loading
watchEffect(() => {
  if (pdf.value) {
    console.log('PDF loaded successfully, pages:', pages.value)
    loading.value = false
    error.value = false
    emit('load')
  }
})

// Container and page styles
const containerStyle = computed(() => {
  const style = {
    width: props.width,
    minHeight: props.minHeight,
    position: 'relative',
    overflow: 'auto'
  }

  if (props.height === 'auto') {
    style.maxHeight = props.maxHeight
  } else {
    style.height = props.height
  }


  // Adjust for fullscreen
  if (isFullscreen.value) {
    style.position = 'fixed'
    style.top = '0'
    style.left = '0'
    style.right = '0'
    style.bottom = '0'
    style.width = '100vw'
    style.height = '100vh'
    style.maxHeight = '100vh'
    style.zIndex = '9999'
    style.backgroundColor = '#f3f4f6'
  }

  return style
})

const pageStyle = computed(() => {
  return {
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
    backgroundColor: 'white',
    transformOrigin: 'top center',
    transition: 'transform 0.2s ease'
  }
})

// Navigation methods
const previousPage = () => {
  if (page.value > 1) {
    page.value--
    emit('page-change', page.value)
  }
}

const nextPage = () => {
  if (page.value < pages.value) {
    page.value++
    emit('page-change', page.value)
  }
}

const goToPage = () => {
  const newPage = parseInt(page.value)
  if (newPage >= 1 && newPage <= pages.value) {
    page.value = newPage
    emit('page-change', page.value)
  } else {
    // Reset to valid range
    if (newPage < 1) page.value = 1
    if (newPage > pages.value) page.value = pages.value
  }
}

// Zoom methods
const zoomIn = () => {
  if (typeof scale.value === 'number' && scale.value < 3) {
    scale.value = Math.round((scale.value + 0.1) * 10) / 10
    scale.value = Math.min(scale.value, 3)
  } else {
    scale.value = 1.1
  }
  resize.value = !resize.value
}

const zoomOut = () => {
  if (typeof scale.value === 'number' && scale.value > 0.5) {
    scale.value = Math.round((scale.value - 0.1) * 10) / 10
    scale.value = Math.max(scale.value, 0.5)
  } else {
    scale.value = 0.9
  }
  resize.value = !resize.value
}

const updateScale = () => {
  resize.value = !resize.value
}

// Fullscreen
const toggleFullscreen = async () => {
  if (!isFullscreen.value) {
    const elem = document.querySelector('.pdf-content')
    if (elem?.requestFullscreen) {
      await elem.requestFullscreen()
    } else if (elem?.webkitRequestFullscreen) {
      await elem.webkitRequestFullscreen()
    } else if (elem?.mozRequestFullScreen) {
      await elem.mozRequestFullScreen()
    } else if (elem?.msRequestFullscreen) {
      await elem.msRequestFullscreen()
    }
    isFullscreen.value = true
    // Center the page after entering fullscreen
    nextTick(() => {
      centerPageInView()
    })
  } else {
    exitFullscreen()
  }
}

// Center the PDF page in the container
const centerPageInView = () => {
  const container = pdfContainer.value
  if (!container) return

  // Wait for layout to settle
  setTimeout(() => {
    const scrollWidth = container.scrollWidth
    const scrollHeight = container.scrollHeight
    const clientWidth = container.clientWidth
    const clientHeight = container.clientHeight

    // Center horizontally
    if (scrollWidth > clientWidth) {
      container.scrollLeft = (scrollWidth - clientWidth) / 2
    }

    // Center vertically
    if (scrollHeight > clientHeight) {
      container.scrollTop = (scrollHeight - clientHeight) / 2
    }
  }, 100)
}

const exitFullscreen = async () => {
  if (document.exitFullscreen) {
    await document.exitFullscreen()
  } else if (document.webkitExitFullscreen) {
    await document.webkitExitFullscreen()
  } else if (document.mozCancelFullScreen) {
    await document.mozCancelFullScreen()
  } else if (document.msExitFullscreen) {
    await document.msExitFullscreen()
  }
  isFullscreen.value = false
}

// Mouse wheel zoom with Ctrl
const handleWheel = (event) => {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()
    if (event.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  }
}

// Keyboard navigation
const handleKeydown = (event) => {
  // Only handle if this component is visible/focused
  if (!pdf.value) return

  switch (event.key) {
    case 'ArrowLeft':
      if (!event.target.matches('input')) {
        event.preventDefault()
        previousPage()
      }
      break
    case 'ArrowRight':
      if (!event.target.matches('input')) {
        event.preventDefault()
        nextPage()
      }
      break
    case 'Home':
      if (!event.target.matches('input')) {
        event.preventDefault()
        page.value = 1
        emit('page-change', page.value)
      }
      break
    case 'End':
      if (!event.target.matches('input')) {
        event.preventDefault()
        page.value = pages.value
        emit('page-change', page.value)
      }
      break
    case '+':
    case '=':
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault()
        zoomIn()
      }
      break
    case '-':
    case '_':
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault()
        zoomOut()
      }
      break
    case 'f':
    case 'F':
      if (!event.target.matches('input')) {
        event.preventDefault()
        toggleFullscreen()
      }
      break
    case 'Escape':
      if (isFullscreen.value) {
        exitFullscreen()
      }
      break
  }
}

// Error handling
const handleError = (err) => {
  loading.value = false
  error.value = true
  errorMessage.value = err?.message || 'Failed to load PDF document'
  emit('error', errorMessage.value)

  // Try fallback viewer if enabled
  if (props.fallbackOnError && !useFallback.value) {
    setTimeout(() => {
      useFallback.value = true
    }, 1000)
  }
}

const retryLoad = () => {
  loading.value = true
  error.value = false
  useFallback.value = false
  // Force re-initialization by changing the URL slightly
  window.location.reload()
}

// Page events
const onPageLoaded = () => {
  // Page loaded successfully
}

const onPageError = (err) => {
  console.error('Page rendering error:', err)
}

// Responsive handling
const handleResize = () => {
  resize.value = !resize.value
  // Re-center page in fullscreen when resizing/rotating
  if (isFullscreen.value) {
    centerPageInView()
  }
}

// Handle orientation change
const handleOrientationChange = () => {
  if (isFullscreen.value) {
    // Small delay to allow layout to update after orientation change
    setTimeout(() => {
      centerPageInView()
    }, 200)
  }
}

// Set initial scale based on device
const setInitialScale = () => {
  const isMobile = DeviceDetector.isMobile()
  const isTablet = DeviceDetector.isTablet()

  if (isMobile) {
    scale.value = 0.75  // Use 75% for mobile instead of fit-width
  } else if (isTablet) {
    scale.value = 1
  } else {
    // Desktop
    scale.value = 1.25
  }
}

// Lifecycle
onMounted(() => {
  console.log('PDFViewerEnhanced mounted with src:', props.src)
  setInitialScale()
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', handleResize)

  // Listen for fullscreen changes
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('mozfullscreenchange', handleFullscreenChange)
  document.addEventListener('MSFullscreenChange', handleFullscreenChange)

  // Listen for orientation changes
  window.addEventListener('orientationchange', handleOrientationChange)
  screen.orientation?.addEventListener('change', handleOrientationChange)
})

const handleFullscreenChange = () => {
  const fullscreenElement = document.fullscreenElement ||
                           document.webkitFullscreenElement ||
                           document.mozFullScreenElement ||
                           document.msFullscreenElement

  isFullscreen.value = !!fullscreenElement

  // Center page when entering fullscreen
  if (isFullscreen.value) {
    nextTick(() => {
      centerPageInView()
    })
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
  document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
  window.removeEventListener('orientationchange', handleOrientationChange)
  screen.orientation?.removeEventListener('change', handleOrientationChange)
})

// Watch for URL changes
watch(() => props.src, () => {
  console.log('PDF URL changed:', props.src)
  page.value = 1
  loading.value = true
  error.value = false
  useFallback.value = false
})
</script>

<style scoped>
.pdf-viewer-enhanced {
  position: relative;
  width: 100%;
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  contain: layout style;
}

.pdf-content {
  position: relative;
}

.pdf-content.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99999;
  background: #1a1a1a;
  border-radius: 0;
}

.fullscreen-exit-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  cursor: pointer;
  z-index: 100000;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.fullscreen-exit-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  border-color: rgba(255, 255, 255, 0.6);
  transform: scale(1.1);
}

.fullscreen-exit-btn .exit-icon {
  width: 24px;
  height: 24px;
  color: white;
}

.fullscreen-mode .pdf-controls {
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.fullscreen-mode .control-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}

.fullscreen-mode .control-btn:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.fullscreen-mode .page-indicator {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.fullscreen-mode .page-input {
  color: white;
}

.fullscreen-mode .page-separator,
.fullscreen-mode .page-total {
  color: rgba(255, 255, 255, 0.8);
}

.fullscreen-mode .zoom-select {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}

.fullscreen-mode .controls-divider {
  background: rgba(255, 255, 255, 0.2);
}

.fullscreen-mode .pdf-page-container {
  background: #1a1a1a;
}

.fullscreen-mode .pdf-footer {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
}

.fullscreen-mode .footer-page-info,
.fullscreen-mode .footer-document-name {
  color: rgba(255, 255, 255, 0.9);
}

.fullscreen-mode .footer-divider {
  color: rgba(255, 255, 255, 0.4);
}

.pdf-controls {
  position: sticky;
  top: 0;
  z-index: 10;
  background: linear-gradient(to bottom, #ffffff, #fafbfc);
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

.pdf-controls-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.controls-divider {
  width: 1px;
  height: 24px;
  background: #e5e7eb;
  margin: 0 0.5rem;
}

.control-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 8px;
  background: white;
  color: #4b5563;
  transition: all 0.2s ease;
  cursor: pointer;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  text-decoration: none;
}

.control-btn:hover:not(.disabled) {
  background: #f9fafb;
  border-color: #e5e7eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.1);
}

.control-btn:active:not(.disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.control-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.control-btn .icon {
  width: 18px;
  height: 18px;
}

.page-indicator {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.page-input {
  width: 3rem;
  padding: 0.125rem 0.25rem;
  text-align: center;
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  background: transparent;
  border: none;
  outline: none;
}

.page-input:focus {
  background: #f9fafb;
  border-radius: 4px;
}

.page-separator {
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 400;
}

.page-total {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

.zoom-select {
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  outline: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}

.zoom-select:hover {
  border-color: #d1d5db;
  background-color: #f9fafb;
}

.zoom-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.pdf-page-container {
  position: relative;
  overflow: auto;
  transition: all 0.3s ease;
  contain: size layout;
}

.pdf-page-wrapper {
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  height: 100%;
}

.pdf-page {
  transition: transform 0.2s ease;
  max-width: 100%;
  height: auto;
}

.pdf-footer {
  position: sticky;
  bottom: 0;
  z-index: 10;
  background: linear-gradient(to top, #ffffff, #fafbfc);
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -1px 3px 0 rgba(0, 0, 0, 0.05);
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  font-size: 0.8125rem;
}

.footer-page-info {
  font-weight: 500;
  color: #4b5563;
}

.footer-divider {
  color: #d1d5db;
}

.footer-document-name {
  color: #6b7280;
}

/* Loading spinner animation */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .pdf-controls-inner {
    padding: 0.5rem;
    gap: 0.5rem;
  }

  .control-btn {
    width: 32px;
    height: 32px;
  }

  .control-btn .icon {
    width: 16px;
    height: 16px;
  }

  .controls-divider {
    display: none;
  }

  .page-input {
    width: 2.5rem;
  }

  .zoom-select {
    padding: 0.375rem 2rem 0.375rem 0.5rem;
    font-size: 0.8125rem;
  }

  .pdf-page-wrapper {
    padding: 0.5rem;
  }

  .footer-content {
    font-size: 0.75rem;
    padding: 0.5rem;
  }
}

/* Tablet responsive */
@media (min-width: 641px) and (max-width: 1024px) {
  .pdf-page-container {
    padding: 0.75rem;
  }
}

/* Print styles */
@media print {
  .pdf-controls,
  .pdf-footer {
    display: none;
  }

  .pdf-page-container {
    padding: 0;
    overflow: visible;
    height: auto !important;
    max-height: none !important;
  }
}

/* Fullscreen styles */
.pdf-page-container:fullscreen {
  background: #f3f4f6;
  padding: 2rem;
}

/* Custom scrollbar */
.pdf-page-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.pdf-page-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.pdf-page-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.pdf-page-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Fullscreen Navigation */
.mobile-fullscreen-nav {
  display: none;
}

.fullscreen-mode .mobile-fullscreen-nav {
  display: flex;
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100001;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.85);
  border-radius: 50px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.mobile-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-nav-btn:hover:not(.disabled),
.mobile-nav-btn:active:not(.disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.mobile-nav-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.mobile-nav-icon {
  width: 24px;
  height: 24px;
  color: white;
}

.mobile-page-indicator {
  font-size: 14px;
  font-weight: 600;
  color: white;
  min-width: 60px;
  text-align: center;
}

/* Mobile Landscape Mode */
@media (max-width: 896px) and (orientation: landscape) {
  .fullscreen-mode {
    background: #f3f4f6;
  }

  .fullscreen-mode .pdf-page-container {
    min-height: auto !important;
    max-height: 100vh !important;
    height: 100vh !important;
    background: #f3f4f6 !important;
  }

  .fullscreen-mode .pdf-page-wrapper {
    min-height: auto;
    padding: 0.5rem;
    padding-bottom: 2rem;
  }

  .fullscreen-mode .pdf-controls {
    display: none;
  }

  .fullscreen-mode .pdf-footer {
    display: none;
  }

  .fullscreen-mode .pdf-controls-compact {
    padding: 0.25rem 0.5rem;
  }

  .fullscreen-mode .pdf-controls-inner {
    gap: 0.5rem;
  }

  .fullscreen-mode .control-btn {
    width: 28px;
    height: 28px;
  }

  .fullscreen-mode .control-btn .icon {
    width: 14px;
    height: 14px;
  }

  .fullscreen-mode .page-indicator {
    padding: 0.25rem 0.5rem;
  }

  .fullscreen-mode .zoom-select {
    padding: 0.25rem 1.5rem 0.25rem 0.5rem;
    font-size: 0.75rem;
  }

  /* Move navigation to the side in landscape */
  .fullscreen-mode .mobile-fullscreen-nav {
    flex-direction: column;
    bottom: auto;
    top: 50%;
    left: auto;
    right: 20px;
    transform: translateY(-50%);
    padding: 12px 8px;
    border-radius: 30px;
  }

  .fullscreen-mode .mobile-nav-btn {
    width: 40px;
    height: 40px;
  }

  .fullscreen-mode .mobile-nav-icon {
    width: 20px;
    height: 20px;
  }

  .fullscreen-mode .mobile-page-indicator {
    font-size: 12px;
    min-width: auto;
    writing-mode: vertical-rl;
    text-orientation: mixed;
    transform: rotate(180deg);
  }

  /* Adjust exit button for landscape */
  .fullscreen-exit-btn {
    top: 10px;
    right: 10px;
    width: 36px;
    height: 36px;
  }

  .fullscreen-exit-btn .exit-icon {
    width: 18px;
    height: 18px;
  }
}
</style>