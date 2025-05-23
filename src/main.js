import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueViewer from 'v-viewer'
import 'viewerjs/dist/viewer.css'

const app = createApp(App)
// Configure v-viewer with options
app.use(VueViewer, {
  defaultOptions: {
    zIndex: 9999,
    movable: true,
    scalable: true,
    rotatable: true,
    tooltip: true,
    navbar: true,
    title: false,
    fullscreen: true,
    keyboard: true
  }
})
app.mount('#app')
