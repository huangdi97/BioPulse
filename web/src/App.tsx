import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import MainLayout from "./components/layout/MainLayout"
import PharmaPage from "./pages/dashboard/PharmaPage"
import ResearchPage from "./pages/research/ResearchPage"
import CompliancePage from "./pages/compliance/CompliancePage"
import TrainingPage from "./pages/coach/TrainingPage"
import IntelPage from "./pages/intel/IntelPage"
import SettingsPage from "./pages/settings/SettingsPage"
import PricingPage from "./pages/pricing/PricingPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard/pharma" replace />} />
          <Route path="dashboard/pharma" element={<PharmaPage />} />
          <Route path="dashboard/research" element={<ResearchPage />} />
          <Route path="compliance/overview" element={<CompliancePage />} />
          <Route path="coach/training" element={<TrainingPage />} />
          <Route path="intel/analysis" element={<IntelPage />} />
          <Route path="settings/system" element={<SettingsPage />} />
          <Route path="pricing" element={<PricingPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
