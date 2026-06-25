import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useSettingsStore } from '@/store/useSettingsStore'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/pages/Dashboard'
import { MediaDetail } from '@/pages/MediaDetail'
import { Search } from '@/pages/Search'
import { Settings } from '@/pages/Settings'

function App() {
  const syncWithBackend = useSettingsStore(state => state.syncWithBackend)

  useEffect(() => {
    syncWithBackend()
  }, [syncWithBackend])

  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="media/:id" element={<MediaDetail />} />
        <Route path="search" element={<Search />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
