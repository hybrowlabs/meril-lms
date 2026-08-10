<template>
	<div
		v-if="course.title"
		class="flex flex-col h-full rounded-md border-2 overflow-auto"
		style="min-height: 350px"
	>
		<div
			class="course-image"
			:class="{ 'default-image': !course.image }"
			:style="{ backgroundImage: 'url(\'' + encodeURI(course.image) + '\')' }"
		>
			<div class="flex items-center flex-wrap relative top-4 px-2 w-fit">
				<Badge
					v-if="course.featured"
					variant="subtle"
					theme="green"
					size="md"
					class="mb-1 mr-1"
				>
					{{ __('Featured') }}
				</Badge>
				<!-- Completion Status Badge -->
				<Badge
					v-if="showCompletionBadge"
					variant="subtle"
					:theme="completionBadgeTheme"
					size="md"
					class="mb-1 mr-1"
				>
					{{ completionBadgeText }}
				</Badge>
				<div
					v-if="course.tags"
					v-for="tag in course.tags?.split(', ')"
					class="text-xs bg-white text-gray-800 px-2 py-0.5 rounded-md mb-1 mr-1"
				>
					{{ tag }}
				</div>
			</div>
			<div v-if="!course.image" class="image-placeholder">
				{{ course.title[0] }}
			</div>
		</div>
		<div class="flex flex-col flex-auto p-4">
			<div class="flex items-center justify-between mb-2">
				<div v-if="course.lessons">
					<Tooltip :text="__('Lessons')">
						<span class="flex items-center text-ink-gray-7">
							<BookOpen class="h-4 w-4 stroke-1.5 mr-1" />
							{{ course.lessons }}
						</span>
					</Tooltip>
				</div>

				<div v-if="course.status != 'Approved'">
					<Badge
						variant="subtle"
						:theme="course.status === 'Under Review' ? 'orange' : 'blue'"
						size="sm"
					>
						{{ course.status }}
					</Badge>
				</div>
			</div>

			<div class="text-xl font-semibold leading-6 text-ink-gray-9">
				{{ course.title }}
			</div>

			<div class="short-introduction text-ink-gray-7 text-sm">
				{{ course.short_introduction }}
			</div>

			<!-- Progress Bar and Completion Status -->
			<div v-if="user && course.membership">
				<ProgressBar
					:progress="course.membership.progress"
				/>
				
				<!-- Completion Information -->
				<div v-if="isCompleted" class="mt-2 mb-4">
					<div class="flex items-center text-sm text-ink-gray-7 mb-1">
						<CheckCircle class="h-4 w-4 mr-1 text-green-600" />
						{{ __('Course Completed') }}
					</div>
					<div class="text-xs text-ink-gray-6">
						{{ __('Completed on') }}: {{ formatCompletionDate }}
					</div>
					<div v-if="isReEnrolled" class="text-xs text-blue-600 mt-1">
						{{ __('Re-enrolled on') }}: {{ formatReEnrollmentDate }}
					</div>
				</div>
				
				<!-- Active Progress -->
				<div
					v-else-if="course.membership.progress != null"
					class="text-sm text-ink-gray-7 mt-2 mb-4"
				>
					{{ Math.ceil(course.membership.progress) }}% completed
				</div>
			</div>

			<div class="flex items-center justify-between mt-auto">
				<div></div>

				<div v-if="course.paid_course" class="font-semibold">
					{{ course.price }}
				</div>
				<div
					v-if="course.paid_certificate || course.enable_certification"
					class="text-xs text-ink-blue-3 bg-surface-blue-1 py-0.5 px-1 rounded-md"
				>
					{{ __('Certification') }}
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import { BookOpen, CheckCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import { sessionStore } from '@/stores/session'
import { Badge, Tooltip } from 'frappe-ui'
import ProgressBar from '@/components/ProgressBar.vue'

const { user } = sessionStore()

const props = defineProps({
	course: {
		type: Object,
		default: null,
	},
})

// Computed properties for completion status
const isCompleted = computed(() => {
	return props.course.membership?.completion_status === 'Completed'
})

const isReEnrolled = computed(() => {
	return props.course.membership?.completion_status === 'Re-enrolled'
})

const completionStatus = computed(() => {
	return props.course.membership?.completion_status || 'Active'
})

const showCompletionBadge = computed(() => {
	return user && props.course.membership && 
		   (completionStatus.value === 'Completed' || completionStatus.value === 'Re-enrolled')
})

const completionBadgeText = computed(() => {
	switch (completionStatus.value) {
		case 'Completed':
			return __('Completed')
		case 'Re-enrolled':
			return __('Re-enrolled')
		default:
			return ''
	}
})

const completionBadgeTheme = computed(() => {
	switch (completionStatus.value) {
		case 'Completed':
			return 'green'
		case 'Re-enrolled':
			return 'blue'
		default:
			return 'gray'
	}
})

const formatCompletionDate = computed(() => {
	if (!props.course.membership?.completed_on) return ''
	
	const date = new Date(props.course.membership.completed_on)
	return date.toLocaleDateString()
})

const formatReEnrollmentDate = computed(() => {
	if (!props.course.membership?.re_enrolled_on) return ''
	
	const date = new Date(props.course.membership.re_enrolled_on)
	return date.toLocaleDateString()
})
</script>
<style>
.course-image {
	height: 168px;
	width: 100%;
	background-size: cover;
	background-position: center;
	background-repeat: no-repeat;
	position: relative;
}

.course-card-pills {
	background: #ffffff;
	margin-left: 0;
	margin-right: 0.5rem;
	padding: 3.5px 8px;
	font-size: 11px;
	text-align: center;
	letter-spacing: 0.011em;
	text-transform: uppercase;
	font-weight: 600;
	width: fit-content;
}

.default-image {
	display: flex;
	flex-direction: column;
	align-items: center;
	background-color: theme('colors.green.100');
	color: theme('colors.green.600');
}

.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
}
.image-placeholder {
	display: flex;
	align-items: center;
	flex: 1;
	font-size: 5rem;
	color: theme('colors.gray.700');
	font-weight: 600;
}
.avatar-group.overlap .avatar + .avatar {
	margin-left: calc(-8px);
}

.short-introduction {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	margin: 0.25rem 0 1.25rem;
	line-height: 1.5;
}
</style>
