<template>
  <div class="test-pdf-viewer p-8">
    <h1 class="text-2xl font-bold mb-6">PDF Viewer Test Page</h1>

    <!-- Test with URL input -->
    <div class="mb-8 p-4 bg-gray-50 rounded-lg">
      <h2 class="text-lg font-semibold mb-3">Test PDF Viewer</h2>
      <div class="flex gap-2 mb-4">
        <input
          v-model="testPdfUrl"
          type="text"
          placeholder="Enter PDF URL"
          class="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          @click="loadPdf"
          class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
        >
          Load PDF
        </button>
      </div>

      <!-- Toggle between viewers -->
      <div class="flex items-center gap-4 mb-4">
        <label class="flex items-center gap-2">
          <input
            v-model="useEnhanced"
            type="checkbox"
            class="rounded"
          />
          <span>Use Enhanced Viewer</span>
        </label>
      </div>
    </div>

    <!-- Sample PDFs -->
    <div class="mb-8 p-4 bg-gray-50 rounded-lg">
      <h2 class="text-lg font-semibold mb-3">Sample PDFs</h2>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="sample in samplePdfs"
          :key="sample.url"
          @click="testPdfUrl = sample.url; loadPdf()"
          class="px-3 py-1 bg-white hover:bg-gray-100 border border-gray-300 rounded text-sm transition-colors"
        >
          {{ sample.name }}
        </button>
      </div>
    </div>

    <!-- Enhanced PDF Viewer -->
    <div v-if="showPdf && useEnhanced" class="mb-8">
      <h2 class="text-lg font-semibold mb-3">Enhanced PDF Viewer</h2>
      <PDFViewerEnhanced
        :src="currentPdfUrl"
        :document-name="pdfName"
        :download-url="currentPdfUrl"
        :show-controls="true"
        :show-footer="true"
        :min-height="'600px'"
        @load="onPdfLoad"
        @error="onPdfError"
        @page-change="onPageChange"
      />
    </div>

    <!-- Original PDF Viewer -->
    <div v-if="showPdf && !useEnhanced" class="mb-8">
      <h2 class="text-lg font-semibold mb-3">Original PDF Viewer</h2>
      <PDFViewer
        :src="currentPdfUrl"
        :title="pdfName"
        :width="'100%'"
        :height="'700px'"
        @load="onPdfLoad"
        @error="onPdfError"
      />
    </div>

    <!-- Event log -->
    <div v-if="eventLog.length > 0" class="p-4 bg-gray-50 rounded-lg">
      <h2 class="text-lg font-semibold mb-3">Event Log</h2>
      <div class="max-h-40 overflow-y-auto">
        <div
          v-for="(event, index) in eventLog"
          :key="index"
          class="text-sm py-1 border-b border-gray-200 last:border-0"
        >
          <span class="text-gray-500">{{ event.time }}:</span>
          <span class="ml-2">{{ event.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PDFViewerEnhanced from '@/components/PDFViewerEnhanced.vue'
import PDFViewer from '@/components/PDFViewer.vue'

// State
const testPdfUrl = ref('')
const currentPdfUrl = ref('')
const pdfName = ref('Test Document')
const showPdf = ref(false)
const useEnhanced = ref(true)
const eventLog = ref([])

// Sample PDFs for testing
const samplePdfs = ref([
  {
    name: 'PDF.js Sample',
    url: 'https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf'
  },
  {
    name: 'W3C Sample',
    url: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    name: 'Adobe Sample',
    url: 'https://www.adobe.com/support/products/enterprise/knowledgecenter/media/c4611_sample_explain.pdf'
  }
])

// Methods
const loadPdf = () => {
  if (testPdfUrl.value) {
    currentPdfUrl.value = testPdfUrl.value
    showPdf.value = true

    // Extract name from URL
    const parts = testPdfUrl.value.split('/')
    pdfName.value = parts[parts.length - 1] || 'Test Document'

    logEvent(`Loading PDF: ${pdfName.value}`)
  }
}

const onPdfLoad = () => {
  logEvent('PDF loaded successfully')
}

const onPdfError = (error) => {
  logEvent(`PDF error: ${error}`)
}

const onPageChange = (page) => {
  logEvent(`Page changed to: ${page}`)
}

const logEvent = (message) => {
  const time = new Date().toLocaleTimeString()
  eventLog.value.unshift({ time, message })

  // Keep only last 20 events
  if (eventLog.value.length > 20) {
    eventLog.value = eventLog.value.slice(0, 20)
  }
}

// Load default PDF on mount
testPdfUrl.value = samplePdfs.value[0].url
</script>

<style scoped>
.test-pdf-viewer {
  max-width: 1200px;
  margin: 0 auto;
}
</style>