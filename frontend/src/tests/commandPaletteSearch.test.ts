/**
 * Searching, keyboard navigation and routing in the command palette.
 *
 * Every case here is a bug the palette shipped with: arrowing through search
 * results threw `Cannot set properties of undefined` because no result was ever
 * the active one, Enter therefore did nothing, every non-course hit routed into
 * the batch page, and one typed character blanked the dialog because the results
 * pane took over before the search was allowed to run.
 */
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const resource = {
	data: null as unknown,
	next: null as unknown,
	params: null as unknown,
	options: null as any,
	reload: vi.fn(),
}

vi.mock('frappe-ui', () => ({
	createResource: (options: any) => {
		resource.options = options
		resource.reload = vi.fn(() => {
			resource.params = options.makeParams?.()
			resource.data = resource.next
			options.onSuccess?.(resource.data)
		})
		return resource
	},
	debounce: (fn: (...args: unknown[]) => void) => fn,
	Dialog: Object.assign(
		{
			props: ['open', 'size', 'bare'],
			template: `<div><slot /></div>`,
		},
		{ Title: { template: `<div><slot /></div>` } }
	),
}))

const push = vi.fn()
vi.mock('vue-router', () => ({
	useRouter: () => ({ push, replace: vi.fn() }),
}))

vi.mock('@/components/CommandPalette/CommandPaletteGroup.vue', () => ({
	default: { name: 'PaletteGroup', props: ['list'], template: `<div />` },
}))

// Called from `<script setup>` as well as the template, so it has to be global.
// None of the palette's strings take `{0}` placeholders, which is why the plain
// identity stub is faithful here and would not be elsewhere.
vi.stubGlobal('__', (text: string) => text)

import CommandPalette from '@/components/CommandPalette/CommandPalette.vue'

const COURSE = {
	doctype: 'LMS Course',
	name: 'kubernetes-in-practice',
	title: 'Kubernetes in Practice',
}
const JOB = {
	doctype: 'Job Opportunity',
	name: 'JOB-0001',
	title: 'Backend Engineer',
}
const BATCH = {
	doctype: 'LMS Batch',
	name: 'batch-01',
	title: 'Autumn Batch',
}

const RESULTS = [
	{ title: 'Courses', items: [COURSE] },
	{ title: 'Batches', items: [BATCH] },
	{ title: 'Job Opportunities', items: [JOB] },
]

function build() {
	return mount(CommandPalette, {
		props: { modelValue: true },
		global: { mocks: { __: (text: string) => text } },
	})
}

/** Types `term`, letting the (synchronously mocked) debounce fire the search. */
async function search(
	wrapper: ReturnType<typeof build>,
	term: string,
	data: unknown = RESULTS
) {
	resource.next = data
	const input = wrapper.find('input')
	await input.setValue(term)
	await input.trigger('input')
	await nextTick()
	await nextTick()
}

function rows(wrapper: ReturnType<typeof build>) {
	const list = wrapper
		.findComponent({ name: 'PaletteGroup' })
		.props('list') as any[]
	return list.flatMap((group) => group.items)
}

function press(wrapper: ReturnType<typeof build>, key: string) {
	return wrapper.find('input').trigger('keydown', { key })
}

describe('command palette search', () => {
	it('activates the first result when the user arrows down', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')

		await press(wrapper, 'ArrowDown')

		const active = rows(wrapper).filter((item) => item.isActive)
		expect(active).toHaveLength(1)
		expect(active[0].title).toBe(COURSE.title)
	})

	it('opens the active result on Enter', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')

		await press(wrapper, 'ArrowDown')
		await press(wrapper, 'Enter')

		expect(push).toHaveBeenCalledWith(
			expect.objectContaining({
				name: 'CourseDetail',
				params: { courseName: COURSE.name },
			})
		)
	})

	it('wraps from the last result back to the first', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')

		for (let i = 0; i < RESULTS.length; i++) await press(wrapper, 'ArrowDown')
		await press(wrapper, 'ArrowDown')

		expect(rows(wrapper).findIndex((item) => item.isActive)).toBe(0)
	})

	it('survives arrowing through an empty result set', async () => {
		const wrapper = build()
		await search(wrapper, 'nothing matches this', [])

		await expect(press(wrapper, 'ArrowDown')).resolves.not.toThrow()
		await expect(press(wrapper, 'ArrowUp')).resolves.not.toThrow()
		expect(rows(wrapper)).toHaveLength(0)
	})

	// Every doctype but LMS Course used to fall through to the batch route, so a
	// job hit navigated to /batches/JOB-0001.
	it.each([
		{
			item: COURSE,
			route: 'CourseDetail',
			params: { courseName: COURSE.name },
		},
		{ item: BATCH, route: 'BatchDetail', params: { batchName: BATCH.name } },
		{ item: JOB, route: 'JobDetail', params: { job: JOB.name } },
	])(
		'routes a $item.doctype hit to $route',
		async ({ item, route, params }) => {
			const wrapper = build()
			await search(wrapper, 'engineer', [{ title: 'Results', items: [item] }])

			const row = rows(wrapper)[0]
			expect(row.route).toEqual(
				expect.objectContaining({ name: route, params })
			)
		}
	)

	it('keeps showing the jump-to list while the query is too short to search', async () => {
		const wrapper = build()
		await search(wrapper, 'k')

		expect(rows(wrapper).length).toBeGreaterThan(0)
	})

	it('replaces rather than appends when a second response lands', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')
		await search(wrapper, 'kubernetes again')

		const titles = rows(wrapper).map((item) => item.title)
		expect(new Set(titles).size).toBe(titles.length)
	})
})
