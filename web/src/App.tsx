import { useEffect } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./auth/AuthContext"
import MainLayout from "./components/layout/MainLayout"
import PharmaPage from "./pages/dashboard/PharmaPage"
import ResearchPage from "./pages/research/ResearchPage"
import CompliancePage from "./pages/compliance/CompliancePage"
import TrainingPage from "./pages/coach/TrainingPage"
import IntelPage from "./pages/intel/IntelPage"
import ConferencePage from "./pages/conference/ConferencePage"
import SettingsPage from "./pages/settings/SettingsPage"
import PricingPage from "./pages/pricing/PricingPage"
import LoginPage from "./pages/auth/LoginPage"
import RegisterPage from "./pages/auth/RegisterPage"

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, init } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    init()
  }, [init])

  useEffect(() => {
    if (!token) {
      navigate("/login", { replace: true, state: { from: location } })
    }
  }, [token, navigate, location])

  if (!token) return null

  return <>{children}</>
}

function AuthenticatedLayout() {
  return (
    <AuthGuard>
      <MainLayout />
    </AuthGuard>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<AuthenticatedLayout />}>
            <Route index element={<Navigate to="/dashboard/pharma" replace />} />
            <Route path="dashboard/pharma" element={<PharmaPage />} />
            <Route path="dashboard/research" element={<ResearchPage />} />
            <Route path="compliance/overview" element={<CompliancePage />} />
            <Route path="coach/training" element={<TrainingPage />} />
            <Route path="intel/analysis" element={<IntelPage />} />
            <Route path="conference" element={<ConferencePage />} />
            <Route path="settings/system" element={<SettingsPage />} />
            <Route path="pricing" element={<PricingPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
