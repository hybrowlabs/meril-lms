<template>
	<Dialog
		v-if="!isMobile"
		:open="true"
		:title="title"
		:size="size"
		@update:open="onDialogToggle"
	>
		<template #title>
			<div class="flex flex-1 items-center justify-between gap-2">
				<h3 class="text-2xl-semibold leading-6 text-ink-gray-8">
					{{ title }}
				</h3>
				<slot name="header-action" />
			</div>
		</template>
		<template #default>
			<slot />
		</template>
		<template #actions>
			<slot name="actions" />
		</template>
	</Dialog>

	<Teleport v-else to="body">
		<Transition
			appear
			:enter-active-class="
				reduceMotion ? '' : 'transition duration-200 ease-out'
			"
			:enter-from-class="reduceMotion ? '' : 'translate-y-4 opacity-0'"
			:enter-to-class="reduceMotion ? '' : 'translate-y-0 opacity-100'"
		>
			<div
				ref="pageRef"
				data-testid="form-shell-page"
				role="dialog"
				aria-modal="true"
				:aria-labelledby="titleId"
				tabindex="-1"
				class="fixed inset-0 z-40 flex flex-col bg-surface-base"
			>
				<header class="header-frame gap-1 pt-safe-0">
					<button
						type="button"
						data-testid="form-shell-back"
						:aria-label="__('Back')"
						class="-ms-3 shrink-0 rounded p-1.5 text-ink-gray-9 transition-colors hover:bg-surface-gray-2"
						@click="emit('close')"
					>
						<span class="lucide-chevron-left size-4 block" />
					</button>
					<p :id="titleId" class="truncate text-lg-medium text-ink-gray-9">
						{{ title }}
					</p>
					<div
						data-testid="form-shell-header-actions"
						class="ms-auto flex shrink-0 items-center gap-2"
					>
						<slot name="header-action" />
						<slot name="actions" />
					</div>
				</header>

				<div
					data-testid="form-shell-body"
					class="flex-1 overflow-y-auto overscroll-contain px-5 py-4"
				>
					<slot />
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
<script setup lang="ts">
// The title is a <p>, not an <h1>: the list page behind this Teleport keeps its
// own <h1> in the a11y tree, and aria-labelledby on the dialog root does the
// labelling.
//
// `actions` renders in the header on mobile and in the Dialog's footer on
// desktop. Pass HeaderButton, never a bare frappe-ui Button — Button.vue only
// applies square icon-button sizing when the slot's vnode type name starts with
// `lucide-`, which a plain `<span class="lucide-save">` does not satisfy.
import { Dialog } from 'frappe-ui'
import type { DialogSize } from 'frappe-ui'
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'
import { useEventListener, useMediaQuery } from '@vueuse/core'
import { useScreenSize } from '@/utils/composables'

// The transition lives INSIDE the Teleport, wrapping the teleported node —
// never on <router-view>. The comment below on the Teleport spells out why: a
// transform on any ancestor establishes a containing block for `fixed`, which
// would drop this overlay back into main#scrollContainer and reproduce the
// list-then-form-below-it bug the component exists to fix. A page transition is
// exactly the ancestor transform that comment anticipated.
//
// Enter only. A leave animation needs the page to outlive its own route change,
// which means deferring close() until the animation ends, and browser-back
// would still hard-cut regardless.
const reduceMotion = useMediaQuery('(prefers-reduced-motion: reduce)')

withDefaults(defineProps<{ title: string; size?: DialogSize }>(), {
	size: '3xl',
})

const emit = defineEmits<{ close: [] }>()
const { isMobile } = useScreenSize()
const titleId = useId()
const pageRef = ref<HTMLElement | null>(null)

// The desktop Dialog owns its own dismiss affordances (Escape, backdrop, the
// header X). Route the close back out rather than letting it manage state we
// do not own — the route is the single source of truth for whether we are open.
const onDialogToggle = (open: boolean): void => {
	if (!open) emit('close')
}

// Mirrors BottomSheet.vue's overlay contract:
// - Teleport to body is the load-bearing part, not just a11y hygiene. `fixed
//   inset-0` only escapes to the viewport today because no ancestor
//   establishes a containing block for `fixed`. The moment any layout
//   ancestor gains a transform/filter/will-change (a page-transition being
//   the obvious future candidate), the overlay would silently reparent back
//   into main#scrollContainer and reproduce the exact list-then-form-below-it
//   bug this component exists to fix. Teleporting past that ancestor removes
//   the whole class of failure.
// - role="dialog" + aria-modal, matching BottomSheet.vue:16-17.
// - Escape closes, matching BottomSheet.vue's useEventListener(document,
//   'keydown', ...) at :83-84. Guarded on isMobile so it never double-fires
//   alongside the desktop Dialog's own (frappe-ui-internal) Escape handling.
//
// Tab is trapped for a reason that only became urgent when the actions moved
// into the header. `aria-modal="true"` tells a screen reader the list page
// behind this Teleport does not exist, but nothing was stopping Tab from
// walking into it — the page is last in <body>, so Tab off its final stop
// wrapped round to the list. While Save/Delete sat in the footer they were
// that final stop, so the ordinary path (last field -> Tab -> Save) never hit
// the leak. With the footer gone, the last field IS the last stop and the very
// next Tab lands in content the user was just told is not there. The cycle
// below is the fix; without it, removing the footer is a regression.
const FOCUSABLE =
	'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

useEventListener(document, 'keydown', (e: KeyboardEvent) => {
	if (!isMobile.value) return
	if (e.key === 'Escape') {
		emit('close')
		return
	}
	if (e.key !== 'Tab' || !pageRef.value) return
	const stops = Array.from(
		pageRef.value.querySelectorAll<HTMLElement>(FOCUSABLE)
	).filter((el) => !el.closest('[hidden]'))
	if (stops.length === 0) return
	const first = stops[0]
	const last = stops[stops.length - 1]
	// pageRef itself is the mount-time focus holder (tabindex="-1"), so a
	// Shift+Tab from there has to wrap to the end rather than escape upwards.
	if (
		e.shiftKey &&
		(document.activeElement === first ||
			document.activeElement === pageRef.value)
	) {
		e.preventDefault()
		last.focus()
	} else if (!e.shiftKey && document.activeElement === last) {
		e.preventDefault()
		first.focus()
	}
})

// FormShell IS the routed page, so its mount/unmount already line up with
// open/close — no separate isMobile watcher needed. Move focus in so a
// screen-reader user hears the dialog announced, and restore it to whatever
// had focus before, so closing doesn't strand focus on <body>.
let previouslyFocused: HTMLElement | null = null
onMounted(() => {
	if (isMobile.value) {
		previouslyFocused = document.activeElement as HTMLElement | null
		pageRef.value?.focus()
	}
})
onBeforeUnmount(() => {
	if (isMobile.value) previouslyFocused?.focus()
})
</script>
