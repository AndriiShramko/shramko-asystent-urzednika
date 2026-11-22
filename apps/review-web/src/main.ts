import './style.css'
import { mountApp } from './ui/app'
import { attachModelKey } from './ui/modelkey'

const root = document.getElementById('app')
if (root) {
  mountApp(root)
  attachModelKey(root) // W11 KEY: the block "Model AI (opcjonalnie)" under the upload panel
}
