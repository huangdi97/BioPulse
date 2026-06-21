export default function MarketAccessPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{color: 'var(--clr-text-primary)'}}>招标监控</h1>
        <p className="text-sm mt-1" style={{color: 'var(--clr-text-secondary)'}}>医保目录与招标价格监控</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: '活跃招标', value: '24', color: 'var(--clr-brand)' },
          { label: '本月新增', value: '7', color: 'var(--clr-success)' },
          { label: '价格变动', value: '3', color: 'var(--clr-warning)' },
          { label: '待分析', value: '12', color: 'var(--clr-text-primary)' },
        ].map((kpi) => (
          <div key={kpi.label} className="p-4 rounded-lg" style={{backgroundColor: 'var(--clr-gray-10)'}}>
            <p className="text-xs" style={{color: 'var(--clr-text-secondary)'}}>{kpi.label}</p>
            <p className="text-2xl font-bold mt-1" style={{color: kpi.color}}>{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Recent Tenders Table */}
      <div className="rounded-lg overflow-hidden" style={{backgroundColor: 'var(--clr-gray-10)'}}>
        <div className="p-3 border-b" style={{borderColor: 'var(--clr-border-default)'}}>
          <h3 className="text-sm font-semibold" style={{color: 'var(--clr-text-primary)'}}>最近招标动态</h3>
        </div>
        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-sm">
            <thead>
              <tr style={{color: 'var(--clr-text-secondary)'}}>
                <th className="text-left p-3 font-medium">省份</th>
                <th className="text-left p-3 font-medium">产品</th>
                <th className="text-left p-3 font-medium">类型</th>
                <th className="text-left p-3 font-medium">状态</th>
                <th className="text-left p-3 font-medium">日期</th>
              </tr>
            </thead>
            <tbody>
              {[
                { region: '广东', product: '阿托伐他汀', type: '集采', status: '报价中', date: '2026-06-15' },
                { region: '江苏', product: '氯吡格雷', type: '挂网', status: '已公示', date: '2026-06-12' },
                { region: '上海', product: '奥美拉唑', type: '议价', status: '待确认', date: '2026-06-10' },
                { region: '北京', product: '瑞舒伐他汀', type: '集采', status: '报价中', date: '2026-06-08' },
              ].map((row, i) => (
                <tr key={i} className="border-t" style={{borderColor: 'var(--clr-border-default)'}}>
                  <td className="p-3" style={{color: 'var(--clr-text-primary)'}}>{row.region}</td>
                  <td className="p-3" style={{color: 'var(--clr-text-primary)'}}>{row.product}</td>
                  <td className="p-3" style={{color: 'var(--clr-text-secondary)'}}>{row.type}</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded text-xs" style={{backgroundColor: 'var(--clr-brand-light)', color: 'var(--clr-brand)'}}>{row.status}</span></td>
                  <td className="p-3" style={{color: 'var(--clr-text-secondary)'}}>{row.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="block md:hidden space-y-2 p-3">
          {[
            { region: '广东', product: '阿托伐他汀', type: '集采', status: '报价中', date: '2026-06-15' },
            { region: '江苏', product: '氯吡格雷', type: '挂网', status: '已公示', date: '2026-06-12' },
            { region: '上海', product: '奥美拉唑', type: '议价', status: '待确认', date: '2026-06-10' },
            { region: '北京', product: '瑞舒伐他汀', type: '集采', status: '报价中', date: '2026-06-08' },
          ].map((row, i) => (
            <div key={i} className="p-3 rounded-lg" style={{backgroundColor: 'var(--clr-surface-card)'}}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium" style={{color: 'var(--clr-text-primary)'}}>{row.product}</span>
                <span className="px-2 py-0.5 rounded text-xs" style={{backgroundColor: 'var(--clr-brand-light)', color: 'var(--clr-brand)'}}>{row.status}</span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-xs" style={{color: 'var(--clr-text-secondary)'}}>
                <span>省份: {row.region}</span>
                <span>类型: {row.type}</span>
                <span>日期: {row.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
