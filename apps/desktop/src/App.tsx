import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeContext'
import Layout from './components/Layout'
import SyncStatus from './components/SyncStatus'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import DocumentViewer from './pages/DocumentViewer'
import Settings from './pages/Settings'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/search" element={<Search />} />
              <Route path="/document/:id" element={<DocumentViewer />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
          <SyncStatus />
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
