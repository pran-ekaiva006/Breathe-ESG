import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard    from './pages/Dashboard'
import Uploads      from './pages/Uploads'
import Reviews      from './pages/Reviews'
import RecordDetail from './pages/RecordDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"              element={<Dashboard />} />
        <Route path="/uploads"       element={<Uploads />} />
        <Route path="/reviews"       element={<Reviews />} />
        <Route path="/records/:id"   element={<RecordDetail />} />
        <Route path="*"              element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
