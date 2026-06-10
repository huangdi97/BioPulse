import { lazy, Suspense } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import KeyboardShell from './components/KeyboardShell'
import ProtectedRoute from './components/ProtectedRoute'
import RoleRoute from './components/RoleRoute'
import RepLayout from './pages/rep/RepLayout'
import ManagerLayout from './pages/manager/ManagerLayout'
import ManagementLayout from './layouts/ManagementLayout'
import CoachLayout from './pages/coach/CoachLayout'
import OpportunityLayout from './pages/opportunity/OpportunityLayout'
import AssistantLayout from './pages/assistant/AssistantLayout'
import SalesAssistantLayout from './pages/sales-assistant/SalesAssistantLayout'

const Login = lazy(() => import('./pages/Login'))
const RepDashboard = lazy(() => import('./pages/rep/Dashboard'))
const HcpList = lazy(() => import('./pages/rep/HcpList'))
const HcpDetail = lazy(() => import('./pages/rep/HcpDetail'))
const VisitNew = lazy(() => import('./pages/rep/VisitNew'))
const VisitDetail = lazy(() => import('./pages/rep/VisitDetail'))
const TaskList = lazy(() => import('./pages/rep/TaskList'))
const ManagerDashboard = lazy(() => import('./pages/manager/Dashboard'))
const ManagerVisits = lazy(() => import('./pages/manager/Visits'))
const ManagerOpportunities = lazy(() => import('./pages/manager/Opportunities'))
const ComplianceOverview = lazy(() => import('./pages/manager/ComplianceOverview'))
const ComplianceRecords = lazy(() => import('./pages/manager/ComplianceRecords'))
const ComplianceDetail = lazy(() => import('./pages/manager/ComplianceDetail'))
const InspectionDashboard = lazy(() => import('./pages/manager/InspectionDashboard'))
const InspectionChecklist = lazy(() => import('./pages/manager/InspectionChecklist'))
const InspectionHistory = lazy(() => import('./pages/manager/InspectionHistory'))
const InspectionAssign = lazy(() => import('./pages/manager/InspectionAssign'))
const InspectionReview = lazy(() => import('./pages/manager/InspectionReview'))
const ApprovalPanel = lazy(() => import('./pages/manager/ApprovalPanel'))
const AdmissionTracker = lazy(() => import('./pages/manager/AdmissionTracker'))
const Settings = lazy(() => import('./pages/manager/Settings'))
const PresidentSummary = lazy(() => import('./pages/admin/president/Summary'))
const PresidentCompliance = lazy(() => import('./pages/admin/president/ComplianceOverview'))
const PresidentRankings = lazy(() => import('./pages/admin/president/TeamRankings'))
const PresidentTrend = lazy(() => import('./pages/admin/president/TrendReport'))
const ExpenseWasteDashboard = lazy(() => import('./pages/admin/president/ExpenseWasteDashboard'))
const VisitFraudDashboard = lazy(() => import('./pages/admin/president/VisitFraudDashboard'))
const ManagementNeglectDashboard = lazy(() => import('./pages/admin/president/ManagementNeglectDashboard'))
const RectificationDashboard = lazy(() => import('./pages/admin/president/RectificationDashboard'))
const ExclusionGateConfig = lazy(() => import('./pages/admin/president/ExclusionGateConfig'))
const ManagerStats = lazy(() => import('./pages/admin/manager/TeamStats'))
const ManagerMembers = lazy(() => import('./pages/admin/manager/TeamMembers'))
const ManagerCompliance = lazy(() => import('./pages/admin/manager/TeamCompliance'))
const ManagerPerformance = lazy(() => import('./pages/admin/manager/TeamPerformance'))
const EmployeeProfile = lazy(() => import('./pages/admin/employee/MyProfile'))
const EmployeeTasks = lazy(() => import('./pages/admin/employee/MyTasks'))
const EmployeeCompliance = lazy(() => import('./pages/admin/employee/MyCompliance'))
const EmployeePerformance = lazy(() => import('./pages/admin/employee/MyPerformance'))
const EmployeeTrend = lazy(() => import('./pages/admin/employee/MyTrend'))
const AgentTraceDashboard = lazy(() => import('./pages/admin/AgentTraceDashboard'))
const ScenarioList = lazy(() => import('./pages/coach/ScenarioList'))
const SessionList = lazy(() => import('./pages/coach/SessionList'))
const SessionDetail = lazy(() => import('./pages/coach/SessionDetail'))
const AssessmentList = lazy(() => import('./pages/coach/AssessmentList'))
const ReflectionList = lazy(() => import('./pages/coach/ReflectionList'))
const StatsDashboard = lazy(() => import('./pages/coach/StatsDashboard'))
const OpportunityList = lazy(() => import('./pages/opportunity/OpportunityList'))
const OpportunityDetail = lazy(() => import('./pages/opportunity/OpportunityDetail'))
const BiddingList = lazy(() => import('./pages/opportunity/BiddingList'))
const ResearchPanel = lazy(() => import('./pages/opportunity/ResearchPanel'))
const ContactList = lazy(() => import('./pages/opportunity/ContactList'))
const TrendsChart = lazy(() => import('./pages/opportunity/TrendsChart'))
const OppStats = lazy(() => import('./pages/opportunity/OppStats'))
const AsstHcpList = lazy(() => import('./pages/assistant/HcpList'))
const AsstHcpDetail = lazy(() => import('./pages/assistant/HcpDetail'))
const VisitList = lazy(() => import('./pages/assistant/VisitList'))
const NotFound = lazy(() => import('./pages/NotFound'))
const AsstTaskList = lazy(() => import('./pages/assistant/TaskList'))
const KnowledgeView = lazy(() => import('./pages/assistant/KnowledgeView'))
const QAPanel = lazy(() => import('./pages/assistant/QAPanel'))
const PreCallView = lazy(() => import('./pages/sales-assistant/PreCallView'))
const ContentLibrary = lazy(() => import('./pages/sales-assistant/ContentLibrary'))
const StrategyView = lazy(() => import('./pages/sales-assistant/StrategyView'))
const ObjectionList = lazy(() => import('./pages/sales-assistant/ObjectionList'))
const NoteList = lazy(() => import('./pages/sales-assistant/NoteList'))
const FunnelView = lazy(() => import('./pages/sales-assistant/FunnelView'))
const ScheduleView = lazy(() => import('./pages/sales-assistant/ScheduleView'))

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<div className="flex items-center justify-center h-screen">加载中...</div>}>
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
                <Route path="visits" element={<VisitList />} />
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
                <Route path="inspection/assign" element={<InspectionAssign />} />
                <Route path="inspection/review" element={<InspectionReview />} />
                <Route path="approval" element={<ApprovalPanel />} />
                <Route path="admission" element={<AdmissionTracker />} />
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
                <Route path="president/expense-waste" element={<ExpenseWasteDashboard />} />
                <Route path="president/visit-fraud" element={<VisitFraudDashboard />} />
                <Route path="president/management-neglect" element={<ManagementNeglectDashboard />} />
                <Route path="president/rectification" element={<RectificationDashboard />} />
                <Route path="president/exclusion-gates" element={<ExclusionGateConfig />} />
                <Route path="traces" element={<AgentTraceDashboard />} />
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
            <Route path="*" element={<NotFound />} />
          </Route>
          </Route>
        </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}
