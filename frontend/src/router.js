import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from './stores/user'
import { sessionStore } from './stores/session'
import { useSettings } from './stores/settings'

let defaultRoute = '/courses'
const routes = [
	{
		path: '/',
		redirect: {
			name: 'Courses',
		},
	},
	{
		path: '/courses',
		name: 'Courses',
		component: () => import('@/pages/Courses.vue'),
	},
	{
		path: '/courses/:courseName',
		name: 'CourseDetail',
		component: () => import('@/pages/CourseDetail.vue'),
		props: true,
	},
	{
		path: '/courses/:courseName/learn/:chapterNumber-:lessonNumber',
		name: 'Lesson',
		component: () => import('@/pages/Lesson.vue'),
		props: true,
	},
	{
		path: '/courses/:courseName/certification',
		name: 'CourseCertification',
		component: () => import('@/pages/CourseCertification.vue'),
		props: true,
	},
	{
		path: '/courses/:courseName/learn/:chapterName',
		name: 'SCORMChapter',
		component: () => import('@/pages/SCORMChapter.vue'),
		props: true,
	},
	{
		path: '/batches',
		name: 'Batches',
		component: () => import('@/pages/Batches.vue'),
	},
	{
		path: '/test-pdf',
		name: 'TestPDFViewer',
		component: () => import('@/pages/TestPDFViewer.vue'),
	},
	{
		path: '/pdf-lesson-demo',
		name: 'PDFLessonDemo',
		component: () => import('@/pages/PDFLessonDemo.vue'),
	},
	{
		path: '/batches/details/:batchName',
		name: 'BatchDetail',
		component: () => import('@/pages/BatchDetail.vue'),
		props: true,
	},
	{
		path: '/batches/:batchName',
		name: 'Batch',
		component: () => import('@/pages/Batch.vue'),
		props: true,
	},
	{
		path: '/billing/:type/:name',
		name: 'Billing',
		component: () => import('@/pages/Billing.vue'),
		props: true,
	},
	{
		path: '/statistics',
		name: 'Statistics',
		component: () => import('@/pages/Statistics.vue'),
	},
	{
		path: '/user/:username',
		name: 'Profile',
		component: () => import('@/pages/Profile.vue'),
		props: true,
		redirect: { name: 'ProfileAbout' },
		children: [
			{
				name: 'ProfileAbout',
				path: '',
				component: () => import('@/pages/ProfileAbout.vue'),
			},
			{
				name: 'ProfileCertificates',
				path: 'certificates',
				component: () => import('@/pages/ProfileCertificates.vue'),
			},
			{
				name: 'ProfileRoles',
				path: 'roles',
				component: () => import('@/pages/ProfileRoles.vue'),
			},
			{
				name: 'ProfileEvaluator',
				path: 'slots',
				component: () => import('@/pages/ProfileEvaluator.vue'),
			},
			{
				name: 'ProfileEvaluationSchedule',
				path: 'schedule',
				component: () => import('@/pages/ProfileEvaluationSchedule.vue'),
			},
		],
	},
	{
		path: '/jobs',
		name: 'Jobs',
		component: () => import('@/pages/Jobs.vue'),
	},
	{
		path: '/jobs/:jobName',
		name: 'JobForm',
		component: () => import('@/pages/JobForm.vue'),
		props: true,
	},
	{
		path: '/job/:jobName',
		name: 'JobDetail',
		component: () => import('@/pages/JobDetail.vue'),
		props: true,
	},
	{
		path: '/notifications',
		name: 'Notifications',
		component: () => import('@/pages/Notifications.vue'),
	},
	{
		path: '/course-form/:courseName',
		name: 'CourseForm',
		component: () => import('@/pages/CourseForm.vue'),
		props: true,
	},
	{
		path: '/lesson-form/:courseName/:chapterNumber/:lessonNumber',
		name: 'LessonForm',
		component: () => import('@/pages/LessonForm.vue'),
		props: true,
	},
	{
		path: '/batch-form/:batchName',
		name: 'BatchForm',
		component: () => import('@/pages/BatchForm.vue'),
		props: true,
	},
	{
		path: '/certified-participants',
		name: 'CertifiedParticipants',
		component: () => import('@/pages/CertifiedParticipants.vue'),
	},
	{
		path: '/badges/:badgeName/:email',
		name: 'Badge',
		component: () => import('@/pages/Badge.vue'),
		props: true,
	},
	{
		path: '/quizzes',
		name: 'Quizzes',
		component: () => import('@/pages/Quizzes.vue'),
	},
	{
		path: '/quizzes/:quizID',
		name: 'QuizForm',
		component: () => import('@/pages/QuizForm.vue'),
		props: true,
	},
	{
		path: '/quiz/:quizID',
		name: 'QuizPage',
		component: () => import('@/pages/QuizPage.vue'),
		props: true,
	},
	{
		path: '/quiz-submissions/:quizID',
		name: 'QuizSubmissionList',
		component: () => import('@/pages/QuizSubmissionList.vue'),
		props: true,
	},
	{
		path: '/quiz-submission/:submission',
		name: 'QuizSubmission',
		component: () => import('@/pages/QuizSubmission.vue'),
		props: true,
	},
	{
		path: '/programs/:programName',
		name: 'ProgramForm',
		component: () => import('@/pages/ProgramForm.vue'),
		props: true,
	},
	{
		path: '/programs',
		name: 'Programs',
		component: () => import('@/pages/Programs.vue'),
	},
	{
		path: '/assignments',
		name: 'Assignments',
		component: () => import('@/pages/Assignments.vue'),
	},
	{
		path: '/assignment-submission/:assignmentID/:submissionName',
		name: 'AssignmentSubmission',
		component: () => import('@/pages/AssignmentSubmission.vue'),
		props: true,
	},
	{
		path: '/assignment-submissions',
		name: 'AssignmentSubmissionList',
		component: () => import('@/pages/AssignmentSubmissionList.vue'),
	},
	{
		path: '/persona',
		name: 'PersonaForm',
		component: () => import('@/pages/PersonaForm.vue'),
	},
	{
		path: '/admin/enrollment-management',
		name: 'CourseEnrollmentManagement',
		component: () => import('@/pages/CourseEnrollmentManagement.vue'),
	},
	{
		path: '/admin/reminders-dashboard',
		name: 'RemindersManagementDashboard',
		component: () => import('@/pages/RemindersManagementDashboard.vue'),
	},
	{
		path: '/admin/distributor-management',
		name: 'DistributorManagement',
		component: () => import('@/pages/DistributorManagement.vue'),
		meta: {
			requiresRole: ['System Manager', 'Administrator']
		}
	},
]

let router = createRouter({
	history: createWebHistory('/lms'),
	routes,
})

router.beforeEach(async (to, from, next) => {
	const { userResource } = usersStore()
	let { isLoggedIn } = sessionStore()
	const { allowGuestAccess } = useSettings()

	try {
		if (isLoggedIn) {
			await userResource.promise
		}
	} catch (error) {
		isLoggedIn = false
	}

	if (!isLoggedIn) {
		await allowGuestAccess.promise
		if (!allowGuestAccess.data) {
			window.location.href = '/login'
			return
		}
	}
	return next()
})

export default router