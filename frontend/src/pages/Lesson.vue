<template>
	<div v-if="lesson.data" class="">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
			<div class="flex items-center space-x-2">
				<Tooltip v-if="canGoZen()" :text="__('Zen Mode')">
					<Button @click="goFullScreen()">
						<template #icon>
							<Focus class="w-4 h-4 stroke-2" />
						</template>
					</Button>
				</Tooltip>
				<Button v-if="canSeeStats()" @click="showVideoStats()">
					<template #icon>
						<TrendingUp class="size-4 stroke-1.5" />
					</template>
				</Button>
				<CertificationLinks :courseName="courseName" />
				<Button v-if="lesson.data.prev" @click="switchLesson('prev')">
					<template #prefix>
						<ChevronLeft class="w-4 h-4 stroke-1" />
					</template>
					<span>
						{{ __('Previous') }}
					</span>
				</Button>

				<router-link
					v-if="allowEdit()"
					:to="{
						name: 'LessonForm',
						params: {
							courseName: courseName,
							chapterNumber: props.chapterNumber,
							lessonNumber: props.lessonNumber,
						},
					}"
				>
					<Button>
						{{ __('Edit') }}
					</Button>
				</router-link>

				<Button v-if="lesson.data.next" @click="switchLesson('next')">
					<template #suffix>
						<ChevronRight class="w-4 h-4 stroke-1" />
					</template>
					<span>
						{{ __('Next') }}
					</span>
				</Button>

				<router-link
					v-else
					:to="{
						name: 'CourseDetail',
						params: { courseName: courseName },
					}"
				>
					<Button>
						{{ __('Back to Course') }}
					</Button>
				</router-link>
			</div>
		</header>
		<div class="grid md:grid-cols-[70%,30%] h-screen">
			<div v-if="lesson.data.no_preview" class="border-r">
				<div class="shadow rounded-md w-3/4 mt-10 mx-auto text-center p-4">
					<div class="flex items-center justify-center mt-4 space-x-2">
						<LockKeyholeIcon class="size-4 stroke-2 text-ink-gray-5" />
						<div class="text-lg font-semibold text-ink-gray-7">
							{{ __('This lesson is locked') }}
						</div>
					</div>
					<div class="mt-1 mb-4 text-ink-gray-7">
						{{
							__(
								'This lesson is not available for preview. Please enroll in the course to access it.'
							)
						}}
					</div>
					<Button
						v-if="user.data && !lesson.data.disable_self_learning"
						@click="enrollStudent()"
						variant="solid"
					>
						{{ __('Start Learning') }}
					</Button>
					<Badge
						theme="blue"
						size="lg"
						v-else-if="lesson.data.disable_self_learning"
						class="mt-2"
					>
						{{ __('Contact the Administrator to enroll for this course.') }}
					</Badge>
					<Button v-else @click="redirectToLogin()">
						<template #prefix>
							<LogIn class="w-4 h-4 stroke-1" />
						</template>
						{{ __('Login') }}
					</Button>
				</div>
			</div>
			<!-- Access Restricted Section for Completed Lessons -->
			<div v-else-if="lesson.data.access_restricted" class="border-r">
				<div class="shadow rounded-md w-3/4 mt-10 mx-auto text-center p-4">
					<div class="flex items-center justify-center mt-4 space-x-2">
						<LockKeyholeIcon class="size-4 stroke-2 text-ink-gray-5" />
						<div class="text-lg font-semibold text-ink-gray-7">
							{{ __('Lesson Access Restricted') }}
						</div>
					</div>
					<div class="mt-1 mb-4 text-ink-gray-7">
						{{ lesson.data.restriction_message || __('This lesson was completed and is currently restricted.') }}
					</div>
					<div v-if="lesson.data.lesson_completed" class="mt-2 mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
						<div class="flex items-center justify-center text-green-700">
							<CheckCircle class="w-4 h-4 mr-2" />
							<span class="text-sm font-medium">{{ __('Lesson Completed') }}</span>
						</div>
						<p class="text-xs text-green-600 mt-1">
							{{ __('You have successfully completed this lesson.') }}
						</p>
					</div>
					
					<Button
						@click="goBackToCourse()"
						variant="subtle"
					>
						{{ __('Back to Course') }}
					</Button>
				</div>
			</div>
			<div
				v-else
				ref="lessonContainer"
				class="bg-surface-white"
				:class="{
					'overflow-y-auto': zenModeEnabled,
				}"
			>
				<div
					class="border-r pt-5 pb-10 h-full"
					:class="{
						'w-full md:w-3/5 mx-auto border-none !pt-10': zenModeEnabled,
					}"
				>
					<div class="px-5">
						<div
							class="flex flex-col space-y-3 md:space-y-0 md:flex-row md:items-center justify-between"
						>
							<div class="flex flex-col">
								<div class="text-3xl font-semibold text-ink-gray-9">
									{{ lesson.data.title }}
								</div>

								<div
									v-if="zenModeEnabled"
									class="relative flex items-center space-x-2 text-sm mt-1 text-ink-gray-7 group w-fit mt-2"
								>
									<span>
										{{ lesson.data.chapter_title }} -
										{{ lesson.data.course_title }}
									</span>
									<Info class="size-3" />
									<div
										class="hidden group-hover:block rounded bg-gray-900 px-2 py-1 text-xs text-white shadow-xl absolute left-0 top-full mt-2"
									>
										{{ Math.ceil(lesson.data.membership.progress) }}%
										{{ __('completed') }}
									</div>
								</div>
							</div>

							<div
								v-if="zenModeEnabled"
								class="flex items-center space-x-2 mt-2 md:mt-0"
							>
								<Button @click="showDiscussionsInZenMode()">
									<template #icon>
										<MessageCircleQuestion class="w-4 h-4 stroke-1.5" />
									</template>
								</Button>
								<Button v-if="lesson.data.prev" @click="switchLesson('prev')">
									<template #prefix>
										<ChevronLeft class="w-4 h-4 stroke-1" />
									</template>
									<span>
										{{ __('Previous') }}
									</span>
								</Button>

								<router-link
									v-if="allowEdit()"
									:to="{
										name: 'LessonForm',
										params: {
											courseName: courseName,
											chapterNumber: props.chapterNumber,
											lessonNumber: props.lessonNumber,
										},
									}"
								>
									<Button>
										{{ __('Edit') }}
									</Button>
								</router-link>

								<Button v-if="lesson.data.next" @click="switchLesson('next')">
									<template #suffix>
										<ChevronRight class="w-4 h-4 stroke-1" />
									</template>
									<span>
										{{ __('Next') }}
									</span>
								</Button>

								<router-link
									v-else
									:to="{
										name: 'CourseDetail',
										params: { courseName: courseName },
									}"
								>
									<Button>
										{{ __('Back to Course') }}
									</Button>
								</router-link>
							</div>
						</div>

						<div v-if="!zenModeEnabled" class="flex items-center mt-4 md:mt-2">
							<span
								class="h-6 mr-1"
								:class="{
									'avatar-group overlap': lesson.data.instructors?.length > 1,
								}"
							>
								<UserAvatar
									v-for="instructor in lesson.data.instructors"
									:user="instructor"
								/>
							</span>
							<CourseInstructors
								v-if="lesson.data?.instructors"
								:instructors="lesson.data.instructors"
							/>
						</div>

						<div
							v-if="
								lesson.data.instructor_content &&
								JSON.parse(lesson.data.instructor_content)?.blocks?.length >
									1 &&
								allowInstructorContent()
							"
							class="bg-surface-gray-2 p-3 rounded-md mt-6"
						>
							<div class="text-ink-gray-5 font-medium">
								{{ __('Instructor Notes') }}
							</div>
							<div
								id="instructor-content"
								class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal"
							></div>
						</div>
						<div
							v-else-if="lesson.data.instructor_notes"
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<LessonContent :content="lesson.data.instructor_notes" />
						</div>
						<div
							v-if="lesson.data.content"
							@mouseup="toggleInlineMenu"
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<div id="editor"></div>
						</div>
						<div
							v-else
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<LessonContent
								v-if="lesson.data?.body"
								:content="lesson.data.body"
								:youtube="lesson.data.youtube"
								:quizId="lesson.data.quiz_id"
							/>
						</div>
					</div>
					<div
						v-if="lesson.data"
						class="mt-10 pb-20 pt-5 border-t px-5"
						ref="discussionsContainer"
					>
						<TabButtons
							v-if="tabs.length > 1"
							:buttons="tabs"
							v-model="currentTab"
							class="w-fit mb-10"
						/>
						<Notes
							v-if="currentTab === 'Notes'"
							:lesson="lesson.data?.name"
							v-model:notes="notes"
							@updateNotes="updateNotes"
						/>
						<Discussions
							v-else-if="allowDiscussions && currentTab === 'Community'"
							:title="'Questions'"
							:doctype="'Course Lesson'"
							:docname="lesson.data.name"
							:key="lesson.data.name"
							:emptyStateText="
								__('Ask a question to get help from the community.')
							"
						/>
				</div>
			</div>
			<div class="sticky top-10">
				<div class="bg-surface-menu-bar py-5 px-2 border-b">
					<div class="flex w-full">
						<div class="text-lg font-semibold text-ink-gray-9">
							{{ lesson.data.course_title }}
						</div>
						<div v-show="lesson?.data?.duration && lesson?.data?.duration>=0" class="ml-auto flex items-center gap-2 text-ink-gray-7">
							<span class="flex items-center gap-1">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="inline w-5 h-5"
									:class="{
										'text-ink-gray-5': lesson.data.progress === null,
										'text-green-600': lesson.data.progress !== null
									}"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<circle cx="12" cy="12" r="10" stroke-width="2" />
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6l4 2" />
								</svg>
								<span class="font-medium" v-show="(videoFiles?.length==0)">
									{{
										!!lesson.data.progress ?
											 (lesson.data.duration + 's')
											: ((timer >= lesson.data.duration
												? lesson.data.duration
												: timer) + 's')
									}}
									/ {{ lesson.data.duration }}s
								</span>
							</span>
						</div>
						</div>
					<div
						v-if="user && lesson.data.membership"
						class="text-sm mt-4 mb-2 text-ink-gray-5"
					>
						{{ Math.ceil(lessonProgress) }}% {{ __('completed') }}
					</div>

					<ProgressBar
						v-if="user && lesson.data.membership"
						:progress="lessonProgress"
					/>
				</div>
				<CourseOutline
					:courseName="courseName"
					:key="chapterNumber"
					:getProgress="lesson.data.membership ? true : false"
					:lessonProgress="lessonProgress"
				/>
			</div>
		</div>
	</div>
	<InlineLessonMenu
		v-if="lesson.data"
		v-model="showInlineMenu"
		:lesson="lesson.data?.name"
		v-model:notes="notes"
		@updateNotes="updateNotes"
	/>
	<VideoStatistics
		v-model="showStatsDialog"
		:lessonName="lesson.data?.name"
		:lessonTitle="lesson.data?.title"
	/>
</template>
<script setup>
import {
	Badge,
	Breadcrumbs,
	Button,
	call,
	createListResource,
	createResource,
	TabButtons,
	Tooltip,
	usePageMeta,
} from 'frappe-ui'
import {
	computed,
	watch,
	inject,
	ref,
	onMounted,
	onBeforeUnmount,
	nextTick,
} from 'vue'
import CourseOutline from '@/components/CourseOutline.vue'
import { useRouter, useRoute } from 'vue-router'
import {
	ChevronLeft,
	ChevronRight,
	LockKeyholeIcon,
	LogIn,
	Focus,
	Info,
	MessageCircleQuestion,
	TrendingUp,
	CheckCircle,
} from 'lucide-vue-next'
import { getEditorTools, enablePlyr, highlightText } from '@/utils'
import { sessionStore } from '@/stores/session'
import { useSidebar } from '@/stores/sidebar'
import EditorJS from '@editorjs/editorjs'
import LessonContent from '@/components/LessonContent.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Discussions from '@/components/Discussions.vue'
import CertificationLinks from '@/components/CertificationLinks.vue'
import VideoStatistics from '@/components/Modals/VideoStatistics.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Notes from '@/components/Notes/Notes.vue'
import InlineLessonMenu from '@/components/Notes/InlineLessonMenu.vue'
import PDFViewerEnhanced from '@/components/PDFViewerEnhanced.vue'
import { setCourseCompletion } from "../stores/course_completion.js"
import { createApp } from 'vue'
import translationPlugin from '@/translation'
import { createDialog } from '@/utils/dialogs'

const user = inject('$user')
const socket = inject('$socket')
const router = useRouter()
const route = useRoute()
const allowDiscussions = ref(false)
const editor = ref(null)
const lessonProgress = ref(0)
const lessonContainer = ref(null)
const zenModeEnabled = ref(false)
const showStatsDialog = ref(false)
const hasQuiz = ref(false)
const discussionsContainer = ref(null)
const timer = ref(0)
const { brand } = sessionStore()
const sidebarStore = useSidebar()
const plyrSources = ref([])
const showInlineMenu = ref(false)
const currentTab = ref('Notes')
const instructorEditor = ref(null)
let timerInterval
let timerFrame
let timerPaused = false
let savedTimerKey = null
let timerSaveInterval = null
let currentEnrollmentVersion = ref(null)
let isReEnrollment = ref(false)
let enrollmentId = ref(null)

// --- Video completion logic ---
const videoFiles = ref([]) // List of video URLs in the lesson
const completedVideos = ref(new Set())
let markProgressTimeout = null
function handleVideoCompleted(e) {
  onVideoCompleted(e.detail.file)
}

function onVideoCompleted(fileUrl) {
  const before = completedVideos.value.size
  completedVideos.value.add(fileUrl)
  if (
    completedVideos.value.size === videoFiles.value.length &&
    before !== completedVideos.value.size
  ) {
    if (markProgressTimeout) clearTimeout(markProgressTimeout)
    markProgressTimeout = setTimeout(() => {
      markProgress()
    }, 200)
  }
}

const tabs = ref([
	{
		label: __('Notes'),
		value: 'Notes',
	},
])

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	chapterNumber: {
		type: String,
		required: true,
	},
	lessonNumber: {
		type: String,
		required: true,
	},
})

onMounted(() => {
	sidebarStore.isSidebarCollapsed = true
	// Timer will be started when lesson data loads
	document.addEventListener('fullscreenchange', attachFullscreenEvent)
	document.addEventListener('visibilitychange', handleVisibilityChange)
	window.addEventListener('beforeunload', handleBeforeUnload)
	socket.on('update_lesson_progress', (data) => {
		if (data.course === props.courseName) {
			lessonProgress.value = data.progress
		}
	})
	window.addEventListener('video-completed', handleVideoCompleted)
	window.addEventListener("message", handleMessage )

	// Check enrollment status when component mounts
	if (user.data) {
		checkEnrollmentStatus()
	}
})

const handleMessage = (data) =>{
	if(data.data === "quize completed")
		markProgress();
}
const attachFullscreenEvent = () => {
	if (document.fullscreenElement) {
		zenModeEnabled.value = true
		allowDiscussions.value = false
	} else {
		zenModeEnabled.value = false
		if (!hasQuiz.value) {
			allowDiscussions.value = true
		}
	}
}

onBeforeUnmount(() => {
	document.removeEventListener('fullscreenchange', attachFullscreenEvent)
	sidebarStore.isSidebarCollapsed = false
	trackVideoWatchDuration()
	window.removeEventListener('video-completed', handleVideoCompleted)
	if (timerFrame) cancelAnimationFrame(timerFrame)
	if (timerSaveInterval) clearInterval(timerSaveInterval)
	saveTimerToBackend() // Final save before unmounting
})

const lesson = createResource({
	url: 'lms.lms.utils.get_lesson',
	makeParams(values) {
		return {
			course: props.courseName,
			chapter: values ? values.chapter : props.chapterNumber,
			lesson: values ? values.lesson : props.lessonNumber,
		}
	},
	auto: true,
})


const setupLesson = (data) => {
	if (Object.keys(data).length === 0) {
		router.push({
			name: 'CourseDetail',
			params: { courseName: props.courseName },
		})
		return
	}
	if (data.is_scorm_package) {
		router.push({
			name: 'SCORMChapter',
			params: {
				courseName: props.courseName,
				chapterName: data.chapter_name,
			},
		})
	}
	lessonProgress.value = data.membership?.progress
	let contentRendered = false
	if (data.content) {
		try {
			editor.value = renderEditor('editor', data.content)
			contentRendered = true
		} catch (e) {
			console.error('Failed to render lesson content:', e)
			contentRendered = false
		}
	}
	if (!contentRendered && data.body) {
		// Remove any previous EditorJS instance
		if (editor.value && editor.value.destroy) editor.value.destroy()
		// Render legacy body as HTML
		const editorDiv = document.getElementById('editor')
		if (editorDiv) {
			editorDiv.innerHTML = ''
			const bodyDiv = document.createElement('div')
			bodyDiv.className = 'lesson-content prose'
			bodyDiv.innerHTML = data.body
			editorDiv.appendChild(bodyDiv)
			// Process PDF embeds and fix videos for legacy content
			nextTick(() => {
				processPDFEmbeds()
				fixVideoRendering()
				enablePlyr()
			})
		}
	}
	if (!contentRendered && !data.body) {
		// Show a fallback message if no content
		const editorDiv = document.getElementById('editor')
		if (editorDiv) {
			editorDiv.innerHTML = '<div class="text-ink-gray-5 text-center py-10">No content available for this lesson.</div>'
		}
	}
	editor.value?.isReady.then(() => {
		checkIfDiscussionsAllowed()
		// Process PDF embeds after EditorJS is ready
		nextTick(() => {
			processPDFEmbeds()
			// Fix incorrectly rendered videos (images that should be videos)
			fixVideoRendering()
			// Enable Plyr for embedded videos
			enablePlyr()
		})
	})
	checkQuiz()
}

const checkQuiz = () => {
	if (!editor.value && lesson.body) {
		const quizRegex = /\{\{ Quiz\(".*"\) \}\}/
		hasQuiz.value = quizRegex.test(lesson.body)
		if (!hasQuiz.value && !zenModeEnabled) {
			allowDiscussions.value = true
		} else {
			allowDiscussions.value = false
		}
	}
}

const renderEditor = (holder, content) => {
	if (document.getElementById(holder))
		document.getElementById(holder).innerHTML = ''
	return new EditorJS({
		holder: holder,
		tools: getEditorTools(),
		data: JSON.parse(content),
		readOnly: true,
		defaultBlock: 'embed',
	})
}

// Fix incorrectly rendered videos (images that should be videos)
const fixVideoRendering = () => {
	const editorDiv = document.getElementById('editor')
	if (!editorDiv) return

	// Video file extensions
	const videoExtensions = ['mp4', 'mov', 'avi', 'mkv', 'webm']
	
	// Find all images in the editor content
	const images = editorDiv.querySelectorAll('img')
	
	images.forEach((img) => {
		const src = img.src || img.getAttribute('src') || ''
		if (!src) return
		
		// Extract extension from URL
		const getExtension = (url) => {
			try {
				const urlWithoutParams = url.split('?')[0]
				const filename = urlWithoutParams.split('/').pop()
				if (filename && filename.includes('.')) {
					return filename.split('.').pop().toLowerCase()
				}
			} catch (e) {
				// Ignore errors
			}
			return null
		}
		
		const extension = getExtension(src)
		
		// Check if this image is actually a video
		if (extension && videoExtensions.includes(extension)) {
			// Find the parent wrapper (usually a div or the upload block wrapper)
			let wrapper = img.parentElement
			
			// Look for the upload block wrapper (usually has specific classes)
			while (wrapper && wrapper !== editorDiv) {
				if (wrapper.classList.contains('ce-block') || 
				    wrapper.classList.contains('ce-block__content') ||
				    wrapper.classList.contains('cdx-block')) {
					break
				}
				wrapper = wrapper.parentElement
			}
			
			// If we found a wrapper, replace the entire block content
			if (wrapper) {
				// Create a container for the VideoBlock component
				const container = document.createElement('div')
				container.className = 'video-block-container'
				container.style.marginTop = '1rem'
				container.style.marginBottom = '1rem'
				
				// Replace the image or its parent block with the container
				if (wrapper.classList.contains('ce-block__content') || wrapper.classList.contains('cdx-block')) {
					// Replace the content of the block
					wrapper.innerHTML = ''
					wrapper.appendChild(container)
				} else {
					// Replace the image itself
					img.parentNode.replaceChild(container, img)
				}
				
				// Import VideoBlock dynamically
				import('@/components/VideoBlock.vue').then(({ default: VideoBlock }) => {
					// Mount VideoBlock component
					const app = createApp(VideoBlock, {
						file: src,
						readOnly: true,
						quizzes: []
					})
					app.use(translationPlugin)
					app.config.globalProperties.$dialog = createDialog
					app.mount(container)
				}).catch((error) => {
					console.error('Failed to load VideoBlock component:', error)
					// Fallback: create a video element
					const video = document.createElement('video')
					video.src = src
					video.controls = true
					video.style.width = '100%'
					video.style.marginTop = '1rem'
					video.style.marginBottom = '1rem'
					container.appendChild(video)
				})
			}
		}
	})
}

// Process PDF embeds and replace with PDFViewerEnhanced
const processPDFEmbeds = () => {
	// Find all iframes in the editor content
	const editorDiv = document.getElementById('editor')
	if (!editorDiv) return

	// Find all iframes that contain PDF URLs
	const iframes = editorDiv.querySelectorAll('iframe')
	iframes.forEach((iframe) => {
		const src = iframe.src || ''

		// Check if this is a PDF (either direct PDF URL or Google Docs viewer)
		const isPDFUrl = src.toLowerCase().includes('.pdf')
		const isGoogleDocsViewer = src.includes('docs.google.com/viewer') || src.includes('drive.google.com')
		const isDriveEmbed = src.includes('drive.google.com/file')

		if (isPDFUrl || isGoogleDocsViewer || isDriveEmbed) {
			// Extract the actual PDF URL
			let pdfUrl = src

			// If it's a Google Docs viewer URL, extract the actual PDF URL
			if (isGoogleDocsViewer && src.includes('url=')) {
				const urlMatch = src.match(/url=([^&]+)/)
				if (urlMatch) {
					pdfUrl = decodeURIComponent(urlMatch[1])
				}
			}

			// If it's a Google Drive embed, convert to direct download URL
			if (isDriveEmbed) {
				const fileIdMatch = src.match(/\/d\/([A-Za-z0-9_-]+)/)
				if (fileIdMatch) {
					pdfUrl = `https://drive.google.com/uc?export=download&id=${fileIdMatch[1]}`
				}
			}

			// Create a container for the Vue component
			const container = document.createElement('div')
			container.className = 'pdf-viewer-enhanced-container'
			container.style.marginTop = '1rem'
			container.style.marginBottom = '1rem'
			container.style.position = 'relative'
			container.style.isolation = 'isolate'
			container.style.contain = 'layout style'

			// Replace iframe with container
			iframe.parentNode.replaceChild(container, iframe)

			// Mount PDFViewerEnhanced component
			const app = createApp(PDFViewerEnhanced, {
				src: pdfUrl,
				documentName: pdfUrl.split('/').pop() || 'Document',
				downloadUrl: pdfUrl,
				minHeight: '500px',
				maxHeight: '80vh',
				showControls: true,
				showFooter: true
			})

			app.mount(container)
		}
	})

	// Also process PDF tool placeholders
	const pdfPlaceholders = editorDiv.querySelectorAll('.pdf-viewer-placeholder')
	pdfPlaceholders.forEach((placeholder) => {
		const pdfUrl = placeholder.getAttribute('data-pdf-url')
		const caption = placeholder.getAttribute('data-pdf-caption')
		const height = placeholder.getAttribute('data-pdf-height')

		if (pdfUrl) {
			// Create a container for the Vue component
			const container = document.createElement('div')
			container.className = 'pdf-viewer-enhanced-container'
			container.style.marginTop = '1rem'
			container.style.marginBottom = '1rem'
			container.style.position = 'relative'
			container.style.isolation = 'isolate'
			container.style.contain = 'layout style'

			// Replace placeholder with container
			placeholder.parentNode.replaceChild(container, placeholder)

			// Mount PDFViewerEnhanced component
			const app = createApp(PDFViewerEnhanced, {
				src: pdfUrl,
				documentName: caption || pdfUrl.split('/').pop() || 'Document',
				downloadUrl: pdfUrl,
				minHeight: height || '500px',
				maxHeight: '80vh',
				showControls: true,
				showFooter: true
			})

			app.mount(container)
		}
	})
}

// --- Override markProgress ---
const markProgress = () => {
  if (user.data && lesson.data && !lesson.data.progress) {
    // If there are videos, only mark complete if all are done
    if (videoFiles.value.length > 0) {
      if (completedVideos.value.size < videoFiles.value.length) return
	  console.log("progress ", completedVideos.value)
      progress.submit({ completed_videos: JSON.stringify(Array.from(completedVideos.value)) })
    } else {
      progress.submit()
    }
  }
}


const progress = createResource({
	url: 'lms.lms.doctype.course_lesson.course_lesson.save_progress',
	makeParams(values) {
		return {
			...(values || {}), // Ensure completed_videos and any other params are included
			lesson: lesson.data.name,
			course: props.courseName
		}
	},
	onSuccess(data) {
		console.log("progress onSuccess, data:", data)
		lessonProgress.value = data
		if(parseInt(data)==100){
			setCourseCompletion({
				courseName: props.courseName,
				showDocument: true
			})
		}
	},
})

const notes = createListResource({
	doctype: 'LMS Lesson Note',
	filters: {
		lesson: lesson.data?.name,
		member: user.data?.name,
	},
	fields: ['name', 'color', 'highlighted_text', 'note'],
	cache: ['notes', lesson.data?.name, user.data?.name],
	onSuccess(data) {
		data.forEach((note) => {
			setTimeout(() => {
				highlightText(note)
			}, 500)
		})
	},
})

const breadcrumbs = computed(() => {
	let items = [{ label: 'Courses', route: { name: 'Courses' } }]
	items.push({
		label: lesson?.data?.course_title,
		route: { name: 'CourseDetail', params: { courseName: props.courseName } },
	})
	items.push({
		label: lesson?.data?.title,
		route: {
			name: 'Lesson',
			params: {
				courseName: props.courseName,
				chapterNumber: props.chapterNumber,
				lessonNumber: props.lessonNumber,
			},
		},
	})
	return items
})

const switchLesson = (direction) => {
	trackVideoWatchDuration()
	let lessonIndex =
		direction === 'prev'
			? lesson.data.prev.split('.')
			: lesson.data.next.split('.')

	router.push({
		name: 'Lesson',
		params: {
			courseName: props.courseName,
			chapterNumber: lessonIndex[0],
			lessonNumber: lessonIndex[1],
		},
	})
}

watch(
	[() => route.params.chapterNumber, () => route.params.lessonNumber],
	async (
		[newChapterNumber, newLessonNumber],
		[oldChapterNumber, oldLessonNumber]
	) => {
		if (newChapterNumber || newLessonNumber) {
			plyrSources.value = []
			await nextTick()

			// Save current lesson timer state before switching
			await saveTimerState()
			if (timerFrame) cancelAnimationFrame(timerFrame)
			if (timerSaveInterval) clearInterval(timerSaveInterval)

			resetLessonState(newChapterNumber, newLessonNumber)

			// Check enrollment status for the new lesson
			if (user.data) {
				await checkEnrollmentStatus()
			}

			startTimer()
			updateNotes()
			checkIfDiscussionsAllowed()
			checkQuiz()
		}
	}
)

const resetLessonState = (newChapterNumber, newLessonNumber) => {
	editor.value = null
	instructorEditor.value = null
	allowDiscussions.value = false
	lesson.submit({
		chapter: newChapterNumber,
		lesson: newLessonNumber,
	})
	clearInterval(timerInterval)
	timer.value = 0
}

const trackVideoWatchDuration = () => {
	if (!lesson.data.membership) return
	let videoDetails = getVideoDetails()
	videoDetails = videoDetails.concat(getPlyrSourceDetails())
	call('lms.lms.api.track_video_watch_duration', {
		lesson: lesson.data.name,
		videos: videoDetails,
	})
}

const getVideoDetails = () => {
	let details = []
	const videos = document.querySelectorAll('video')
	if (videos.length > 0) {
		videos.forEach((video) => {
			if (video.currentTime == video.duration) markProgress()
			details.push({
				source: video.src,
				watch_time: video.currentTime,
			})
		})
	}
	return details
}

const getPlyrSourceDetails = () => {
	let details = []
	plyrSources.value.forEach((source) => {
		if (source.currentTime == source.duration) markProgress()
		let src = cleanYouTubeUrl(source.source)
		details.push({
			source: src,
			watch_time: source.currentTime,
		})
	})
	return details
}

const cleanYouTubeUrl = (url) => {
	if (!url) return url
	const urlObj = new URL(url)
	urlObj.searchParams.delete('t')
	return urlObj.toString()
}

watch(
	() => lesson.data,
	async (data) => {
		if (data) {
			setupLesson(data)
			getPlyrSource()
			updateNotes()

			// Check enrollment status when lesson loads
			if (user.data) {
				await checkEnrollmentStatus()
			}

			// Start timer after lesson setup if duration is available
			if (data.duration && videoFiles.value.length === 0) {
				startTimer()
			}
			if (data.icon == 'icon-youtube') clearInterval(timerInterval)
		}
	},
	{ immediate: true }
)

watch(
	() => lesson.data,
	(data) => {
		if (data && data.content) {
			try {
				const blocks = JSON.parse(data.content).blocks
				console.log("Parsed blocks:", blocks)
				videoFiles.value = extractVideoFiles(blocks)
				completedVideos.value = new Set()
			} catch (e) {
				videoFiles.value = []
				completedVideos.value = new Set()
			}
		} else {
			videoFiles.value = []
			completedVideos.value = new Set()
		}
	},
	{ immediate: true }
)

// Watch for changes in the number of video files and start/stop the timer accordingly
watch(
	() => videoFiles.value.length,
	(newLength) => {
		// Only restart timer if videos were removed (going from video lesson to non-video)
		if (newLength === 0 && lesson?.data?.duration) {
			startTimer()
		}
	}
)

function isVideoFile(type) {
	const result = ["mp4", "mov", "avi", "mkv", "webm"].includes((type || "").toLowerCase())
	return result
}

function extractVideoFiles(blocks) {
	const files = blocks
		.filter(b => {
			const isVideo = isVideoFile(b.data.file_type)
			return b.type === 'upload' && isVideo
		})
		.map(b => b.data.file_url)
	return files
}

const getPlyrSource = async () => {
	await nextTick()
	if (plyrSources.value.length == 0) {
		plyrSources.value = await enablePlyr()
	}
	updateVideoWatchDuration()
}

const updateVideoWatchDuration = () => {
	if (lesson.data.videos && lesson.data.videos.length > 0) {
		lesson.data.videos.forEach((video) => {
			if (video.source.includes('youtube') || video.source.includes('vimeo')) {
				updatePlyrVideoTime(video)
			} else {
				updateVideoTime(video)
			}
		})
	}
}

const updatePlyrVideoTime = (video) => {
	plyrSources.value.forEach((plyrSource) => {
		let lastWatchedTime = 0
		let isSeeking = false

		plyrSource.on('ready', () => {
			if (plyrSource.source === video.source) {
				plyrSource.embed.seekTo(video.watch_time, true)
				plyrSource.play()
				plyrSource.pause()
			}
		})
	})
}

const updateVideoTime = (video) => {
	const videos = document.querySelectorAll('video')
	if (videos.length > 0) {
		videos.forEach((vid) => {
			if (vid.src === video.source) {
				let watch_time = video.watch_time < vid.duration ? video.watch_time : 0
				if (vid.readyState >= 1) {
					vid.currentTime = watch_time
				} else {
					vid.addEventListener('loadedmetadata', () => {
						vid.currentTime = watch_time
					})
				}
			}
		})
	}
}

// Enrollment and Re-enrollment functions
const checkEnrollmentStatus = async () => {
	if (!user.data || !props.courseName) return

	try {
		const response = await call('lms.lms.doctype.lms_enrollment.lms_enrollment.get_current_enrollment', {
			course: props.courseName
		})

		if (response.success) {
			const enrollment = response.enrollment
			currentEnrollmentVersion.value = enrollment.enrollment_version
			enrollmentId.value = enrollment.name

			// Check if this is a re-enrollment
			if (enrollment.enrollment_version > 1 && enrollment.progress === 0) {
				isReEnrollment.value = true
				showReEnrollmentNotification()
			}

			// Load timer data from backend
			await loadTimerFromBackend()
		}
	} catch (error) {
		console.error('Error checking enrollment status:', error)
	}
}

const showReEnrollmentNotification = () => {
	// Show a notification that the user has been re-enrolled
	if (window.frappe && window.frappe.show_alert) {
		window.frappe.show_alert({
			message: 'You have been re-enrolled in this course. Your progress has been reset.',
			indicator: 'blue'
		}, 5)
	}
}

// Backend timer persistence functions
const saveTimerToBackend = async () => {
	if (!user.data || !props.courseName || !lesson.data?.name) return

	const lessonId = `${props.chapterNumber}.${props.lessonNumber}`
	const duration = lesson.data?.duration || 30
	const completed = timer.value >= duration

	try {
		await call('lms.lms.doctype.lms_enrollment.lms_enrollment.save_lesson_timer_progress_by_course', {
			course: props.courseName,
			lesson_id: lessonId,
			current_time: timer.value,
			duration: duration,
			completed: completed
		})
	} catch (error) {
		console.error('Error saving timer to backend:', error)
		// Fallback to localStorage on error
		saveTimerStateLocal()
	}
}

const loadTimerFromBackend = async () => {
	if (!user.data || !props.courseName) return 0

	const lessonId = `${props.chapterNumber}.${props.lessonNumber}`

	try {
		const response = await call('lms.lms.doctype.lms_enrollment.lms_enrollment.get_lesson_timer_progress_by_course', {
			course: props.courseName,
			lesson_id: lessonId
		})

		if (response.success && response.timer_data) {
			const timerData = response.timer_data

			// Check if enrollment version changed (re-enrollment occurred)
			if (response.enrollment_version !== currentEnrollmentVersion.value && currentEnrollmentVersion.value !== null) {
				// Reset timer for new enrollment
				currentEnrollmentVersion.value = response.enrollment_version
				return 0
			}

			if (timerData.current_time !== undefined) {
				return timerData.current_time || 0
			}
		}
	} catch (error) {
		console.error('Error loading timer from backend:', error)
	}

	// Fallback to localStorage if backend fails
	return loadTimerStateLocal()
}

// Setup periodic timer saving
const setupTimerAutoSave = () => {
	if (timerSaveInterval) clearInterval(timerSaveInterval)

	// Save timer every 5 seconds
	timerSaveInterval = setInterval(() => {
		if (!timerPaused && timer.value > 0) {
			saveTimerToBackend()
		}
	}, 5000)
}

// Local storage fallback functions (renamed from original)
const getTimerKey = () => {
  if (!lesson.data?.name || !props.courseName || !props.chapterNumber || !props.lessonNumber) return null
  return `lesson_timer_${props.courseName}_${props.chapterNumber}_${props.lessonNumber}_v${currentEnrollmentVersion.value || 1}`
}

const saveTimerStateLocal = () => {
  const key = getTimerKey()
  if (!key || timer.value === 0) return

  const timerState = {
    elapsed: timer.value,
    timestamp: Date.now(),
    lessonName: lesson.data?.name,
    duration: lesson.data?.duration,
    enrollmentVersion: currentEnrollmentVersion.value
  }
  localStorage.setItem(key, JSON.stringify(timerState))
}

const loadTimerStateLocal = () => {
  const key = getTimerKey()
  if (!key) return 0

  const savedState = localStorage.getItem(key)
  if (!savedState) return 0

  try {
    const timerState = JSON.parse(savedState)
    // Check if it's the same lesson and enrollment version
    if (timerState.lessonName !== lesson.data?.name ||
        timerState.enrollmentVersion !== currentEnrollmentVersion.value) {
      localStorage.removeItem(key)
      return 0
    }

    // If lesson is already completed (timer reached duration), return the duration
    if (timerState.elapsed >= timerState.duration) {
      return timerState.duration
    }

    // Return the saved elapsed time
    return timerState.elapsed || 0
  } catch (e) {
    console.error('Error loading timer state:', e)
    localStorage.removeItem(key)
    return 0
  }
}

const clearTimerState = () => {
  const key = getTimerKey()
  if (key) {
    localStorage.removeItem(key)
  }
}

// Combined save function that saves to both backend and localStorage
const saveTimerState = () => {
  saveTimerToBackend()
  saveTimerStateLocal()
}

// Combined load function that prioritizes backend
const loadTimerState = async () => {
  return await loadTimerFromBackend()
}

// --- Update startTimer to skip timer if videos exist ---
const startTimer = async () => {
  if (timerFrame) cancelAnimationFrame(timerFrame)

  console.log("duration", lesson.data?.duration);
  if (videoFiles.value.length > 0) return // Don't use timer for video lessons

  let durationSeconds = Number(lesson.data?.duration)
  if (isNaN(durationSeconds) || durationSeconds < 0) durationSeconds = 30
  // Enforce a minimum visible duration of 2s
  console.log("durationSeconds", durationSeconds);
  if (durationSeconds > 0 && durationSeconds < 2) durationSeconds = 2
  if (durationSeconds === 0) {
    markProgress()
    return
  }

  // Load saved timer state from backend
  const savedTime = await loadTimerState()
  timer.value = savedTime

  // If lesson was already completed previously
  if (savedTime >= durationSeconds) {
    timer.value = durationSeconds
    markProgress()
    return
  }

  // Setup auto-save interval
  setupTimerAutoSave()

  let startTimestamp = null
  let baseElapsed = savedTime // Start from saved time

  const tick = (timestamp) => {
    if (timerPaused) {
      timerFrame = requestAnimationFrame(tick)
      return
    }

    if (!startTimestamp) startTimestamp = timestamp
    const elapsed = Math.floor((timestamp - startTimestamp) / 1000) + baseElapsed

    if (elapsed > timer.value) {
      timer.value = elapsed
      // Local save every second for immediate persistence
      if (elapsed % 1 === 0) {
        saveTimerStateLocal()
      }
    }

    if (timer.value >= durationSeconds) {
      timer.value = durationSeconds
      saveTimerState()
      clearTimerState() // Clear saved state after completion
      markProgress()
      if (timerSaveInterval) clearInterval(timerSaveInterval)
      return
    }
    timerFrame = requestAnimationFrame(tick)
  }
  timerFrame = requestAnimationFrame(tick)
}

// Handle page visibility changes
const handleVisibilityChange = () => {
  if (document.hidden) {
    // Page is hidden (user switched tabs or minimized)
    timerPaused = true
    saveTimerState()
  } else {
    // Page is visible again
    timerPaused = false
    // Restart the timer if it hasn't completed and no videos exist
    if (!timerPaused && timer.value < lesson.data?.duration && videoFiles.value.length === 0) {
      if (!timerFrame) {
        startTimer()
      }
    }
  }
}

// Handle page unload
const handleBeforeUnload = () => {
  saveTimerState()
}

onBeforeUnmount(() => {
	if (timerFrame) cancelAnimationFrame(timerFrame)
	saveTimerState()
	document.removeEventListener('visibilitychange', handleVisibilityChange)
	window.removeEventListener('beforeunload', handleBeforeUnload)
})

const checkIfDiscussionsAllowed = () => {
	hasQuiz.value = false
	JSON.parse(lesson.data?.content)?.blocks?.forEach((block) => {
		if (block.type === 'quiz') {
			hasQuiz.value = true
		}
	})

	if (
		!hasQuiz.value &&
		!zenModeEnabled.value &&
		(lesson.data?.membership ||
			user.data?.is_moderator ||
			user.data?.is_instructor)
	) {
		allowDiscussions.value = true
	} else {
		allowDiscussions.value = false
	}
}

const allowEdit = () => {
	if (window.read_only_mode) return false
	if (user.data?.is_moderator) return true
	return false
}


const enrollment = createResource({
	url: 'frappe.client.insert',
	makeParams() {
		return {
			doc: {
				doctype: 'LMS Enrollment',
				course: props.courseName,
				member: user.data?.name,
			},
		}
	},
})

const enrollStudent = () => {
	enrollment.submit(
		{},
		{
			onSuccess() {
				window.location.reload()
			},
		}
	)
}

const toggleInlineMenu = async () => {
	showInlineMenu.value = false
	await nextTick()
	let selection = window.getSelection()
	if (selection.toString()) {
		showInlineMenu.value = true
	}
}

const canSeeStats = () => {
	if (user.data?.is_moderator || user.data?.is_instructor) return true
	return false
}

const showVideoStats = () => {
	showStatsDialog.value = true
}

const canGoZen = () => {
	if (
		user.data?.is_moderator ||
		user.data?.is_evaluator
	)
		return true
	if (lesson.data?.membership) return true
	return false
}

const goFullScreen = () => {
	if (lessonContainer.value.requestFullscreen) {
		lessonContainer.value.requestFullscreen()
	} else if (lessonContainer.value.mozRequestFullScreen) {
		lessonContainer.value.mozRequestFullScreen()
	} else if (lessonContainer.value.webkitRequestFullscreen) {
		lessonContainer.value.webkitRequestFullscreen()
	} else if (lessonContainer.value.msRequestFullscreen) {
		lessonContainer.value.msRequestFullscreen()
	}
}

const showDiscussionsInZenMode = () => {
	if (allowDiscussions.value) {
		allowDiscussions.value = false
	} else {
		allowDiscussions.value = true
		currentTab.value = 'Community'
		scrollDiscussionsIntoView()
	}
}

// Scroll discussions function commented out - Questions section removed
// const scrollDiscussionsIntoView = () => {
// 	nextTick(() => {
// 		discussionsContainer.value?.scrollIntoView({
// 			behavior: 'smooth',
// 			block: 'center',
// 			inline: 'nearest',
// 		})
// 	})
// }

const updateNotes = () => {
	notes.update({
		filters: {
			lesson: lesson.data?.name,
			member: user.data?.name,
		},
	})
	notes.reload()
}

watch(allowDiscussions, () => {
	if (allowDiscussions.value) {
		tabs.value = [
			{
				label: __('Notes'),
				value: 'Notes',
			},
			{
				label: __('Community'),
				value: 'Community',
			},
		]
	} else {
		tabs.value = [
			{
				label: __('Notes'),
				value: 'Notes',
			},
		]
	}
})

const redirectToLogin = () => {
	window.location.href = `/login?redirect-to=/lms/courses/${props.courseName}`
}

const goBackToCourse = () => {
	router.push({
		name: 'CourseDetail',
		params: { courseName: props.courseName },
	})
}

usePageMeta(() => {
	return {
		title: lesson?.data?.title,
		icon: brand.favicon,
	}
})
</script>
<style>

.lesson-content p {
	margin-bottom: 1rem;
	line-height: 1.7;
}

.lesson-content li {
	line-height: 1.7;
}

.lesson-content ol {
	list-style: auto;
	margin: revert;
	padding: 1rem;
}

.lesson-content ul {
	list-style: auto;
	padding: 1rem;
	margin: revert;
}

.lesson-content img {
	border: 1px solid theme('colors.gray.200');
	border-radius: 0.5rem;
}

.lesson-content code {
	display: block;
	overflow-x: auto;
	padding: 1rem 1.25rem;
	background: #011627;
	color: #d6deeb;
	border-radius: 0.5rem;
	margin: 1rem 0;
}

.lesson-content a {
	color: theme('colors.gray.900');
	text-decoration: underline;
	font-weight: 500;
}

.embed-tool__caption,
.cdx-simple-image__caption {
	display: none;
}

.ce-block__content {
	max-width: unset;
}

.codex-editor__redactor {
	padding-bottom: 0px !important;
}

.codeBoxHolder {
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
}

.codeBoxTextArea {
	width: 100%;
	min-height: 30px;
	padding: 10px;
	border-radius: 2px 2px 2px 0;
	border: none !important;
	outline: none !important;
	font: 14px monospace;
}

.codeBoxSelectDiv {
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
	position: relative;
}

.codeBoxSelectInput {
	border-radius: 0 0 20px 2px;
	padding: 2px 26px;
	padding-top: 0;
	padding-right: 0;
	text-align: left;
	cursor: pointer;
	border: none !important;
	outline: none !important;
}

.codeBoxSelectDropIcon {
	position: absolute !important;
	left: 10px !important;
	bottom: 0 !important;
	width: unset !important;
	height: unset !important;
	font-size: 16px !important;
}

.codeBoxSelectPreview {
	display: none;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
	border-radius: 2px;
	box-shadow: 0 3px 15px -3px rgba(13, 20, 33, 0.13);
	position: absolute;
	top: 100%;
	margin: 5px 0;
	max-height: 30vh;
	overflow-x: hidden;
	overflow-y: auto;
	z-index: 10000;
}

.codeBoxSelectItem {
	width: 100%;
	padding: 5px 20px;
	margin: 0;
	cursor: pointer;
}

.codeBoxSelectItem:hover {
	opacity: 0.7;
}

.codeBoxSelectedItem {
	background-color: lightblue !important;
}

.codeBoxShow {
	display: flex !important;
}

.dark {
	color: #abb2bf;
	background-color: #282c34;
}

.light {
	color: #383a42;
	background-color: #fafafa;
}

.codeBoxTextArea {
	line-height: 1.7;
}

.tc-table {
	border-left: 1px solid #e8e8eb;
}

.plyr__volume input[type='range'] {
	display: none;
}

.plyr__control--overlaid {
	background: radial-gradient(
		circle,
		rgba(0, 0, 0, 0.4) 0%,
		rgba(0, 0, 0, 0.5) 50%
	);
}

.plyr__control:hover {
	background: none;
}

.plyr--video {
	border: 1px solid theme('colors.gray.200');
	border-radius: 8px;
}

:root {
	--plyr-range-fill-background: white;
	--plyr-video-control-background-hover: transparent;
}
</style>
