/**
 * Lesson.vue is the heaviest page in the app (1300+ lines): a socket
 * subscription, an EditorJS instance, plyr video tracking, two Pinia stores
 * and a dozen child components. Every dependency below is stubbed so the
 * mount exercises the REAL `canGoNext` computed, the REAL `goNext` /
 * `switchLesson` / `setupLesson` / `goToLessonNumber` handlers, and the REAL
 * socket callback registered in onMounted -- not a hand-rolled restatement of
 * any of them.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'

const pushMock = vi.hoisted(() => vi.fn())
const replaceMock = vi.hoisted(() => vi.fn())
const socketOnMock = vi.hoisted(() => vi.fn())
const socketOffMock = vi.hoisted(() => vi.fn())
const created = vi.hoisted(() => ({ list: [] as any[] }))
const stub = vi.hoisted(() => (name: string) => ({
	name,
	template: `<div><slot /></div>`,
}))

vi.mock('vue-router', () => ({
	useRoute: () => ({
		params: { chapterNumber: '1', lessonNumber: '1' },
		query: {},
	}),
	useRouter: () => ({ push: pushMock, replace: replaceMock }),
}))

vi.mock('frappe-ui', async () => {
	const { reactive } = await import('vue')
	const passthrough = (name: string) => ({
		name,
		template: `<div><slot name="prefix" /><slot name="icon" /><slot /><slot name="suffix" /></div>`,
	})
	return {
		createResource: (config: any) => {
			const resource: any = reactive({
				data: null,
				loading: false,
				_config: config,
				submit: vi.fn((_params: any, handlers: any) => {
					handlers?.onSuccess?.(resource.data)
					return Promise.resolve()
				}),
				reload: vi.fn(),
				fetch: vi.fn(),
			})
			created.list.push(resource)
			return resource
		},
		createListResource: () =>
			reactive({
				data: [],
				loading: false,
				update: vi.fn(),
				reload: vi.fn(),
				fetch: vi.fn(),
			}),
		call: vi.fn(() => Promise.resolve()),
		usePageMeta: vi.fn(),
		toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
		Badge: passthrough('Badge'),
		Button: {
			name: 'Button',
			template: `<button><slot name="prefix" /><slot name="icon" /><slot /><slot name="suffix" /></button>`,
		},
		TabButtons: passthrough('TabButtons'),
		Tooltip: { name: 'Tooltip', template: `<span><slot /></span>` },
	}
})

vi.mock('@editorjs/editorjs', () => ({
	default: class {
		isReady = Promise.resolve()
		destroy = vi.fn()
	},
}))

vi.mock('@/utils', () => ({
	getEditorTools: () => ({}),
	enablePlyr: () => Promise.resolve([]),
	highlightText: vi.fn(),
	sanitizeEditorJs: (x: any) => x,
}))

vi.mock('@/stores/session', () => ({
	sessionStore: () => ({ brand: {} }),
}))
vi.mock('@/stores/sidebar', () => ({
	useSidebar: () => ({ isSidebarCollapsed: false }),
}))
vi.mock('@/stores/settings', () => ({
	useSettings: () => ({
		settings: { data: {}, promise: Promise.resolve() },
	}),
}))

vi.mock('@/components/LessonContent.vue', () => ({
	default: stub('LessonContent'),
}))
vi.mock('@/components/CourseInstructors.vue', () => ({
	default: stub('CourseInstructors'),
}))
vi.mock('@/components/ProgressBar.vue', () => ({
	default: stub('ProgressBar'),
}))
vi.mock('@/components/Discussions.vue', () => ({
	default: stub('Discussions'),
}))
vi.mock('@/components/CertificationLinks.vue', () => ({
	default: stub('CertificationLinks'),
}))
vi.mock('@/components/CourseOutline.vue', () => ({
	default: stub('CourseOutline'),
}))
vi.mock('@/components/StudentLessonSidebar.vue', () => ({
	default: stub('StudentLessonSidebar'),
}))
vi.mock('@/components/BottomSheet.vue', () => ({
	default: stub('BottomSheet'),
}))
vi.mock('@/components/Layouts/PageHeader.vue', () => ({
	default: stub('PageHeader'),
}))
vi.mock('@/components/HeaderButton.vue', () => ({
	default: stub('HeaderButton'),
}))
vi.mock('@/components/UserAvatar.vue', () => ({
	default: stub('UserAvatar'),
}))
vi.mock('@/components/Notes/Notes.vue', () => ({ default: stub('Notes') }))
vi.mock('@/components/Notes/InlineLessonMenu.vue', () => ({
	default: stub('InlineLessonMenu'),
}))

vi.stubGlobal('__', (s: string) => s)

import Lesson from '@/pages/Lesson.vue'

const findResource = (url: string) =>
	created.list.find((resource) => resource._config.url === url)

async function mountLesson(
	props: { chapterNumber: string; lessonNumber: string } = {
		chapterNumber: '1',
		lessonNumber: '1',
	}
) {
	const wrapper = mount(Lesson, {
		props: { courseName: 'COURSE-1', ...props },
		global: {
			mocks: { __: (s: string) => s },
			provide: {
				$user: { data: { name: 'student@example.com' } },
				$socket: { on: socketOnMock, off: socketOffMock },
			},
			stubs: {
				teleport: true,
				'router-link': { template: '<a><slot /></a>' },
			},
		},
	})
	await flushPromises()
	return wrapper
}

const baseLesson = {
	name: 'L1',
	title: 'Lesson 1',
	course_title: 'Course 1',
	chapter_title: 'Chapter 1',
	prev: null,
	next: '1.2',
	instructors: [],
}

let wrapper: VueWrapper

beforeEach(() => {
	created.list.length = 0
	pushMock.mockReset()
	replaceMock.mockReset()
	socketOnMock.mockReset()
	socketOffMock.mockReset()
})

afterEach(() => {
	wrapper?.unmount()
})

describe('Lesson.vue Next affordance follows canGoNext', () => {
	it('hides the Next button when the following lesson is locked', async () => {
		wrapper = await mountLesson()
		findResource('lms.lms.utils.get_course_outline').data = [
			{
				name: 'CH-1',
				lessons: [
					{ name: 'L1', number: '1-1', locked: 0 },
					{ name: 'L2', number: '1-2', locked: 1 },
				],
			},
		]
		findResource('lms.lms.utils.get_lesson').data = { ...baseLesson }
		await flushPromises()

		expect((wrapper.vm as any).canGoNext).toBe(false)
		expect(wrapper.text()).not.toContain('Next')
	})

	it('shows the Next button when the following lesson is unlocked', async () => {
		wrapper = await mountLesson()
		findResource('lms.lms.utils.get_course_outline').data = [
			{
				name: 'CH-1',
				lessons: [
					{ name: 'L1', number: '1-1', locked: 0 },
					{ name: 'L2', number: '1-2', locked: 0 },
				],
			},
		]
		findResource('lms.lms.utils.get_lesson').data = { ...baseLesson }
		await flushPromises()

		expect((wrapper.vm as any).canGoNext).toBe(true)
		expect(wrapper.text()).toContain('Next')
	})

	it('hardens goNext and switchLesson so neither navigates when the template is bypassed', async () => {
		wrapper = await mountLesson()
		findResource('lms.lms.utils.get_course_outline').data = [
			{
				name: 'CH-1',
				lessons: [
					{ name: 'L1', number: '1-1', locked: 0 },
					{ name: 'L2', number: '1-2', locked: 1 },
				],
			},
		]
		findResource('lms.lms.utils.get_lesson').data = { ...baseLesson }
		await flushPromises()
		;(wrapper.vm as any).goNext()
		;(wrapper.vm as any).switchLesson('next')

		expect(pushMock).not.toHaveBeenCalled()
	})

	it('still pushes (not replaces) for an ordinary Previous navigation', async () => {
		wrapper = await mountLesson({ chapterNumber: '1', lessonNumber: '2' })
		findResource('lms.lms.utils.get_course_outline').data = [
			{
				name: 'CH-1',
				lessons: [
					{ name: 'L1', number: '1-1', locked: 0 },
					{ name: 'L2', number: '1-2', locked: 0 },
				],
			},
		]
		findResource('lms.lms.utils.get_lesson').data = {
			...baseLesson,
			name: 'L2',
			prev: '1.1',
			next: null,
		}
		await flushPromises()
		;(wrapper.vm as any).goPrev()

		expect(pushMock).toHaveBeenCalledWith(
			expect.objectContaining({
				name: 'Lesson',
				params: {
					courseName: 'COURSE-1',
					chapterNumber: '1',
					lessonNumber: '1',
				},
			})
		)
		expect(replaceMock).not.toHaveBeenCalled()
	})
})

describe('Lesson.vue locked lesson payload', () => {
	it('replaces (not pushes) to redirect_to and renders the locked panel', async () => {
		wrapper = await mountLesson()
		findResource('lms.lms.utils.get_lesson').data = {
			locked: 1,
			title: 'Lesson 3',
			course_title: 'Course 1',
			redirect_to: '2-3',
		}
		await flushPromises()

		expect(replaceMock).toHaveBeenCalledWith(
			expect.objectContaining({
				name: 'Lesson',
				params: {
					courseName: 'COURSE-1',
					chapterNumber: '2',
					lessonNumber: '3',
				},
			})
		)
		expect(pushMock).not.toHaveBeenCalled()
		expect(wrapper.text()).toContain('This lesson is locked')
		expect(wrapper.text()).toContain('Go to my current lesson')
	})

	it('goToCurrentLesson also replaces using the payload redirect_to', async () => {
		wrapper = await mountLesson()
		findResource('lms.lms.utils.get_lesson').data = {
			locked: 1,
			title: 'Lesson 3',
			course_title: 'Course 1',
			redirect_to: '2-3',
		}
		await flushPromises()
		replaceMock.mockReset()
		;(wrapper.vm as any).goToCurrentLesson()

		expect(replaceMock).toHaveBeenCalledWith(
			expect.objectContaining({
				params: {
					courseName: 'COURSE-1',
					chapterNumber: '2',
					lessonNumber: '3',
				},
			})
		)
	})
})
