import { useEffect, lazy, Suspense } from "react"
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./auth/AuthContext"
import MainLayout from "./components/layout/MainLayout"

const PharmaPage = lazy(() => import("./pages/dashboard/PharmaPage"))
const ResearchPage = lazy(() => import("./pages/research/ResearchPage"))
const CompliancePage = lazy(() => import("./pages/compliance/CompliancePage"))
const TrainingPage = lazy(() => import("./pages/coach/TrainingPage"))
const IntelPage = lazy(() => import("./pages/intel/IntelPage"))
const ConferencePage = lazy(() => import("./pages/conference/ConferencePage"))
const SettingsPage = lazy(() => import("./pages/settings/SettingsPage"))
const MarketAccessPage = lazy(() => import("./pages/market/MarketAccessPage"))
const PricingPage = lazy(() => import("./pages/pricing/PricingPage"))
const LoginPage = lazy(() => import("./pages/auth/LoginPage"))
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"))
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"))

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

function DynamicTitle() {
  useEffect(() => { document.title = '制药情报 · BioPulse' }, [])
  return null
}

export default function App() {
  useEffect(() => {
    const stored = localStorage.getItem("theme")
    if (stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [])
  return (
    <>
    <DynamicTitle />
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<div className="flex items-center justify-center h-screen">加载中...</div>}>
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
            <Route path="market" element={<MarketAccessPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
    </>
  )
}
