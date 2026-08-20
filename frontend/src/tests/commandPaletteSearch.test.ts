/**
 * Searching, keyboard navigation and routing in the command palette.
 *
 * Every case here is a bug the palette shipped with: arrowing through search
 * results threw `Cannot set properties of undefined` because no result was ever
 * the active one, Enter therefore did nothing, every non-course hit routed into
 * the batch page, and one typed character blanked the dialog because the results
 * pane took over before the search was allowed to run.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const resource = {
	next: null as unknown,
	params: null as any,
	submit: vi.fn(async (params: any) => {
		resource.params = params
		return resource.next
	}),
}

vi.mock('frappe-ui', () => ({
	createResource: () => resource,
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

// The palette reads roles to decide which category rows to show, which page a
// program hit opens, and — with the settings store — whether Settings can act.
const user = { data: {} as Record<string, unknown> }
vi.mock('@/stores/user', () => ({ usersStore: () => ({ userResource: user }) }))
vi.mock('@/utils', () => ({
	getSidebarLinks: () => [
		{
			items: [
				{ to: 'Courses' },
				{ to: 'Batches' },
				{ to: 'Programs' },
				{ to: 'Jobs' },
				{ to: 'Quizzes' },
				{ to: 'Assignments' },
			],
		},
	],
}))

vi.mock('@/stores/settings', () => ({
	useSettings: () => ({
		isSettingsOpen: false,
		isSettingsMounted: true,
		// The palette filters its rows by these flags as well as by the sidebar.
		sidebarSettings: { data: null },
		loadSidebarSettings: vi.fn(async () => null),
	}),
}))

vi.mock('@/components/CommandPalette/CommandPaletteGroup.vue', () => ({
	default: { name: 'PaletteGroup', props: ['list'], template: `<div />` },
}))

// Mirrors src/translation.js: a message with {0} placeholders returns an object
// carrying `format`, not a string. A plain identity stub would let a real
// `.format is not a function` crash pass.
vi.stubGlobal('__', (message: string) => {
	if (!/{\d+}/.test(message)) return message
	return {
		format: (...args: string[]) =>
			message.replace(
				/{(\d+)}/g,
				(match, index) => args[Number(index)] ?? match
			),
	}
})

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
		global: { mocks: { __: (globalThis as any).__ } },
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

beforeEach(() => {
	user.data = { is_moderator: true }
	push.mockClear()
	// The outage case swaps submit() for one that throws, and never puts it
	// back — every later search in the file inherited the failure.
	resource.submit = vi.fn(async (params: any) => {
		resource.params = params
		return resource.next
	})
})

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
		{
			item: { doctype: 'LMS Quiz', name: 'quiz-1', title: 'Week 1 Quiz' },
			route: 'QuizForm',
			params: { quizID: 'quiz-1' },
		},
		{
			item: { doctype: 'LMS Assignment', name: 'ASG-00001', title: 'Essay' },
			route: 'AssignmentForm',
			params: { assignmentID: 'ASG-00001' },
		},
		{
			item: { doctype: 'LMS Program', name: 'Bootcamp', title: 'Bootcamp' },
			route: 'ProgramForm',
			params: { programName: 'Bootcamp' },
		},
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

	it('offers the matching section page above the hits', async () => {
		const wrapper = build()
		await search(wrapper, 'cour')

		const first = rows(wrapper)[0]
		expect(first.title).toBe('Courses')
		expect(first.route).toEqual(expect.objectContaining({ name: 'Courses' }))
	})

	it('does not offer a section page that the query does not match', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')

		expect(rows(wrapper).map((item) => item.title)).not.toContain('Courses')
	})

	// The guard used to compare against the current query, which cannot tell an
	// older request from a newer one when both are for queries since replaced.
	it('ignores a response that a newer request has already overtaken', async () => {
		const wrapper = build()
		const input = wrapper.find('input')

		let releaseFirst: (value: unknown) => void = () => {}
		const slow = new Promise((resolve) => (releaseFirst = resolve))
		resource.submit = vi.fn(async (params: any) =>
			params.query === 'kub' ? slow : RESULTS
		) as any

		await input.setValue('kub')
		await input.trigger('input')
		await input.setValue('kube')
		await input.trigger('input')
		await nextTick()
		await nextTick()

		const afterNewer = rows(wrapper).map((item: any) => item.title)

		releaseFirst([
			{ title: 'Courses', items: [{ ...COURSE, title: 'Stale hit' }] },
		])
		await nextTick()
		await nextTick()

		expect(rows(wrapper).map((item: any) => item.title)).toEqual(afterNewer)
		expect(rows(wrapper).map((item: any) => item.title)).not.toContain(
			'Stale hit'
		)
	})

	it('says a failed search failed rather than that nothing matched', async () => {
		const wrapper = build()
		resource.submit = vi.fn(async () => {
			throw new Error('500')
		}) as any

		const input = wrapper.find('input')
		await input.setValue('kubernetes')
		await input.trigger('input')
		await nextTick()
		await nextTick()

		expect(wrapper.text()).toContain('Could not search')
		expect(wrapper.text()).not.toContain('No results found')
	})

	it('replaces rather than appends when a second response lands', async () => {
		const wrapper = build()
		await search(wrapper, 'kubernetes')
		await search(wrapper, 'kubernetes again')

		const titles = rows(wrapper).map((item) => item.title)
		expect(new Set(titles).size).toBe(titles.length)
	})
})

/**
 * Where a program hit lands depends on who is searching. Programs.vue renders a
 * student the read-only ProgramDetail page, but gives a moderator or instructor
 * a list whose cards open the ProgramForm modal — so sending everyone to
 * ProgramDetail dropped an author onto the page they cannot edit from.
 */
describe('command palette program routing', () => {
	const PROGRAM = {
		doctype: 'LMS Program',
		name: 'Bootcamp',
		title: 'Bootcamp',
	}

	it.each([
		{ who: 'moderator', data: { is_moderator: true }, route: 'ProgramForm' },
		{ who: 'instructor', data: { is_instructor: true }, route: 'ProgramForm' },
		{ who: 'student', data: { is_student: true }, route: 'ProgramDetail' },
		{ who: 'evaluator', data: { is_evaluator: true }, route: 'ProgramDetail' },
	])('sends a $who to $route', async ({ data, route }) => {
		user.data = { ...data }
		const wrapper = build()
		await search(wrapper, 'bootcamp', [{ title: 'Results', items: [PROGRAM] }])

		expect(rows(wrapper)[0].route).toEqual(
			expect.objectContaining({
				name: route,
				params: { programName: 'Bootcamp' },
			})
		)
	})

	// read_only_mode is what Programs.vue gates its own card click on, so the
	// palette must not offer an edit route the page itself would refuse.
	it('sends a moderator to ProgramDetail in read-only mode', async () => {
		;(window as any).read_only_mode = true
		try {
			const wrapper = build()
			await search(wrapper, 'bootcamp', [
				{ title: 'Results', items: [PROGRAM] },
			])
			expect(rows(wrapper)[0].route).toEqual(
				expect.objectContaining({ name: 'ProgramDetail' })
			)
		} finally {
			;(window as any).read_only_mode = false
		}
	})
})

/**
 * ProgramForm and AssignmentForm are child routes that render as a modal over
 * their list page, and both pages open them through openFormRoute so that Back
 * closes the modal. A bare push leaves no marker, which degrades the form's
 * close from a pop into a replace.
 */
describe('command palette form routes', () => {
	it.each([
		{
			who: 'a program',
			item: { doctype: 'LMS Program', name: 'Bootcamp', title: 'Bootcamp' },
		},
		{
			who: 'an assignment',
			item: { doctype: 'LMS Assignment', name: 'ASG-1', title: 'Essay' },
		},
	])('marks the history entry when opening $who', async ({ item }) => {
		const wrapper = build()
		await search(wrapper, 'thing', [{ title: 'Results', items: [item] }])
		await press(wrapper, 'ArrowDown')
		await press(wrapper, 'Enter')
		await nextTick()

		expect(push).toHaveBeenCalledWith(
			expect.objectContaining({ state: { lmsFormEntry: true } })
		)
	})

	// QuizForm is a top-level route, and the quiz list reaches it with a plain
	// row link — there is no modal to keep on the stack.
	it('leaves a quiz hit as an ordinary push', async () => {
		const wrapper = build()
		await search(wrapper, 'week', [
			{
				title: 'Results',
				items: [{ doctype: 'LMS Quiz', name: 'quiz-1', title: 'Week 1' }],
			},
		])
		await press(wrapper, 'ArrowDown')
		await press(wrapper, 'Enter')
		await nextTick()

		expect(push).toHaveBeenCalledWith(
			expect.not.objectContaining({ state: expect.anything() })
		)
	})
})
