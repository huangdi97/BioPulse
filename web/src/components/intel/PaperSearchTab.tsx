import { useState, useEffect } from "react"
import { Search, ChevronLeft, ChevronRight } from "lucide-react"
import { Card, CardContent } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { Button } from "../ui/Button"
import { Input } from "../ui/Input"
import { getIntelPapers } from "../../api/client"
import type { Paper } from "../../types/intel"

const PAGE_SIZE = 5

export default function PaperSearchTab() {
  const [paperQuery, setPaperQuery] = useState('')
  const [page, setPage] = useState(1)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [papers, setPapers] = useState<Paper[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getIntelPapers('', 1, PAGE_SIZE).then(data => {
      setPapers(data.items)
      setTotal(data.total)
      setLoading(false)
    })
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function doSearch(q: string, p: number) {
    setLoading(true)
    getIntelPapers(q, p, PAGE_SIZE).then(data => {
      setPapers(data.items)
      setTotal(data.total)
      setLoading(false)
    })
  }

  function handleSearch() {
    setPage(1)
    doSearch(paperQuery, 1)
  }

  function handlePageChange(newPage: number) {
    setPage(newPage)
    doSearch(paperQuery, newPage)
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{color: 'var(--clr-text-placeholder)'}} />
          <Input
            placeholder="搜索论文、关键词、作者..."
            value={paperQuery}
            onChange={e => setPaperQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button onClick={handleSearch}>搜索</Button>
      </div>
      {loading ? (
        <p className="text-center py-8 text-sm" style={{color: 'var(--clr-text-secondary)'}}>加载中...</p>
      ) : papers.length === 0 ? (
        <p className="text-center py-8 text-sm" style={{color: 'var(--clr-text-secondary)'}}>未找到相关论文</p>
      ) : (
        <>
          <div className="space-y-3">
            {papers.map(p => (
              <Card key={p.id} className="cursor-pointer" onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}>
                <CardContent className="p-4 space-y-2">
                  <h4 className="text-sm font-medium cursor-pointer hover:underline" style={{color: 'var(--clr-brand)'}}>{p.title}</h4>
                  <p className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>{p.authors.join('、')}</p>
                  <div className="flex items-center gap-3 text-xs flex-wrap" style={{color: 'var(--clr-text-secondary)'}}>
                    <i>{p.journal}</i>
                    <span>{p.year}</span>
                    <span>引用: {p.citations}</span>
                    <span>PMID: {p.pmid}</span>
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    {p.keywords?.map(k => <Badge key={k}>{k}</Badge>)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>相关度: {p.relevance}%</span>
                    <div className="flex-1 h-1.5 rounded-full" style={{backgroundColor: 'var(--clr-gray-20)'}}>
                      <div className="h-full rounded-full" style={{width: `${p.relevance}%`, backgroundColor: 'var(--clr-brand)'}} />
                    </div>
                  </div>
                  {expandedId === p.id && (
                    <p className="text-xs p-2 rounded mt-1" style={{color: 'var(--clr-text-secondary)', backgroundColor: 'var(--clr-gray-10)'}}>{p.abstract}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>共 {total} 条结果</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1 || loading} onClick={() => handlePageChange(page - 1)}>
                <ChevronLeft className="w-3 h-3" /> 上一页
              </Button>
              <span className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>{page}/{totalPages}</span>
              <Button variant="outline" size="sm" disabled={page >= totalPages || loading} onClick={() => handlePageChange(page + 1)}>
                下一页 <ChevronRight className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
