import { reactive } from 'vue'

const state = reactive({
  courseName: null,           // string: current course name // boolean: is course completed
  showDocument: false         // boolean: show completion document/certificate
})

const setCourseCompletion = ({ courseName, showDocument }) => {
  state.courseName = courseName
  state.showDocument = !!showDocument
}

const resetCourseCompletion = () => {
  console.log("reseting course completion")
  state.courseName = null
  state.showDocument = false
}


export {
  state,
  setCourseCompletion,
  resetCourseCompletion
}
