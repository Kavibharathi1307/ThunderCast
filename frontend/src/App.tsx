import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LoadingState from './components/common/LoadingState'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const RiskMap = lazy(() => import('./pages/RiskMap'))
const Forecast = lazy(() => import('./pages/Forecast'))
const StormTracking = lazy(() => import('./pages/StormTracking'))
const Alerts = lazy(() => import('./pages/Alerts'))
const HistoricalEvents = lazy(() => import('./pages/HistoricalEvents'))
const Methodology = lazy(() => import('./pages/Methodology'))
const NotFound = lazy(() => import('./pages/NotFound'))

export default function App() {
  return (
    <Suspense fallback={<LoadingState label="Loading page…" />}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="risk-map" element={<RiskMap />} />
          <Route path="forecast" element={<Forecast />} />
          <Route path="storm-tracking" element={<StormTracking />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="historical-events" element={<HistoricalEvents />} />
          <Route path="methodology" element={<Methodology />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
