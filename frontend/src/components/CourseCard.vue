<template>
	<div
		v-if="course.title"
		class="flex flex-col h-full rounded-md overflow-auto text-ink-gray-9"
		style="min-height: 350px"
	>
		<div
			class="w-[100%] h-[168px] bg-cover bg-center bg-no-repeat border-t border-x rounded-t-md"
			:style="
				course.image
					? { backgroundImage: `url('${encodeURI(course.image)}')` }
					: {
							backgroundImage: getGradientColor(),
							backgroundBlendMode: 'screen',
					  }
			"
		>
			<div
				v-if="!course.image"
				class="flex items-center justify-center text-white flex-1 font-extrabold my-auto px-5 text-center leading-6 h-full"
				:class="
					course.title.length > 32
						? 'text-lg'
						: course.title.length > 20
						? 'text-xl'
						: 'text-2xl'
				"
			>
				{{ course.title }}
			</div>
		</div>
		<div class="flex flex-col flex-auto p-4 border-x-2 border-b-2 rounded-b-md">
			<div class="flex items-center justify-between mb-2">
				<div v-if="course.lessons">
					<Tooltip :text="__('Lessons')">
						<span class="flex items-center">
							<BookOpen class="h-4 w-4 stroke-1.5 mr-1" />
							{{ course.lessons }}
						</span>
					</Tooltip>
				</div>

				<div v-if="course.enrollments">
					<Tooltip :text="__('Enrolled Students')">
						<span class="flex items-center">
							<Users class="h-4 w-4 stroke-1.5 mr-1" />
							{{ formatAmount(course.enrollments) }}
						</span>
					</Tooltip>
				</div>

				<div v-if="course.rating">
					<Tooltip :text="__('Average Rating')">
						<span class="flex items-center">
							<Star class="h-4 w-4 stroke-1.5 mr-1" />
							{{ course.rating }}
						</span>
					</Tooltip>
				</div>

				<Tooltip v-if="course.featured" :text="__('Featured')">
					<Award class="size-4 stroke-2 text-ink-amber-3" />
				</Tooltip>

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

			<div
				v-if="course.image"
				class="font-semibold leading-6"
				:class="course.title.length > 32 ? 'text-lg' : 'text-xl'"
			>
				{{ course.title }}
			</div>

			<div class="short-introduction text-sm">
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
					v-else-if="course.membership.progress"
					class="text-sm text-ink-gray-7 mt-2 mb-4"
				>
					{{ Math.ceil(course.membership.progress) }}% completed
				</div>
			</div>

			<div class="flex items-center justify-between mt-auto">
				<div></div>

				<div class="flex items-center space-x-2">
					<div v-if="course.paid_course" class="font-semibold">
						{{ course.price }}
					</div>

					<Tooltip
						v-if="course.paid_certificate || course.enable_certification"
						:text="__('Get Certified')"
					>
						<GraduationCap class="size-5 stroke-1.5 text-ink-gray-7" />
					</Tooltip>
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import { Award, BookOpen, CheckCircle, GraduationCap, Star, Users } from 'lucide-vue-next'
import { computed } from 'vue'
import { sessionStore } from '@/stores/session'
import { Badge, Tooltip } from 'frappe-ui'
import { formatAmount } from '@/utils'
import ProgressBar from '@/components/ProgressBar.vue'
import colors from '@/utils/frappe-ui-colors.json'

const { user } = sessionStore()

const props = defineProps({
	course: {
		type: Object,
		default: null,
	},
})

const getGradientColor = () => {
	let theme =
		localStorage.getItem('theme') == 'light' ? 'lightMode' : 'darkMode'
	let color = props.course.card_gradient?.toLowerCase() || 'blue'
	let colorMap = colors[theme][color]
	return `linear-gradient(to top right, black, ${colorMap[400]})`
}

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

.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
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
