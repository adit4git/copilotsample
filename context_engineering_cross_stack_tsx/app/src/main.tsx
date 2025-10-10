import React from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './ui/App'
const root = document.getElementById('root')
if(!root) throw new Error('Missing #root')
createRoot(root).render(<App />)
