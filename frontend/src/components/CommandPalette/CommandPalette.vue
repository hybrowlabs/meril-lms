<template>
	<Dialog v-model:open="show" size="2xl" bare>
		<template #default>
			<Dialog.Title as-child>
				<h2 class="sr-only">{{ __('Command palette') }}</h2>
			</Dialog.Title>
			<div class="text-base">
				<div class="flex items-center gap-x-2 ps-4.5 border-b">
					<span class="lucide-search size-4 text-ink-gray-4" />
					<input
						ref="inputRef"
						type="text"
						role="combobox"
						aria-expanded="true"
						aria-controls="command-palette-results"
						:placeholder="__('Search')"
						class="w-full border-none bg-transparent py-3 !ps-2 pe-4.5 text-base text-ink-gray-7 placeholder-ink-gray-4 focus:ring-0"
						@input="onInput"
						@keydown="onKeydown"
						v-model="query"
						autocomplete="off"
					/>
				</div>

				<div
					id="command-palette-results"
					class="max-h-96 overflow-auto mb-2"
					ref="resultsRef"
				>
					<div class="mt-5 space-y-5">
						<CommandPaletteGroup :list="groups" @select="run" />
					</div>
					<p
						v-if="showsEmptyState"
						class="px-4.5 py-2 text-ink-gray-5"
						role="status"
					>
						{{ __('No results found') }}
					</p>
				</div>

				<div
					class="flex items-center gap-x-5 w-full border-t py-2 text-sm text-ink-gray-7 px-4.5"
				>
					<div class="flex items-center gap-x-2">
						<span :class="chipClass">
							<span class="lucide-move-up size-3.5 text-ink-gray-7" />
						</span>
						<span :class="chipClass">
							<span class="lucide-move-down size-3.5 text-ink-gray-7" />
						</span>
						<span>
							{{ __('to navigate') }}
						</span>
					</div>
					<div class="flex items-center gap-x-2">
						<span :class="chipClass">
							<span class="lucide-corner-down-left size-3.5 text-ink-gray-7" />
						</span>
						<span>
							{{ __('to select') }}
						</span>
					</div>
					<div class="flex items-center gap-x-2">
						<span :class="[chipClass, 'px-1.5 text-xs text-ink-gray-7']">
							{{ __('esc') }}
						</span>
						<span>
							{{ __('to close') }}
						</span>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>
<script setup lang="ts">
import { createResource, debounce, Dialog } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpen, Briefcase, Users } from 'lucide-vue-next'
import CommandPaletteGroup from './CommandPaletteGroup.vue'
import type { PaletteGroup, PaletteItem, PaletteRoute } from './paletteTypes'
import { routeForSearchHit } from './paletteTypes'

const chipClass =
	'inline-flex size-5 shrink-0 items-center justify-center rounded-sm bg-surface-gray-2'

// Below this the palette keeps showing the jump-to list. The results pane used
// to take over at one character while the search only ran from three, so the
// dialog went blank for exactly the two keystrokes that start every search.
const MIN_QUERY_LENGTH = 2

const show = defineModel<boolean>({ required: true, default: false })
const router = useRouter()
const query = ref<string>('')
const searchResults = ref<PaletteGroup[]>([])
const inputRef = ref<HTMLInputElement | null>(null)
const resultsRef = ref<HTMLElement | null>(null)

// -1 is "the user has not arrowed yet", which is what lets the first ArrowDown
// land on the first row rather than the second.
const activeIndex = ref(-1)

// The query a response belongs to; a slower earlier response is dropped rather
// than allowed to land under whatever the user has typed since.
let requestedQuery = ''

const search = createResource({
	url: 'lms.command_palette.search_sqlite',
	makeParams: () => {
		requestedQuery = query.value
		return { query: query.value }
	},
	onSuccess(data: unknown) {
		if (requestedQuery !== query.value) return
		searchResults.value = toGroups(data)
	},
})

const isSearching = computed(() => query.value.length >= MIN_QUERY_LENGTH)

const groups = computed<PaletteGroup[]>(() => {
	const source = isSearching.value ? searchResults.value : jumpToOptions.value
	let index = 0
	return source.map((group) => ({
		title: group.title,
		items: group.items.map((item) => ({
			...item,
			isActive: index++ === activeIndex.value,
		})),
	}))
})

const flatItems = computed<PaletteItem[]>(() =>
	groups.value.flatMap((group) => group.items)
)

const showsEmptyState = computed(
	() => isSearching.value && !flatItems.value.length && !search.loading
)

const debouncedSearch = debounce(() => {
	if (isSearching.value) search.reload()
}, 300)

const onInput = () => {
	debouncedSearch()
}

/** Search hits whose doctype has no route are dropped, not pointed at a wrong page. */
const toGroups = (data: unknown): PaletteGroup[] => {
	if (!Array.isArray(data)) return []
	return data
		.map((group: any) => ({
			title: group.title,
			items: (group.items ?? [])
				.map((item: any) => {
					const route = routeForSearchHit(item.doctype, item.name)
					return route ? { ...item, route } : null
				})
				.filter(Boolean) as PaletteItem[],
		}))
		.filter((group) => group.items.length > 0)
}

watch(query, () => {
	activeIndex.value = -1
	if (!isSearching.value) searchResults.value = []
})

watch(show, () => {
	if (!show.value) {
		query.value = ''
		searchResults.value = []
		activeIndex.value = -1
	}
})

const onKeydown = (e: KeyboardEvent) => {
	if (e.key === 'ArrowDown') {
		e.preventDefault()
		moveActive(1)
	} else if (e.key === 'ArrowUp') {
		e.preventDefault()
		moveActive(-1)
	} else if (e.key === 'Enter') {
		e.preventDefault()
		// Enter with nothing arrowed to opens the top hit, which is what the
		// caret sitting in a search box implies.
		const item = flatItems.value[Math.max(activeIndex.value, 0)]
		if (item) run(item)
	} else if (e.key === 'Escape') {
		show.value = false
	}
}

const moveActive = (direction: number) => {
	const total = flatItems.value.length
	if (!total) return
	const next = activeIndex.value + direction
	if (next < 0) activeIndex.value = total - 1
	else if (next >= total) activeIndex.value = 0
	else activeIndex.value = next
	nextTick(scrollActiveItemIntoView)
}

const scrollActiveItemIntoView = () => {
	resultsRef.value
		?.querySelector('[data-palette-item][data-active="true"]')
		?.scrollIntoView({ block: 'nearest' })
}

const run = (item: PaletteItem) => {
	if (item.route) navigateTo(item.route)
}

const navigateTo = (route: PaletteRoute) => {
	show.value = false
	query.value = ''
	searchResults.value = []
	// push, not replace: reaching a course through the palette should still
	// leave the page you came from on the back stack.
	router.push({ name: route.name, params: route.params, query: route.query })
}

const jumpToOptions = ref<PaletteGroup[]>([
	{
		title: __('Jump to'),
		items: [
			{
				title: 'Courses',
				icon: BookOpen,
				route: { name: 'Courses' },
			},
			{
				title: 'Batches',
				icon: Users,
				route: { name: 'Batches' },
			},
			{
				title: 'Jobs',
				icon: Briefcase,
				route: { name: 'Jobs' },
			},
		],
	},
])
</script>
<style>
mark {
	background-color: theme('colors.amber.100');
	font-weight: 500;
}
</style>
