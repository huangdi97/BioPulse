import { Outlet } from "react-router-dom"
import Sidebar from "./Sidebar"
import TopNav from "./TopNav"

export default function MainLayout() {
  return (
    <div className="flex min-h-screen bg-[var(--clr-gray-10)]">
      <Sidebar />
      <div className="flex-1 ml-60">
        <TopNav />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
