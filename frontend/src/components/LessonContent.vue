<template>
	<div v-if="youtube">
		<iframe
			class="youtube-video"
			:src="getYouTubeVideoSource(youtube.split('/').pop())"
			width="100%"
			:height="screenSize.width < 640 ? 200 : 400"
			frameborder="0"
			allowfullscreen
		></iframe>
	</div>
	<div v-for="block in content?.split('\n\n')">
		<div v-if="block.includes('{{ YouTubeVideo')">
			<iframe
				class="youtube-video"
				:src="getYouTubeVideoSource(block)"
				width="100%"
				:height="screenSize.width < 640 ? 200 : 400"
				frameborder="0"
				allowfullscreen
			></iframe>
		</div>
		<div v-else-if="block.includes('{{ Quiz')">
			<Quiz :quiz="getId(block)" />
		</div>
		<div v-else-if="block.includes('{{ Video')">
			<video
				controls
				width="100%"
				controlsList="nodownload"
				oncontextmenu="return false;"
			>
				<source :src="getId(block)" type="video/mp4" />
			</video>
		</div>
		<div v-else-if="block.includes('{{ PDF')">
			<!-- Use Enhanced PDF Viewer if enabled -->
			<PDFViewerEnhanced
				v-if="useEnhancedPDFViewer"
				:src="getId(block)"
				:document-name="extractPDFName(block)"
				:download-url="getId(block)"
				:min-height="'500px'"
				:max-height="screenSize.width < 640 ? '70vh' : '80vh'"
				@load="onPDFLoad"
				@error="onPDFError"
			/>
			<!-- Original PDF Viewer fallback -->
			<div v-else>
				<div v-if="pdfConfig">
					<!-- Loading state -->
					<div v-if="loadingPDF" class="flex justify-center items-center py-8">
						<span class="text-gray-500">Loading document...</span>
					</div>

					<!-- Error state -->
					<div v-else-if="pdfError" class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
						<p class="text-red-600 mb-2">Unable to load document</p>
						<button
							@click="retryPDFLoad(block)"
							class="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-700"
						>
							Retry
						</button>
					</div>

					<!-- PDF Viewer -->
					<div v-else-if="pdfConfig.type === 'iframe'" class="pdf-container relative">
						<iframe
							:src="pdfConfig.src"
							width="100%"
							:height="pdfConfig.height"
							:class="pdfConfig.className"
							v-bind="pdfConfig.attributes"
							@load="onPDFLoad"
							@error="onPDFError"
						></iframe>
					</div>

					<!-- Download fallback -->
					<div v-else-if="pdfConfig.type === 'download'" class="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
						<svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
						</svg>
						<p class="text-gray-600 mb-4">This document cannot be displayed inline on your device.</p>
						<a
							:href="pdfConfig.url"
							:download="pdfConfig.fileName"
							class="inline-block px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
						>
							{{ pdfConfig.buttonText }}
						</a>
					</div>
				</div>
				<div v-else class="py-8 text-center text-gray-500">
					Preparing document viewer...
				</div>
			</div>
		</div>
		<div v-else-if="block.includes('{{ Audio')">
			<audio width="100%" controls controlsList="nodownload">
				<source :src="getId(block)" type="audio/mp3" />
			</audio>
		</div>
		<div v-else-if="block.includes('{{ Embed')">
			<iframe
				width="100%"
				height="400"
				:src="getId(block)"
				frameborder="0"
				allowfullscreen
			>
			</iframe>
		</div>
		<div v-else v-html="markdown.render(block)"></div>
	</div>
	<div v-if="quizId">
		<Quiz :quiz="quizId" />
	</div>
</template>
<script setup>
import Quiz from '@/components/QuizBlock.vue'
import PDFViewerEnhanced from '@/components/PDFViewerEnhanced.vue'
import MarkdownIt from 'markdown-it'
import { useScreenSize } from '@/utils/composables'
import { computed, ref, watchEffect, onMounted, onUnmounted } from 'vue'
import { DocumentViewer, DeviceDetector, getDocumentType } from '@/utils/documentViewer'

const screenSize = useScreenSize()
const pdfConfig = ref(null)
const loadingPDF = ref(false)
const pdfError = ref(false)
const retryCount = ref(0)
const maxRetries = 3

// Feature flag to enable enhanced PDF viewer
// Can be toggled based on user preference or settings
const useEnhancedPDFViewer = ref(true)

// Handle window resize
const handleResize = () => {
	// Recalculate PDF config on resize
	if (pdfConfig.value && pdfConfig.value.type === 'iframe') {
		const height = DocumentViewer.getResponsiveHeight()
		pdfConfig.value.height = height
	}
}

onMounted(() => {
	window.addEventListener('resize', handleResize)
	window.addEventListener('orientationchange', handleResize)
})

onUnmounted(() => {
	window.removeEventListener('resize', handleResize)
	window.removeEventListener('orientationchange', handleResize)
})

const markdown = new MarkdownIt({
	html: true,
	linkify: true,
})

const props = defineProps({
	content: {
		type: String,
		required: true,
	},
	youtube: {
		type: String,
		required: false,
	},
	quizId: {
		type: String,
		required: false,
	},
})

const getYouTubeVideoSource = (block) => {
	if (block.includes('{{')) {
		block = getId(block)
	}
	return `https://www.youtube.com/embed/${block}`
}

// Initialize PDF config when PDF block is encountered
const getPDFSource = (block) => {
	const pdfUrl = getId(block)

	// Get the best viewer configuration for current device
	const config = DocumentViewer.getViewerConfig(pdfUrl, {
		documentType: 'pdf',
		className: 'pdf-viewer-frame'
	})

	// Set the config for template to use
	pdfConfig.value = config

	// Return for backward compatibility
	return config.src || pdfUrl
}

// Handle PDF load success
const onPDFLoad = () => {
	loadingPDF.value = false
	pdfError.value = false
	retryCount.value = 0
}

// Handle PDF load error
const onPDFError = () => {
	loadingPDF.value = false
	pdfError.value = true

	// Try fallback strategies
	if (retryCount.value < maxRetries) {
		retryCount.value++
		retryPDFLoad()
	}
}

// Retry loading PDF with different strategy
const retryPDFLoad = (block = null) => {
	loadingPDF.value = true
	pdfError.value = false

	// Try next fallback strategy
	const strategies = ['native', 'apiEndpoint', 'googleDocs', 'downloadLink']
	const currentStrategy = pdfConfig.value?.strategy || 'native'
	const currentIndex = strategies.indexOf(currentStrategy)
	const nextStrategy = strategies[Math.min(currentIndex + 1, strategies.length - 1)]

	if (block) {
		const pdfUrl = getId(block)
		pdfConfig.value = DocumentViewer.getViewerConfig(pdfUrl, {
			documentType: 'pdf',
			strategy: nextStrategy,
			className: 'pdf-viewer-frame'
		})
	} else if (pdfConfig.value) {
		// Retry with next strategy
		const url = pdfConfig.value.src?.split('?')[0] || ''
		pdfConfig.value = DocumentViewer.getViewerConfig(url, {
			documentType: 'pdf',
			strategy: nextStrategy,
			className: 'pdf-viewer-frame'
		})
	}
}

const getId = (block) => {
	return block.match(/\(["']([^"']+?)["']\)/)[1]
}

// Extract PDF filename from block for display
const extractPDFName = (block) => {
	try {
		const url = getId(block)
		const parts = url.split('/')
		return parts[parts.length - 1] || 'Document'
	} catch {
		return 'Document'
	}
}

// Watch for PDF blocks and initialize config
watchEffect(() => {
	if (props.content && props.content.includes('{{ PDF')) {
		// Pre-initialize PDF config if not already done
		const blocks = props.content.split('\n\n')
		blocks.forEach(block => {
			if (block.includes('{{ PDF') && !pdfConfig.value) {
				getPDFSource(block)
			}
		})
	}
})
</script>

<style scoped>
/* PDF Container Responsive Styles */
.pdf-container {
	position: relative;
	width: 100%;
	overflow: hidden;
	border-radius: 0.5rem;
	box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.pdf-viewer-frame {
	width: 100%;
	border: none;
	display: block;
}

/* Mobile specific styles */
@media (max-width: 640px) {
	.pdf-container {
		/* Remove negative margins that push content off-screen */
		margin: 0;
		width: 100%;
		border-radius: 0.25rem;
		/* Enable smooth scrolling for touch devices */
		-webkit-overflow-scrolling: touch;
		overflow-y: auto;
	}

	.pdf-viewer-frame {
		min-height: 500px;
		height: 70vh;
		max-height: 80vh;
		/* Ensure the iframe is properly contained */
		position: relative;
		display: block;
	}
}

/* Tablet styles */
@media (min-width: 641px) and (max-width: 1024px) {
	.pdf-container {
		margin: 0;
	}

	.pdf-viewer-frame {
		min-height: 500px;
		max-height: 75vh;
	}
}

/* Desktop styles */
@media (min-width: 1025px) {
	.pdf-viewer-frame {
		min-height: 600px;
		max-height: 80vh;
	}
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

/* YouTube video responsive */
.youtube-video {
	aspect-ratio: 16 / 9;
	width: 100%;
	height: auto;
}
</style>
