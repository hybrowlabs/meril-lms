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
				<div
					class="text-p-xs text-ink-gray-5 tabular-nums"
					role="status"
					aria-live="polite"
				>
					{{
						__('Taking you to your current lesson in {0}s').format(secondsLeft)
					}}
				</div>
			</div>
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
let timer = null

const stop = () => {
	if (timer) {
		clearInterval(timer)
		timer = null
	}
}

// The bar drains rather than the page jumping on arrival, so the student reads why
// they were moved instead of landing on an unexplained lesson.
const start = () => {
	stop()
	secondsLeft.value = props.seconds
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
