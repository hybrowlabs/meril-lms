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
						v-if="showsErrorState"
						class="px-4.5 py-2 text-ink-gray-5"
						role="status"
					>
						{{ __('Could not search just now. Try again.') }}
					</p>
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
						<span :class="[wideChipClass, 'text-xs text-ink-gray-7']">
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
import { Settings } from 'lucide-vue-next'
import { usersStore } from '@/stores/user'
import { useSettings } from '@/stores/settings'
// @ts-expect-error utils/index.js has no type declarations yet
import { getSidebarLinks } from '@/utils'
import CommandPaletteGroup from './CommandPaletteGroup.vue'
import type { PaletteGroup, PaletteItem, PaletteRoute } from './paletteTypes'
import { MODAL_FORM_ROUTES, routeForSearchHit } from './paletteTypes'
import {
	categoryById,
	visibleCategories,
	visibleNavTargets,
} from './categories'
import { openFormRoute } from '@/composables/useFormRoute'

const chipClass =
	'inline-flex size-5 shrink-0 items-center justify-center rounded-sm bg-surface-gray-2'

// `size-5` fixes a square, which crops a multi-letter key. Width grows instead.
const wideChipClass =
	'inline-flex h-5 min-w-5 w-auto shrink-0 items-center justify-center rounded-sm bg-surface-gray-2 px-1.5'

// Below this the palette keeps showing the jump-to list. The results pane used
// to take over at one character while the search only ran from three, so the
// dialog went blank for exactly the two keystrokes that start every search.
const MIN_QUERY_LENGTH = 2

const show = defineModel<boolean>({ required: true, default: false })
const router = useRouter()
const { userResource } = usersStore()
const settingsStore = useSettings()

// The category the search is narrowed to, or null at the root.
const scope = ref<string | null>(null)
const query = ref<string>('')
const searchResults = ref<PaletteGroup[]>([])
const inputRef = ref<HTMLInputElement | null>(null)
const resultsRef = ref<HTMLElement | null>(null)

// -1 is "the user has not arrowed yet", which is what lets the first ArrowDown
// land on the first row rather than the second.
const activeIndex = ref(-1)

// One token per request. Comparing against the current query instead would miss
// two requests for *different* queries overlapping and landing out of order:
// frappe-ui never aborts the one already in flight.
let searchToken = 0
const searchFailed = ref(false)

// Whether a search for the current typing run has come back at all. Tying the
// empty message to `search.loading` instead made it blink off and on with every
// keystroke — the results area collapsed to nothing and the dialog resized on
// each letter, which read as the palette tearing itself apart.
const hasSettled = ref(false)

const search = createResource({ url: 'lms.command_palette.search_sqlite' })

const runSearch = async () => {
	const token = ++searchToken
	const params = scope.value
		? { query: query.value, category: scope.value }
		: { query: query.value }
	try {
		const data = await search.submit(params)
		if (token !== searchToken) return
		searchResults.value = toGroups(data)
		searchFailed.value = false
		hasSettled.value = true
	} catch (error) {
		if (token !== searchToken) return
		searchResults.value = []
		searchFailed.value = true
		hasSettled.value = true
	}
}

const isSearching = computed(() => query.value.length >= MIN_QUERY_LENGTH)

/** The same test Programs.vue gates its own card click on. */
const routeContext = computed(() => ({
	canEditPrograms:
		!window.read_only_mode &&
		Boolean(
			userResource.data?.is_moderator || userResource.data?.is_instructor
		),
}))

/**
 * Every row the palette offers by name, in the form it takes while searching: a
 * category resolves to its own list page here rather than drilling in, because
 * typing "cour" means "take me to Courses". Account rows belong here too —
 * Settings lived only in the pre-search list, so typing its name emptied the
 * palette and reported that nothing matched.
 */
const searchableSections = computed<PaletteItem[]>(() => {
	const links = getSidebarLinks()
	return [
		...visibleCategories(links).map((entry) => ({
			title: __(entry.label),
			icon: entry.icon,
			route: { name: entry.listRoute },
		})),
		...visibleNavTargets(links).map((entry) => ({
			title: __(entry.label),
			icon: entry.icon,
			route: { name: entry.route },
		})),
		...accountItems.value,
	]
})

/** Sections whose name the query is starting to spell. */
const matchingSections = computed<PaletteItem[]>(() => {
	const term = query.value.trim().toLowerCase()
	if (!term || scope.value) return []
	return searchableSections.value.filter((section) =>
		String(section.title).toLowerCase().startsWith(term)
	)
})

const groups = computed<PaletteGroup[]>(() => {
	const searched = isSearching.value
	const sections = matchingSections.value
	const source = searched
		? sections.length
			? [{ title: __('Jump to'), items: sections }, ...searchResults.value]
			: searchResults.value
		: browseGroups.value
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
	() =>
		isSearching.value &&
		!flatItems.value.length &&
		hasSettled.value &&
		!searchFailed.value
)

/** A failed request is not an empty result set, and saying so hides an outage. */
const showsErrorState = computed(
	() => searchFailed.value && hasSettled.value && !flatItems.value.length
)

const debouncedSearch = debounce(() => {
	if (isSearching.value) runSearch()
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
					const route = routeForSearchHit(
						item.doctype,
						item.name,
						routeContext.value
					)
					return route ? { ...item, route } : null
				})
				.filter(Boolean) as PaletteItem[],
		}))
		.filter((group) => group.items.length > 0)
}

watch(query, () => {
	activeIndex.value = -1
	if (!isSearching.value) {
		searchResults.value = []
		hasSettled.value = false
		searchFailed.value = false
	}
})

watch(show, () => {
	if (!show.value) {
		query.value = ''
		searchResults.value = []
		activeIndex.value = -1
		// Without this the palette reopened still narrowed to whatever category
		// was last opened, with no visible sign that it was filtering.
		scope.value = null
		searchFailed.value = false
		hasSettled.value = false
		searchToken += 1
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
		if (scope.value) {
			// The dialog closes on Escape at the document level unless this is
			// stopped, which made backing out one level impossible.
			e.preventDefault()
			e.stopPropagation()
			leaveScope()
		} else show.value = false
	} else if (e.key === 'Backspace' && !query.value && scope.value) {
		// Only on an empty query, so Backspace stays an ordinary edit while there
		// is still something to delete.
		e.preventDefault()
		leaveScope()
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
	const active = resultsRef.value?.querySelector<HTMLElement>(
		'[data-palette-item][data-active="true"]'
	)
	if (!active) return
	// Scrolling the row alone left its heading clipped above the fold, so arrowing
	// up to the top row of a group hid which group it belonged to.
	const group = active.closest<HTMLElement>('[data-palette-group]')
	const isFirstOfGroup = group?.querySelector('[data-palette-item]') === active
	;(isFirstOfGroup && group ? group : active).scrollIntoView({
		block: 'nearest',
	})
}

const run = (item: PaletteItem) => {
	if (item.category) enterScope(item.category)
	else if (item.perform) {
		show.value = false
		item.perform()
	} else if (item.route) navigateTo(item.route)
}

const enterScope = (category: string) => {
	scope.value = category
	query.value = ''
	searchResults.value = []
	activeIndex.value = -1
	focusInput()
}

const leaveScope = () => {
	scope.value = null
	query.value = ''
	searchResults.value = []
	activeIndex.value = -1
	focusInput()
}

/** Clicking a row destroys that button and the keys are bound to the input, so
 * without this the palette stopped responding to the keyboard after a click. */
const focusInput = () => {
	nextTick(() => inputRef.value?.focus())
}

const navigateTo = (route: PaletteRoute) => {
	show.value = false
	query.value = ''
	searchResults.value = []
	const to = { name: route.name, params: route.params, query: route.query }
	// push, not replace: reaching a course through the palette should still
	// leave the page you came from on the back stack. A form route needs the
	// marker openFormRoute stamps, or closing the modal ejects the user instead
	// of returning them to the list underneath it.
	if (MODAL_FORM_ROUTES.has(route.name)) openFormRoute(router, to)
	else router.push(to)
}

const scopedCategory = computed(() => categoryById(scope.value))

/** What the palette shows before a search: the categories, or, once inside one,
 * the way out to that category's own page. */
const browseGroups = computed<PaletteGroup[]>(() => {
	const category = scopedCategory.value
	if (category) {
		return [
			{
				title: __(category.label),
				items: [
					{
						title: __('View all {0}').format(__(category.label)),
						icon: category.icon,
						route: { name: category.listRoute },
					},
				],
			},
		]
	}

	const links = getSidebarLinks()
	const groups: PaletteGroup[] = [
		{
			title: __('Jump to'),
			items: [
				...visibleCategories(links).map((entry) => ({
					title: __(entry.label),
					icon: entry.icon,
					category: entry.id,
				})),
				// No records to narrow to, so these navigate rather than drill in.
				...visibleNavTargets(links).map((entry) => ({
					title: __(entry.label),
					icon: entry.icon,
					route: { name: entry.route },
				})),
			],
		},
	]

	const account = accountItems.value
	if (account.length) groups.push({ title: __('Account'), items: account })
	return groups
})

/** Settings is a dialog owned by the desktop sidebar and open to moderators
 * only; on a phone nothing listens to the flag, so the row would do nothing. */
const accountItems = computed<PaletteItem[]>(() => {
	if (!userResource.data?.is_moderator || !settingsStore.isSettingsMounted) {
		return []
	}
	return [
		{
			title: __('Settings'),
			icon: Settings,
			perform: () => {
				settingsStore.isSettingsOpen = true
			},
		},
	]
})
</script>
<style>
mark {
	background-color: theme('colors.amber.100');
	font-weight: 500;
}
</style>
