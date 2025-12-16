<template>
	<div>
		<div v-if="quizzes.length && !showQuiz && readOnly" class="leading-6">
			{{
				__('This video contains {0} {1}:').format(
					quizzes.length,
					quizzes.length == 1 ? 'quiz' : 'quizzes'
				)
			}}

			<div v-for="(quiz, index) in quizzes" class="pl-3 mt-1">
				<span>
					{{ index + 1 }}. <span class="font-semibold"> {{ quiz.quiz }} </span>
				</span>
				{{ __('at {0} minutes').format(formatTimestamp(quiz.time)) }}
			</div>
		</div>
		<div
			v-if="!showQuiz"
			ref="videoContainer"
			class="video-block relative group flex"
		>
			<video
				@timeupdate="updateTime"
				@ended="videoEnded"
				@click="togglePlay"
				@loadedmetadata="onVideoLoaded"
				@seeking="onSeeking"
				@seeked="onSeeked"
				@loadstart="onVideoLoadStart"
				@canplay="onVideoCanPlay"
				@error="onVideoError"
				@waiting="onVideoWaiting"
				oncontextmenu="return false"
				class="rounded-md border border-gray-100 cursor-pointer my-0 border-none"
				ref="videoRef"
				preload="metadata"
			>
				<source :src="fileURL" :type="type" />
				Your browser does not support the video tag.
			</video>

			<!-- Loading indicator -->
			<div
				v-if="videoLoading && !videoError"
				class="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-md"
			>
				<div class="text-center">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
					<p class="text-sm text-gray-600">Loading video...</p>
				</div>
			</div>
			
			<!-- Error display -->
			<div
				v-if="videoError"
				class="absolute inset-0 flex items-center justify-center bg-red-50 rounded-md border border-red-200"
			>
				<div class="text-center p-4">
					<div class="text-red-600 mb-2">
						<svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
						</svg>
					</div>
					<p class="text-red-800 font-medium mb-2">Video Loading Error</p>
					<p class="text-red-600 text-sm mb-4">{{ videoError }}</p>
					<button
						@click="retryVideoLoad"
						class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
					>
						Retry
					</button>
				</div>
			</div>
			<div
				v-if="!playing && !videoLoading && !videoError"
				class="absolute inset-0 flex items-center justify-center cursor-pointer"
				@click="playVideo"
			>
				<div
					class="rounded-full p-4 pl-4.5"
					style="
						background: radial-gradient(
							circle,
							rgba(0, 0, 0, 0.3) 0%,
							rgba(0, 0, 0, 0.4) 50%
						);
					"
				>
					<Play />
				</div>
			</div>
			<div
				class="flex items-center space-x-2 py-2 px-1 text-ink-white bg-gradient-to-b from-transparent to-black/75 absolute bottom-0 left-0 right-0 mx-auto rounded-md"
				:class="{
					'invisible group-hover:visible': playing,
				}"
			>
				<Button variant="ghost" class="hover:bg-transparent">
					<template #icon>
						<Play
							v-if="!playing"
							@click="playVideo"
							class="size-4 text-ink-gray-9"
						/>
						<Pause v-else @click="pauseVideo" class="size-5 text-ink-white" />
					</template>
				</Button>

				<!-- Rewind Button -->
				<Button 
					variant="ghost" 
					@click="rewindVideo" 
					class="hover:bg-transparent"
					title="Rewind 10 seconds"
				>
					<template #icon>
						<Rewind class="size-4 text-ink-white" />
					</template>
				</Button>

				<div class="relative flex items-center w-full flex-1">
					<input
						type="range"
						min="0"
						:max="duration"
						step="0.1"
						:value="currentTime"		
						@input="onProgressChange"
						@change="onProgressChange"
						@mousedown="onSeekStart"
						@mouseup="onSeekEnd"
						@touchstart="onSeekStart"
						@touchend="onSeekEnd"
						class="duration-slider h-1 cursor-pointer"
					/>
					
					<!-- SEEKING LIMIT INDICATOR -->
					<div v-if="isCourseLessonContext" class="absolute top-0 left-0 w-full h-full pointer-events-none">
						<!-- Watchable area (up to maxSeekTime) -->
						<div
							:style="getSeekingLimitStyle()"
							class="absolute top-0 h-full bg-white/40 rounded-r-full transition-all duration-200 seeking-limit-area"
						></div>
						
						<!-- QUIZ MARKERS -->
						<div
							v-for="(quiz, index) in quizzes"
							:key="index"
							:style="getQuizMarkerStyle(quiz.time)"
							class="absolute top-0 h-full w-2 bg-surface-amber-3"
						></div>
						
						<!-- Seeking limit line -->
						<div
							:style="getSeekingLimitLineStyle()"
							class="absolute top-0 h-full w-1 bg-white/80 shadow-sm"
						></div>
						
						<!-- Seeking limit indicator dot -->
						<div
							:style="getSeekingLimitLineStyle()"
							class="absolute top-0 w-3 h-3 bg-white rounded-full shadow-md transform -translate-y-1 -translate-x-1.5 seeking-limit-dot"
						></div>
						
						
					</div>
					
					<!-- Seeking limit tooltip -->
					<div
						v-if="isCourseLessonContext && showSeekingTooltip"
						:style="getSeekingTooltipStyle()"
						class="absolute bottom-6 px-3 py-2 bg-black/90 text-white text-xs rounded-lg pointer-events-none whitespace-nowrap shadow-lg border border-white/20"
					>
						<div class="font-medium mb-1">Seeking Limit</div>
						<div class="text-white/80">{{ formatSeconds(currentTime) }} / {{ formatSeconds(maxSeekTime) }}</div>
						<div class="text-white/60 text-xs mt-1">You can rewind to any previous point</div>
						<div v-if="isUserSeeking" class="text-blue-300 text-xs mt-1">Video paused during seeking</div>
					</div>
				</div>

				<span class="text-sm font-medium">
					{{ formatSeconds(currentTime) }} / {{ formatSeconds(duration) }}
				</span>
				<Button
					variant="ghost"
					@click="toggleMute"
					class="hover:bg-transparent"
				>
					<template #icon>
						<Volume2 v-if="!muted" class="size-5 text-ink-white" />
						<VolumeX v-else class="size-5 text-ink-white" />
					</template>
				</Button>
				<Button
					variant="ghost"
					@click="toggleFullscreen"
					class="hover:bg-transparent"
				>
					<template #icon>
						<Maximize class="size-5 text-ink-white" />
					</template>
				</Button>
			</div>
		</div>
		<Quiz
			v-if="showQuiz"
			:quizName="currentQuiz"
			:inVideo="true"
			:backToVideo="resumeVideo"
		/>
		<div v-if="!readOnly" @click="showQuizModal = true">
			<Button>
				{{ __('Add Quiz to Video') }}
			</Button>
		</div>
	</div>
	<QuizInVideo
		v-model="showQuizModal"
		:quizzes="quizzes"
		:saveQuizzes="saveQuizzes"
		:duration="duration"
	/>
	<Dialog
		v-model="showQuizLoader"
		:options="{
			size: 'sm',
		}"
	>
		<template #body>
			<div class="flex flex-col space-y-2 p-5 text-base leading-5">
				<span class="font-semibold">
					{{ __('Time for a Quiz') }}
				</span>
				<span>
					{{
						__(
							'Complete the upcoming quiz to continue watching the video. The quiz will open in {0} {1}.'
						).format(quizLoadTimer, quizLoadTimer === 1 ? 'second' : 'seconds')
					}}
				</span>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, defineEmits } from 'vue'
import { Pause, Maximize, Volume2, VolumeX, Rewind } from 'lucide-vue-next'
import { Button, Dialog, call } from 'frappe-ui'
import { formatSeconds, formatTimestamp } from '@/utils'
import { useSettings } from '@/stores/settings'
import Play from '@/components/Icons/Play.vue'
import QuizInVideo from '@/components/Modals/QuizInVideo.vue'
import { useRoute } from 'vue-router'

const videoRef = ref(null)
const videoContainer = ref(null)
let playing = ref(false)
let currentTime = ref(0)
let duration = ref(0)
let muted = ref(false)
const showQuizModal = ref(false)
const showQuiz = ref(false)
const showQuizLoader = ref(false)
const quizLoadTimer = ref(0)
const currentQuiz = ref(null)
const nextQuiz = ref({})
const { settings } = useSettings()
const isSeeking = ref(false)
const maxSeekTime = ref(0) // Track the maximum time user has reached
const maxWatchedTime = ref(0) // Track the actual maximum time user has watched
const isUserSeeking = ref(false) // Track if user is actively seeking
const showSeekingTooltip = ref(false) // Show tooltip during seeking
const progressUpdateInterval = ref(null) // Store interval reference for progress updates
const lastProgressUpdate = ref(0) // Track last progress update time
const videoLoading = ref(true) // Track video loading state
const videoError = ref(null) // Track video loading errors
const desiredStartTime = ref(null)
const initialSeekApplied = ref(false)

let route = null
try {
	route = useRoute()
} catch (e) {
	route = null
}

const props = defineProps({
	file: {
		type: String,
		required: true,
	},
	type: {
		type: String,
		default: 'video/mp4',
	},
	readOnly: {
		type: Boolean,
		default: true,
	},
	quizzes: {
		type: Array,
		default: () => [],
	},
	saveQuizzes: {
		type: Function,
		default: () => {},
	},
    // Optional identifiers if parent wants to pass explicitly
    courseId: {
        type: String,
        required: false,
        default: null,
    },
    lessonId: {
        type: String,
        required: false,
        default: null,
    },
})

// Derive identifiers from props first, then fallback to route params, then URL path
const courseId = computed(() => {
    if (props.courseId) return props.courseId
    const p = (route && route.params) ? route.params : {}
    const fromParams = p.courseName || p.course || p.course_id || p.courseID
    if (fromParams) return fromParams
    // Fallback: parse from /lms/courses/<course>/learn/<lesson>
    const segments = (typeof window !== 'undefined' && window.location && window.location.pathname)
        ? window.location.pathname.split('/').filter(Boolean)
        : []
    const idx = segments.findIndex(s => s === 'courses')
    return idx !== -1 && segments[idx + 1] ? decodeURIComponent(segments[idx + 1]) : null
})

const lessonId = computed(() => {
    if (props.lessonId) return props.lessonId
    const p = (route && route.params) ? route.params : {}
    const fromParams = p.lessonId || p.lesson || p.lesson_id || p.lessonID || p.name
    if (fromParams) return fromParams
    // Fallback: parse from /lms/courses/<course>/learn/<lesson>
    const segments = (typeof window !== 'undefined' && window.location && window.location.pathname)
        ? window.location.pathname.split('/').filter(Boolean)
        : []
    const idx = segments.findIndex(s => s === 'learn')
    return idx !== -1 && segments[idx + 1] ? decodeURIComponent(segments[idx + 1]) : null
})

// Only enforce restrictions and save progress inside a course lesson context
const isCourseLessonContext = computed(() => Boolean(courseId.value && lessonId.value))

const emit = defineEmits(['video-completed', 'video-duration'])

// Generate a unique key for this video file
const getProgressKey = () => `video-progress-${props.file}`

// API function to update course progress
const updateCourseProgress = async (progressData) => {
	try {
		// Ensure identifiers are available before calling backend
		if (!isCourseLessonContext.value || !props.file) {
			return
		}
		
		const response = await call('lms.overrides.videoprogress.update_video_progress', 
		 {
				course_id: courseId.value,
				lesson_id: lessonId.value,
				video_file: props.file,
				current_time: progressData.currentTime,
				duration: progressData.duration,
				progress_percentage: progressData.duration > 0 ? (progressData.currentTime / progressData.duration) * 100 : 0,
				max_watched_time: progressData.maxWatchedTime,
				timestamp: Date.now()
			}
		);
		
		return response
	} catch (error) {
		// Don't throw error to prevent breaking video functionality
	}
}

// Function to start progress update interval
const startProgressUpdateInterval = () => {
	// Clear any existing interval
	if (progressUpdateInterval.value) {
		clearInterval(progressUpdateInterval.value)
	}
	
	// Start new interval - update every 5 seconds
	progressUpdateInterval.value = setInterval(() => {
		// Only update if video is playing and has meaningful progress
		if (playing.value && currentTime.value > 0 && duration.value > 0) {
			const progressData = {
				currentTime: currentTime.value,
				duration: duration.value,
				maxWatchedTime: maxWatchedTime.value
			}
			
			// Update last progress update time
			lastProgressUpdate.value = Date.now()
			
			// Send progress update to backend
			updateCourseProgress(progressData)
		}
	}, 5000) // 5 seconds
}

// Function to stop progress update interval
const stopProgressUpdateInterval = () => {
	if (progressUpdateInterval.value) {
		clearInterval(progressUpdateInterval.value)
		progressUpdateInterval.value = null
	}
}

// Fetch previously saved progress from server and restore
const fetchAndRestoreProgress = async () => {
	try {
		if (!props.file || !courseId.value || !lessonId.value) return
		const response = await call('lms.overrides.videoprogress.get_video_progress', {
			course_id: courseId.value,
			lesson_id: lessonId.value,
			video_file: props.file,
		})
		const saved = response?.progress
		if (saved) {
			maxWatchedTime.value = Math.max(0, Number(saved.max_watched_time) || 0)
			maxSeekTime.value = Math.max(maxSeekTime.value, maxWatchedTime.value)
			// Resume from the maximum watched time, not the previously saved current time
			const resumeTime = Math.max(0, Number(saved.max_watched_time) || 0)
			desiredStartTime.value = Math.min(resumeTime, maxSeekTime.value)
			currentTime.value = desiredStartTime.value
		}
	} catch (e) {
		// ignore
	}
}

onMounted(() => {
	// Initialize video state
	videoLoading.value = true
	videoError.value = null
	
	// Restore server progress
	fetchAndRestoreProgress()
	updateCurrentTime()
	updateNextQuiz()
	
	
	// Pause video if user moves to a different tab
	document.addEventListener('visibilitychange', handleVisibilityChange)
	
	// Ensure video element is properly initialized
	setTimeout(() => {
		if (videoRef.value && props.file) {
			videoRef.value.load()
		}
	}, 100)
})

onBeforeUnmount(() => {
	// Cleanup only
	document.removeEventListener('visibilitychange', handleVisibilityChange)
})

const handleVisibilityChange = () => {
	if (document.visibilityState === 'hidden') {
		if (playing.value && videoRef.value) {
			videoRef.value.pause()
			playing.value = false
			// Stop progress updates when tab becomes hidden
			stopProgressUpdateInterval()
		}
	} else {
		// Tab became visible again
		// Progress updates will be restarted when user plays the video
	}
}

const onVideoLoadStart = () => {
	videoLoading.value = true
	videoError.value = null
}

const onVideoCanPlay = () => {
	videoLoading.value = false
	videoError.value = null
	// Ensure initial seek is applied as soon as the video can play
	if (isCourseLessonContext.value && !initialSeekApplied.value && desiredStartTime.value != null) {
		const dur = Number(videoRef.value?.duration) || 0
		const nearEndGuard = dur > 0 ? Math.max(0, dur - 0.5) : desiredStartTime.value
		const target = Math.min(desiredStartTime.value, maxSeekTime.value, nearEndGuard)
		try {
			if (videoRef.value && !videoRef.value.paused) videoRef.value.pause()
			if (videoRef.value) videoRef.value.currentTime = target
			currentTime.value = target
			initialSeekApplied.value = true
		} catch (e) {}
	}
}

const onVideoError = (event) => {
	videoLoading.value = false
	const error = videoRef.value.error
	let errorMessage = 'Unknown error occurred'
	
	if (error) {
		switch (error.code) {
			case error.MEDIA_ERR_ABORTED:
				errorMessage = 'Video loading was aborted'
				break
			case error.MEDIA_ERR_NETWORK:
				errorMessage = 'Network error occurred while loading video'
				break
			case error.MEDIA_ERR_DECODE:
				errorMessage = 'Video decoding error'
				break
			case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
				errorMessage = 'Video format not supported or file not found'
				break
			default:
				errorMessage = `Video error: ${error.message || 'Unknown error'}`
		}
	}
	
	videoError.value = errorMessage
}

const onVideoWaiting = () => {
	// Video is buffering
}

const retryVideoLoad = () => {
	videoError.value = null
	videoLoading.value = true
	
	// Force reload the video
	if (videoRef.value) {
		videoRef.value.load()
	}
}

const onVideoLoaded = () => {
	duration.value = videoRef.value.duration
	emit('video-duration', { file: props.file, duration: duration.value })
	
	// Ensure seekable area is properly maintained after video loads
	maintainSeekableArea()
	
	// Apply initial seek exactly once if we have a saved time
	if (isCourseLessonContext.value && !initialSeekApplied.value && desiredStartTime.value != null) {
		const safeTime = Math.min(desiredStartTime.value, maxSeekTime.value)
		try { videoRef.value.currentTime = safeTime } catch {}
		currentTime.value = safeTime
		initialSeekApplied.value = true
	} else if (currentTime.value > 0 && !isSeeking.value && !isUserSeeking.value) {
		// Fallback to currentTime constraint
		const safeTime = Math.min(currentTime.value, maxSeekTime.value)
		videoRef.value.currentTime = safeTime
		currentTime.value = safeTime
	}
}

const updateTime = () => {
	// Always sync currentTime with the video element during normal playback
	if (!isSeeking.value && !isUserSeeking.value && videoRef.value) {
		const videoCurrentTime = videoRef.value.currentTime

		// Update whenever a small change occurs
		if (Math.abs(videoCurrentTime - currentTime.value) > 0.1) {
			currentTime.value = videoCurrentTime
		}

		if (isCourseLessonContext.value) {
			// Update max watched time (this never decreases)
			const prevMaxWatched = maxWatchedTime.value
			maxWatchedTime.value = Math.max(maxWatchedTime.value, currentTime.value)

			// Send progress on 5-second milestones
			if (
				Math.floor(maxWatchedTime.value) % 5 === 0 && 
				Math.floor(prevMaxWatched) !== Math.floor(maxWatchedTime.value)
			) {
				const progressData = {
					currentTime: currentTime.value,
					duration: duration.value,
					maxWatchedTime: maxWatchedTime.value
				}
				updateCourseProgress(progressData);
			}

			// Safely update seekable area (only during normal playback)
			updateSeekableArea()
		}
	}

	// Check for quiz triggers
	if (currentTime.value >= nextQuiz.value.time && nextQuiz.value.time > 0) {
		videoRef.value.pause()
		playing.value = false
		currentQuiz.value = nextQuiz.value.quiz
		quizLoadTimer.value = 7
	}
}


const onProgressChange = (event) => {
	const newTime = parseFloat(event.target.value)
	// Prevent seeking forward beyond the maximum time user has reached (only in course/lesson)
	if (isCourseLessonContext.value && newTime > maxSeekTime.value) {
		event.target.value = maxSeekTime.value
		return
	}
	
	// Prevent seeking to 0 unless user explicitly wants to restart
	// This prevents accidental video restarts when seeking
	if (isCourseLessonContext.value && newTime === 0 && currentTime.value > 5) {
		// If user is trying to seek to 0 from a significant position, 
		// ask for confirmation or prevent it
		event.target.value = currentTime.value
		return
	}
	
	// Set user seeking flag
	isUserSeeking.value = true
	
	// Set seeking flag to prevent time updates during seek
	isSeeking.value = true
	
	// Update current time immediately for smooth UI
	currentTime.value = newTime
	
	// Update video position if video is ready and time is valid
	if (videoRef.value && !isNaN(newTime) && newTime >= 0) {
		// Only seek if the time is significantly different to prevent unnecessary seeking
		if (Math.abs(videoRef.value.currentTime - newTime) > 0.5) {
			// Update video position
			videoRef.value.currentTime = newTime
			currentTime.value = Math.min(newTime, maxSeekTime.value)
			
			// Update quiz state
			updateNextQuiz()
			
			// Don't update maxSeekTime during seeking - it should only be updated during normal playback
			// This prevents the seekable area from being reset
		}
	}
	
	// Show tooltip during seeking
	showSeekingTooltip.value = true
	
	// Reset seeking flags after a short delay to allow for smooth seeking
	setTimeout(() => {
		isSeeking.value = false
	}, 100)
	
	// Safety timeout to ensure seeking state is reset
	setTimeout(() => {
		if (isUserSeeking.value) {
			resetSeekingState()
		}
	}, 2000)
}

const rewindVideo = () => {
	if (videoRef.value) {
		const newTime = Math.max(0, currentTime.value - 10)
		
		// Set user seeking flag
		isUserSeeking.value = true
		
		// Set seeking flag to prevent time updates during seek
		isSeeking.value = true
		
		// Update current time immediately for smooth UI
		currentTime.value = newTime
		
		// Store current playback state
		const wasPlaying = !videoRef.value.paused
		
		// Only seek if the time is significantly different to prevent unnecessary seeking
		if (Math.abs(videoRef.value.currentTime - newTime) > 0.5) {
			// Update video position
			videoRef.value.currentTime = newTime
			
			// Update quiz state
			updateNextQuiz()
			
			// Don't update maxSeekTime during seeking - it should only be updated during normal playback
			// This prevents the seekable area from being reset
			
			// Ensure video stays in the same playback state
			if (wasPlaying && videoRef.value.paused) {
				videoRef.value.play().catch(() => {
					// Ignore play errors during seeking
				})
			}
		}
		
		// Reset seeking flag after video has settled
		setTimeout(() => {
			isSeeking.value = false
			isUserSeeking.value = false
		}, 300)
	}
}

const onSeeking = () => {
	// Video is seeking - set flag to prevent conflicts
	isSeeking.value = true
	isUserSeeking.value = true

	// Prevent seeking video more than current max watched time
	if (videoRef.value && typeof maxSeekTime.value === 'number') {
		if (videoRef.value.currentTime > maxSeekTime.value) {
			videoRef.value.currentTime = maxSeekTime.value
			currentTime.value = maxSeekTime.value
		}
	}
}

const onSeeked = () => {
	// Prevent seeking beyond max watched time
	if (videoRef.value && typeof maxSeekTime.value === 'number') {
		if (videoRef.value.currentTime > maxSeekTime.value) {
			videoRef.value.currentTime = maxSeekTime.value
			currentTime.value = maxSeekTime.value
		}
	}
	// Video has finished seeking - reset flag after a short delay
	setTimeout(() => {
		isSeeking.value = false
		// Also reset user seeking flag if it's been set
		if (isUserSeeking.value) {
			isUserSeeking.value = false
		}
	}, 100)
}

const onSeekStart = () => {
	// Show tooltip when user starts seeking
	showSeekingTooltip.value = true
	
	// Reset any previous seeking state to ensure clean start
	resetSeekingState()
	
	// Set user seeking flag
	isUserSeeking.value = true
	
	// Store current play state and pause video during seeking
	if (videoRef.value) {
		// Store the previous play state
		videoRef.value._previousPlayState = !videoRef.value.paused
		
	}
}

const onSeekEnd = () => {
	// Hide tooltip when user stops seeking
	setTimeout(() => {
		showSeekingTooltip.value = false
	}, 1000)
	
	// Restore previous play state and reset seeking flags
	if (videoRef.value) {
		// Reset all seeking state
		resetSeekingState()
		
		// Ensure seekable area is maintained
		maintainSeekableArea()
		
		// Restore previous play state
		if (videoRef.value._previousPlayState) {
			videoRef.value.play().then(() => {
				playing.value = true
			}).catch(() => {
				// Ignore play errors
			})
		}
		
		// Clear stored play state
		delete videoRef.value._previousPlayState
	}
}

const getSeekingLimitStyle = () => {
	if (duration.value <= 0) return {}
	const percentage = (maxSeekTime.value / duration.value) * 100
	return {
		width: `${percentage}%`,
	}
}

const getSeekingLimitLineStyle = () => {
	if (duration.value <= 0) return {}
	const percentage = (maxSeekTime.value / duration.value) * 100
	return {
		left: `${percentage}%`,
	}
}

const getSeekingTooltipStyle = () => {
	if (duration.value <= 0) return {}
	const percentage = (maxSeekTime.value / duration.value) * 100
	return {
		left: `${percentage}%`,
		transform: 'translateX(-50%)',
	}
}

// Function to ensure seekable area is maintained
const maintainSeekableArea = () => {
	// Always ensure maxSeekTime is at least as large as maxWatchedTime
	// This prevents the seekable area from shrinking
	if (isCourseLessonContext.value) {
		maxSeekTime.value = Math.max(maxSeekTime.value, maxWatchedTime.value)
	} else {
		// No restrictions outside course/lesson context
		maxSeekTime.value = duration.value || maxSeekTime.value
	}
	
	// Log the current seekable area for debugging
}

// Function to safely update seekable area (only during normal playback)
const updateSeekableArea = () => {
	// Only update seekable area if not currently seeking
	if (!isSeeking.value && !isUserSeeking.value) {
		// Store the previous maxSeekTime to prevent accidental resets
		const previousMaxSeekTime = maxSeekTime.value
		
		if (isCourseLessonContext.value) {
			// Update maxSeekTime to be at least as large as maxWatchedTime
			maxSeekTime.value = Math.max(maxSeekTime.value, maxWatchedTime.value)
		} else {
			// No restriction outside course/lesson
			maxSeekTime.value = duration.value || maxSeekTime.value
		}
		
		// Log if there was a significant change in seekable area
		if (Math.abs(previousMaxSeekTime - maxSeekTime.value) > 1) {
			// updated
		}
	}
}

// Function to force reset seeking state
const resetSeekingState = () => {
	isSeeking.value = false
	isUserSeeking.value = false
	showSeekingTooltip.value = false
}

// Function to save final progress snapshot
const saveFinalProgress = () => {
	try {
		// Ensure we have the latest values
		const finalProgress = {
			currentTime: currentTime.value,
			duration: duration.value || 0,
			maxWatchedTime: maxWatchedTime.value,
			maxSeekTime: maxSeekTime.value,
			timestamp: Date.now(),
			file: props.file,
			isFinal: true // Mark this as a final save
		}
		localStorage.setItem(getProgressKey(), JSON.stringify(finalProgress))
	} catch (error) {
		console.warn('Failed to save final video progress:', error)
	}
}



const updateCurrentTime = () => {
	setTimeout(() => {
		// Set up metadata handler only once
		if (videoRef.value && !videoRef.value.onloadedmetadata) {
			videoRef.value.onloadedmetadata = () => {
				duration.value = videoRef.value.duration
				emit('video-duration', { file: props.file, duration: duration.value })
			}
		}
		
		// Set up time update handler only once
		if (videoRef.value && !videoRef.value.ontimeupdate) {
			videoRef.value.ontimeupdate = () => {
				// This is now handled by the updateTime function
				// No need to duplicate the logic here
			}
		}
	}, 0)
}

watch(quizLoadTimer, () => {
	if (quizLoadTimer.value > 0) {
		showQuizLoader.value = true
		setTimeout(() => {
			quizLoadTimer.value -= 1
		}, 1000)
	} else {
		showQuizLoader.value = false
		showQuiz.value = true
	}
})

const resumeVideo = (restart = false) => {
	showQuiz.value = false
	currentQuiz.value = null
	updateCurrentTime()
	setTimeout(() => {
		// Only restart to beginning if explicitly requested and not during seeking
		if (restart && !isUserSeeking.value && !isSeeking.value) {
			videoRef.value.currentTime = 0
			currentTime.value = 0
			// Reset progress tracking when restarting
			maxWatchedTime.value = 0
			maxSeekTime.value = 0
		} else {
			// Resume from current position, ensuring it's within seekable area
			const safeTime = Math.min(currentTime.value, maxSeekTime.value)
			videoRef.value.currentTime = safeTime
			currentTime.value = safeTime
		}
		videoRef.value.play()
		playing.value = true
		updateNextQuiz()
	}, 0)
}

const updateNextQuiz = () => {
	if (!props.quizzes.length) {
		nextQuiz.value = {}
		return
	}

	props.quizzes.forEach((quiz) => {
		if (typeof quiz.time == 'string' && quiz.time.includes(':')) {
			let time = quiz.time.split(':')
			let timeInSeconds = parseInt(time[0]) * 60 + parseInt(time[1])
			quiz.time = timeInSeconds
		}
	})

	props.quizzes.sort((a, b) => a.time - b.time)

	const nextQuizIndex = props.quizzes.findIndex(
		(quiz) => quiz.time > currentTime.value
	)
	if (nextQuizIndex !== -1) {
		nextQuiz.value = props.quizzes[nextQuizIndex]
	} else {
		// No more quizzes, set to empty object with time 0 to prevent false triggers
		nextQuiz.value = { time: 0, quiz: null }
	}
}

const fileURL = computed(() => {
	if (!props.file) {
		console.warn('No video file provided')
		return ''
	}
	
	// Ensure the file URL is properly formatted
	let url = props.file
	
	// If it's a relative path, make it absolute
	if (!url.startsWith('http') && !url.startsWith('/')) {
		url = '/' + url
	}
	
	// Add cache busting parameter to prevent caching issues
	const separator = url.includes('?') ? '&' : '?'
	url += `${separator}t=${Date.now()}`
	
	return url
})

watch(props, (newVal, oldVal) => {
	// Reset video state when file changes
	if (newVal.file !== oldVal.file) {
		videoLoading.value = true
		videoError.value = null
		playing.value = false
		currentTime.value = 0
		duration.value = 0
		
		// Reload video progress for new file from server
		fetchAndRestoreProgress()
	}
})




const playVideo = () => {
	if (!videoRef.value) return

	// If we have a desired start and haven't applied it yet, ensure seek before play
	if (isCourseLessonContext.value && !initialSeekApplied.value && desiredStartTime.value != null) {
		const applyAndPlay = () => {
			const dur = Number(videoRef.value?.duration) || 0
			const nearEndGuard = dur > 0 ? Math.max(0, dur - 0.5) : desiredStartTime.value
			const target = Math.min(desiredStartTime.value, maxSeekTime.value, nearEndGuard)
			try {
				videoRef.value.currentTime = target
				currentTime.value = target
				initialSeekApplied.value = true
			} catch (e) {}
			videoRef.value.play()
			playing.value = true
		}

		// If metadata not loaded yet, wait for canplay
		if (!isFinite(Number(videoRef.value.duration)) || Number(videoRef.value.duration) === 0) {
			const once = () => {
				videoRef.value.removeEventListener('canplay', once)
				applyAndPlay()
			}
			videoRef.value.addEventListener('canplay', once)
			return
		} else {
			applyAndPlay()
			return
		}
	}

	videoRef.value.play()
	playing.value = true
	// Restart progress updates when video starts playing
}

const pauseVideo = () => {
	videoRef.value.pause()
	playing.value = false
}

const togglePlay = () => {
	if (playing.value) {
		pauseVideo()
	} else {
		playVideo()
	}
}

const videoEnded = () => {
	playing.value = false
	// Stop progress updates when video ends
	
	// Send final progress update (100% completion)
	const finalProgressData = {
		currentTime: duration.value,
		duration: duration.value,
		maxWatchedTime: duration.value
	}
	updateCourseProgress(finalProgressData)
	
	emit('video-completed', props.file)
	window.dispatchEvent(new CustomEvent('video-completed', { detail: { file: props.file } }))
}

const toggleMute = () => {
	videoRef.value.muted = !videoRef.value.muted
	muted.value = videoRef.value.muted
}

const changeCurrentTime = () => {
	if (
		settings.data?.prevent_skipping_videos &&
		currentTime.value > videoRef.value.currentTime
	)
		return
	videoRef.value.currentTime = currentTime.value
	updateNextQuiz()
}

const toggleFullscreen = () => {
	if (document.fullscreenElement) {
		document.exitFullscreen()
	} else {
		videoContainer.value.requestFullscreen()
	}
}

const getQuizMarkerStyle = (time) => {
	const percentage = ((time - 5) / Math.ceil(duration.value)) * 100
	return {
		left: `${percentage}%`,
	}
}
</script>

<style scoped>

/* remove browser native video controllers */
video::-webkit-media-controls { display:none !important; }
video::-webkit-media-controls-enclosure { display:none !important; }
video::-webkit-media-controls-panel { display:none !important; }
video::-moz-media-controls { display:none !important; }


.video-block {
	width: 100%;
	margin: 0 auto;
}

.video-block video {
	width: 100%;
	height: auto;
}

iframe {
	width: 100%;
	min-height: 500px;
}

.duration-slider {
	-webkit-appearance: none;
	appearance: none;
	border-radius: 10px;
	background-color: theme('colors.gray.600');
	cursor: pointer;
	transition: all 0.2s ease;
}

.duration-slider:hover {
	background-color: theme('colors.gray.500');
}

.duration-slider::-webkit-slider-thumb {
	width: 12px;
	height: 12px;
	border-radius: 50%;
	-webkit-appearance: none;
	background-color: theme('colors.white');
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
	cursor: pointer;
	transition: all 0.2s ease;
}

.duration-slider::-webkit-slider-thumb:hover {
	transform: scale(1.2);
	box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4);
}

.duration-slider::-moz-range-thumb {
	width: 12px;
	height: 12px;
	border-radius: 50%;
	border: none;
	background-color: theme('colors.white');
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
	cursor: pointer;
	transition: all 0.2s ease;
}

.duration-slider::-moz-range-thumb:hover {
	transform: scale(1.2);
	box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4);
}

@media screen and (-webkit-min-device-pixel-ratio: 0) {
	input[type='range'] {
		overflow: hidden;
		width: 100%;
	}

	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		cursor: pointer;
		box-shadow: -500px 0 0 500px theme('colors.white');
	}
}

/* Video control buttons hover effects */
.video-block button:hover {
	background-color: rgba(255, 255, 255, 0.1) !important;
	border-radius: 4px;
}

/* Seeking limit indicator animations */
.seeking-limit-dot {
	animation: pulse 2s infinite;
}

@keyframes pulse {
	0% {
		opacity: 1;
		transform: scale(1) translate(-50%, -33%);
	}
	50% {
		opacity: 0.7;
		transform: scale(1.1) translate(-50%, -33%);
	}
	100% {
		opacity: 1;
		transform: scale(1) translate(-50%, -33%);
	}
}

/* Progress bar fill with seeking limit */
.duration-slider {
	background: linear-gradient(
		to right,
		theme('colors.white') 0%,
		theme('colors.white') var(--progress, 0%),
		theme('colors.gray.600') var(--progress, 0%)
	);
}

/* Enhanced progress bar with seeking limit visualization */
.duration-slider::-webkit-slider-runnable-track {
	background: linear-gradient(
		to right,
		theme('colors.white') 0%,
		theme('colors.white') var(--seeking-limit, 0%),
		rgba(255, 255, 255, 0.3) var(--seeking-limit, 0%),
		theme('colors.gray.600') var(--seeking-limit, 0%)
	);
}

/* Enhanced seeking limit visual feedback */
.seeking-limit-area {
	background: linear-gradient(
		to right,
		rgba(255, 255, 255, 0.4) 0%,
		rgba(255, 255, 255, 0.2) 100%
	);
}
</style>