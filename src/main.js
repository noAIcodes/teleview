import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueViewer from 'v-viewer' // Changed import name
import 'viewerjs/dist/viewer.css'

const app = createApp(App)
// Try using VueViewer.default if VueViewer is an object containing the plugin as default export
if (VueViewer && typeof VueViewer === 'object' && VueViewer.default) {
  app.use(VueViewer.default)
} else {
  app.use(VueViewer) // Original attempt with VueViewer
}
app.mount('#app')
