import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { TopPage } from './pages/TopPage'
import { BookDetailPage } from './pages/BookDetailPage'
import { Layout } from './components/Layout'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<TopPage />} />
          <Route path="/book/:id" element={<BookDetailPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
