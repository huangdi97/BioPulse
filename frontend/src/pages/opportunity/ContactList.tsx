import { useState, useEffect } from 'react'
import { fetchContacts, type Contact } from '@/api/opportunity-api'
import { Card, CardContent } from '@/components/ui/card'
import { User, Building2, Phone, Mail } from 'lucide-react'

export default function ContactList() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchContacts().then((data) => {
      if (cancelled) return
      setContacts(data)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return <div className="space-y-3">{[1, 2].map((i) => <Card key={i}><CardContent className="p-4 animate-pulse"><div className="h-24 bg-muted rounded" /></CardContent></Card>)}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">联系人管理</h2>
      {contacts.map((c) => (
        <Card key={c.id}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
                <User className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-semibold">{c.name}</p>
                <p className="text-xs text-muted-foreground">{c.title}</p>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Building2 className="h-3 w-3" /><span>{c.hospital} · {c.department}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Phone className="h-3 w-3" /><span>{c.phone}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Mail className="h-3 w-3" /><span>{c.email}</span>
              </div>
            </div>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-xs bg-purple-50 text-purple-700">{c.role}</span>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
