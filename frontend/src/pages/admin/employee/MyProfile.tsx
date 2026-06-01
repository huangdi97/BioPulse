import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { UserCircle, Mail, Building, Calendar, Shield } from 'lucide-react'

const mockProfile = {
  name: '张小明',
  email: 'zhangxm@example.com',
  dept: '销售部',
  joinDate: '2024-03-15',
  role: '高级销售代表',
  region: '华东区域',
}

export default function MyProfile() {
  const { user } = useAuth()

  const profile = {
    name: user?.username ?? mockProfile.name,
    email: mockProfile.email,
    dept: mockProfile.dept,
    joinDate: mockProfile.joinDate,
    role: mockProfile.role,
    region: mockProfile.region,
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <UserCircle className="h-5 w-5 text-primary" />
          个人信息
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary text-2xl font-bold">
            {profile.name.charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-semibold">{profile.name}</h2>
            <p className="text-sm text-muted-foreground">{profile.role}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span>{profile.email}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Building className="h-4 w-4 text-muted-foreground" />
            <span>{profile.dept}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span>入职日期: {profile.joinDate}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span>负责区域: {profile.region}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
