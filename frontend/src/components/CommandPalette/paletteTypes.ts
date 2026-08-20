import type { Component } from 'vue'

export interface PaletteRoute {
	name: string
	params?: Record<string, string>
	query?: Record<string, string>
}

export interface PaletteItem {
	title: string
	route?: PaletteRoute
	/** Narrows the search to this category instead of acting. */
	category?: string
	perform?: () => void
	doctype?: string
	name?: string
	icon?: Component
	/** Unix seconds, as the search index stores it. */
	modified?: number
	isActive?: boolean
}

export interface PaletteGroup {
	title: string
	items: PaletteItem[]
}

/**
 * Where a search hit opens. Every doctype but LMS Course used to fall through to
 * the batch route, so a job hit navigated to /batches/JOB-0001; an unmapped
 * doctype now yields nothing and its row is dropped instead.
 */
const ROUTE_BUILDERS: Record<string, (name: string) => PaletteRoute> = {
	'LMS Course': (name) => ({
		name: 'CourseDetail',
		params: { courseName: name },
	}),
	'LMS Batch': (name) => ({
		name: 'BatchDetail',
		params: { batchName: name },
	}),
	'Job Opportunity': (name) => ({ name: 'JobDetail', params: { job: name } }),
	'LMS Quiz': (name) => ({ name: 'QuizForm', params: { quizID: name } }),
	'LMS Assignment': (name) => ({
		name: 'AssignmentForm',
		params: { assignmentID: name },
	}),
	'LMS Program': (name) => ({
		name: 'ProgramDetail',
		params: { programName: name },
	}),
}

export function routeForSearchHit(
	doctype: string,
	name: string
): PaletteRoute | null {
	return ROUTE_BUILDERS[doctype]?.(name) ?? null
}
