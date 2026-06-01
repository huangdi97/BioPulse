import { AuthProvider } from './contexts/AuthContext'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import RoleRoute from './components/RoleRoute'
import RepLayout from './pages/rep/RepLayout'
import RepDashboard from './pages/rep/Dashboard'
import HcpList from './pages/rep/HcpList'
import HcpDetail from './pages/rep/HcpDetail'
import VisitNew from './pages/rep/VisitNew'
import VisitDetail from './pages/rep/VisitDetail'
import TaskList from './pages/rep/TaskList'
import ManagerLayout from './pages/manager/ManagerLayout'
import ManagerDashboard from './pages/manager/Dashboard'
import ManagerVisits from './pages/manager/Visits'
import ManagerOpportunities from './pages/manager/Opportunities'
import ComplianceOverview from './pages/manager/ComplianceOverview'
import ComplianceRecords from './pages/manager/ComplianceRecords'
import ComplianceDetail from './pages/manager/ComplianceDetail'
import Settings from './pages/manager/Settings'
import ManagementLayout from './layouts/ManagementLayout'
import PresidentSummary from './pages/admin/president/Summary'
import PresidentCompliance from './pages/admin/president/ComplianceOverview'
import PresidentRankings from './pages/admin/president/TeamRankings'
import PresidentTrend from './pages/admin/president/TrendReport'
import ManagerStats from './pages/admin/manager/TeamStats'
import ManagerMembers from './pages/admin/manager/TeamMembers'
import ManagerCompliance from './pages/admin/manager/TeamCompliance'
import ManagerPerformance from './pages/admin/manager/TeamPerformance'
import EmployeeProfile from './pages/admin/employee/MyProfile'
import EmployeeTasks from './pages/admin/employee/MyTasks'
import EmployeeCompliance from './pages/admin/employee/MyCompliance'
import EmployeePerformance from './pages/admin/employee/MyPerformance'
import EmployeeTrend from './pages/admin/employee/MyTrend'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<RoleRoute allowedRoles={['rep', 'admin']} />}>
              <Route path="/rep" element={<RepLayout />}>
                <Route index element={<Navigate to="dashboard" replace />} />
                <Route path="dashboard" element={<RepDashboard />} />
                <Route path="hcps" element={<HcpList />} />
                <Route path="hcps/:id" element={<HcpDetail />} />
                <Route path="tasks" element={<TaskList />} />
                <Route path="visits/new" element={<VisitNew />} />
                <Route path="visits/:id" element={<VisitDetail />} />
                <Route path="visits" element={<Navigate to="/rep/visits/new?hcpId=1" replace />} />
              </Route>
            </Route>
            <Route element={<RoleRoute allowedRoles={['manager', 'admin']} />}>
              <Route path="/manager" element={<ManagerLayout />}>
                <Route index element={<Navigate to="dashboard" replace />} />
                <Route path="dashboard" element={<ManagerDashboard />} />
                <Route path="visits" element={<ManagerVisits />} />
                <Route path="opportunities" element={<ManagerOpportunities />} />
                <Route path="compliance" element={<ComplianceOverview />} />
                <Route path="compliance/records" element={<ComplianceRecords />} />
                <Route path="compliance/records/:id" element={<ComplianceDetail />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Route>
            <Route path="/admin" element={<ManagementLayout />}>
              <Route index element={<Navigate to="president/summary" replace />} />
              <Route element={<RoleRoute allowedRoles={['admin']} />}>
                <Route path="president/summary" element={<PresidentSummary />} />
                <Route path="president/compliance" element={<PresidentCompliance />} />
                <Route path="president/rankings" element={<PresidentRankings />} />
                <Route path="president/trend" element={<PresidentTrend />} />
              </Route>
              <Route element={<RoleRoute allowedRoles={['manager']} />}>
                <Route path="manager/stats" element={<ManagerStats />} />
                <Route path="manager/members" element={<ManagerMembers />} />
                <Route path="manager/compliance" element={<ManagerCompliance />} />
                <Route path="manager/performance" element={<ManagerPerformance />} />
              </Route>
              <Route element={<RoleRoute allowedRoles={['rep']} />}>
                <Route path="employee/profile" element={<EmployeeProfile />} />
                <Route path="employee/tasks" element={<EmployeeTasks />} />
                <Route path="employee/compliance" element={<EmployeeCompliance />} />
                <Route path="employee/performance" element={<EmployeePerformance />} />
                <Route path="employee/trend" element={<EmployeeTrend />} />
              </Route>
            </Route>
            <Route path="/dashboard" element={<Navigate to="/rep/dashboard" replace />} />
            <Route path="/" element={<Navigate to="/rep/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
