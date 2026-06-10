import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import KeyboardShell from './components/KeyboardShell'
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
import InspectionDashboard from './pages/manager/InspectionDashboard'
import InspectionChecklist from './pages/manager/InspectionChecklist'
import InspectionHistory from './pages/manager/InspectionHistory'
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
import CoachLayout from './pages/coach/CoachLayout'
import ScenarioList from './pages/coach/ScenarioList'
import SessionList from './pages/coach/SessionList'
import SessionDetail from './pages/coach/SessionDetail'
import AssessmentList from './pages/coach/AssessmentList'
import ReflectionList from './pages/coach/ReflectionList'
import StatsDashboard from './pages/coach/StatsDashboard'
import OpportunityLayout from './pages/opportunity/OpportunityLayout'
import OpportunityList from './pages/opportunity/OpportunityList'
import OpportunityDetail from './pages/opportunity/OpportunityDetail'
import BiddingList from './pages/opportunity/BiddingList'
import ResearchPanel from './pages/opportunity/ResearchPanel'
import ContactList from './pages/opportunity/ContactList'
import TrendsChart from './pages/opportunity/TrendsChart'
import OppStats from './pages/opportunity/OppStats'
import AssistantLayout from './pages/assistant/AssistantLayout'
import AsstHcpList from './pages/assistant/HcpList'
import AsstHcpDetail from './pages/assistant/HcpDetail'
import VisitList from './pages/assistant/VisitList'
import AsstTaskList from './pages/assistant/TaskList'
import KnowledgeView from './pages/assistant/KnowledgeView'
import QAPanel from './pages/assistant/QAPanel'
import SalesAssistantLayout from './pages/sales-assistant/SalesAssistantLayout'
import PreCallView from './pages/sales-assistant/PreCallView'
import ContentLibrary from './pages/sales-assistant/ContentLibrary'
import StrategyView from './pages/sales-assistant/StrategyView'
import ObjectionList from './pages/sales-assistant/ObjectionList'
import NoteList from './pages/sales-assistant/NoteList'
import FunnelView from './pages/sales-assistant/FunnelView'
import ScheduleView from './pages/sales-assistant/ScheduleView'

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<KeyboardShell />}>
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
                <Route path="inspection" element={<InspectionDashboard />} />
                <Route path="inspection/checklist" element={<InspectionChecklist />} />
                <Route path="inspection/history" element={<InspectionHistory />} />
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
            {/* Four-End Routes */}
            <Route path="/coach" element={<CoachLayout />}>
              <Route index element={<Navigate to="scenarios" replace />} />
              <Route path="scenarios" element={<ScenarioList />} />
              <Route path="sessions" element={<SessionList />} />
              <Route path="sessions/:id" element={<SessionDetail />} />
              <Route path="assessments" element={<AssessmentList />} />
              <Route path="reflections" element={<ReflectionList />} />
              <Route path="stats" element={<StatsDashboard />} />
            </Route>
            <Route path="/opportunity" element={<OpportunityLayout />}>
              <Route index element={<Navigate to="opportunities" replace />} />
              <Route path="opportunities" element={<OpportunityList />} />
              <Route path="opportunities/:id" element={<OpportunityDetail />} />
              <Route path="bidding" element={<BiddingList />} />
              <Route path="research" element={<ResearchPanel />} />
              <Route path="contacts" element={<ContactList />} />
              <Route path="trends" element={<TrendsChart />} />
              <Route path="stats" element={<OppStats />} />
            </Route>
            <Route path="/assistant" element={<AssistantLayout />}>
              <Route index element={<Navigate to="hcps" replace />} />
              <Route path="hcps" element={<AsstHcpList />} />
              <Route path="hcps/:id" element={<AsstHcpDetail />} />
              <Route path="visits" element={<VisitList />} />
              <Route path="tasks" element={<AsstTaskList />} />
              <Route path="knowledge" element={<KnowledgeView />} />
              <Route path="qa" element={<QAPanel />} />
            </Route>
            <Route path="/sales-assistant" element={<SalesAssistantLayout />}>
              <Route index element={<Navigate to="precall" replace />} />
              <Route path="precall" element={<PreCallView />} />
              <Route path="content" element={<ContentLibrary />} />
              <Route path="strategy" element={<StrategyView />} />
              <Route path="objections" element={<ObjectionList />} />
              <Route path="notes" element={<NoteList />} />
              <Route path="funnel" element={<FunnelView />} />
              <Route path="schedule" element={<ScheduleView />} />
            </Route>
            <Route path="/dashboard" element={<Navigate to="/rep/dashboard" replace />} />
            <Route path="/" element={<Navigate to="/rep/dashboard" replace />} />
          </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}
