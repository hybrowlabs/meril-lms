<template>
	<div class="flex h-full items-center justify-center px-5 py-20">
		<div class="flex flex-col items-center gap-4">
			<div
				class="size-14 rounded-full bg-surface-gray-2 flex items-center justify-center"
			>
				<span class="lucide-lock-keyhole size-6 text-ink-gray-6" />
			</div>
			<div class="flex flex-col items-center gap-1">
				<div class="text-p-lg-medium text-ink-gray-8">
					{{ __('This lesson is locked') }}
				</div>
				<div class="text-center text-p-sm text-ink-gray-6 max-w-72">
					{{ __('Finish the earlier lessons to unlock this one.') }}
				</div>
			</div>
			<div v-if="redirect" class="flex flex-col items-center gap-2 w-52 mt-1">
				<div class="h-1 w-full rounded-full bg-surface-gray-3 overflow-hidden">
					<div
						class="h-full rounded-full bg-surface-gray-6 transition-[width] duration-1000 ease-linear"
						:style="{ width: `${(secondsLeft / seconds) * 100}%` }"
					/>
				</div>
				<div class="text-p-xs text-ink-gray-5 tabular-nums" aria-hidden="true">
					{{
						__('Taking you to your current lesson in {0}s').format(secondsLeft)
					}}
				</div>
			</div>
			<div class="sr-only" role="status">{{ announcement }}</div>
		</div>
	</div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
	redirect: {
		type: Boolean,
		default: true,
	},
	seconds: {
		type: Number,
		default: 3,
	},
})

const emit = defineEmits(['done'])

const secondsLeft = ref(props.seconds)
const announcement = ref('')
let timer = null
let announceTimer = null

const stop = () => {
	if (timer) {
		clearInterval(timer)
		timer = null
	}
	if (announceTimer) {
		clearTimeout(announceTimer)
		announceTimer = null
	}
}

// role="status" implies aria-atomic, so a per-second countdown queues one full
// polite announcement per tick and crowds out the sentence explaining the lock.
// The visible counter is hidden from AT and the reason is announced once.
//
// The region is rendered unconditionally, outside the redirect block, so it is
// already in the accessibility tree before it has content. Populating it in the
// same frame as its own insertion reads as initial content, which most screen
// readers do not announce at all, so the text lands a frame later.
const ANNOUNCE_DELAY = 100

const announce = () => {
	announcement.value = ''
	announceTimer = setTimeout(() => {
		announcement.value = __(
			'This lesson is locked. Taking you to your current lesson in {0} seconds.'
		).format(props.seconds)
	}, ANNOUNCE_DELAY)
}

// The bar drains rather than the page jumping on arrival, so the student reads why
// they were moved instead of landing on an unexplained lesson.
const start = () => {
	stop()
	secondsLeft.value = props.seconds
	announce()
	timer = setInterval(() => {
		secondsLeft.value -= 1
		if (secondsLeft.value > 0) return
		stop()
		emit('done')
	}, 1000)
}

watch(
	() => props.redirect,
	(redirect) => {
		if (redirect) start()
		else stop()
	},
	{ immediate: true }
)

onBeforeUnmount(stop)
</script>
