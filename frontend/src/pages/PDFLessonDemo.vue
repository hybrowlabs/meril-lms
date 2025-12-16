<template>
  <div class="pdf-lesson-demo p-8">
    <h1 class="text-2xl font-bold mb-6">PDF Lesson Content Demo</h1>

    <div class="mb-8 p-4 bg-blue-50 rounded-lg">
      <h2 class="text-lg font-semibold mb-2">How PDF Content Works in Lessons</h2>
      <p class="text-sm text-gray-700 mb-2">
        For PDFViewerEnhanced to work in lessons, the lesson content must be in the <code>body</code> field (not the <code>content</code> field) and include the PDF block syntax:
      </p>
      <code class="block p-2 bg-gray-100 rounded text-sm">
        {{ pdfSyntaxExample }}
      </code>
    </div>

    <!-- Demo Section -->
    <div class="border rounded-lg p-6 bg-white">
      <h2 class="text-xl font-semibold mb-4">Live Demo - PDF in Lesson Content</h2>

      <!-- Simulating LessonContent component behavior -->
      <div class="lesson-content-wrapper">
        <LessonContent
          :content="demoContent"
          :youtube="''"
          :quizId="''"
        />
      </div>
    </div>

    <!-- Manual Test Section -->
    <div class="mt-8 border rounded-lg p-6 bg-white">
      <h2 class="text-xl font-semibold mb-4">Direct PDFViewerEnhanced Test</h2>
      <PDFViewerEnhanced
        :src="testPdfUrl"
        :document-name="'Test PDF Document'"
        :download-url="testPdfUrl"
        :min-height="'500px'"
        @load="onPdfLoad"
        @error="onPdfError"
      />
    </div>

    <!-- Instructions -->
    <div class="mt-8 p-4 bg-yellow-50 rounded-lg">
      <h3 class="font-semibold mb-2">📝 To Fix Lesson Content:</h3>
      <ol class="list-decimal list-inside space-y-2 text-sm">
        <li>Ensure the lesson uses the <code>body</code> field instead of <code>content</code> field</li>
        <li>Add PDF content using the syntax: <code>{{ pdfSyntaxExample }}</code></li>
        <li>The LessonContent component will automatically use PDFViewerEnhanced</li>
        <li>If the lesson uses EditorJS (content field), it will show an iframe instead</li>
      </ol>
    </div>

    <!-- Event Log -->
    <div v-if="events.length > 0" class="mt-8 p-4 bg-gray-50 rounded-lg">
      <h3 class="font-semibold mb-2">Event Log:</h3>
      <div class="space-y-1">
        <div v-for="(event, index) in events" :key="index" class="text-sm">
          <span class="text-gray-500">{{ event.time }}:</span>
          <span class="ml-2">{{ event.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LessonContent from '@/components/LessonContent.vue'
import PDFViewerEnhanced from '@/components/PDFViewerEnhanced.vue'

// Demo content that simulates lesson body with PDF
const demoContent = ref(`
This is a lesson with PDF content.

{{ PDF('https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf') }}

You can also have text after the PDF.
`)

// Test PDF URL
const testPdfUrl = ref('https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf')

// PDF syntax example for template
const pdfSyntaxExample = '{{ PDF("/files/document.pdf") }}'

// Event tracking
const events = ref([])

const logEvent = (message) => {
  const time = new Date().toLocaleTimeString()
  events.value.unshift({ time, message })
  if (events.value.length > 10) {
    events.value = events.value.slice(0, 10)
  }
}

const onPdfLoad = () => {
  logEvent('PDF loaded successfully')
}

const onPdfError = (error) => {
  logEvent(`PDF error: ${error}`)
}

// Log initial mount
logEvent('Demo page mounted')
</script>

<style scoped>
.pdf-lesson-demo {
  max-width: 1200px;
  margin: 0 auto;
}

.lesson-content-wrapper {
  border: 2px dashed #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
}

code {
  font-family: 'Courier New', monospace;
}
</style>