import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { TopPage } from './pages/TopPage'
import { BookDetailPage } from './pages/BookDetailPage'
import { ChannelsPage } from './pages/ChannelsPage'
import { Layout } from './components/Layout'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<TopPage />} />
          <Route path="/book/:id" element={<BookDetailPage />} />
          <Route path="/channels" element={<ChannelsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
