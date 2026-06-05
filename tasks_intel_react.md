# 任务：React IntelPage 对接制药情报 8006 API

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 操作

### 1. 修改 `web/src/api/client.ts`

在文件底部新增函数：

```
let intelBaseURL = "http://localhost:8006"

export function setIntelBaseURL(url: string) { intelBaseURL = url }

// 论文检索
export async function getIntelPapers(q: string, page = 1, pageSize = 10) {
  try {
    const res = await fetch(`${intelBaseURL}/api/intel/papers?q=${encodeURIComponent(q)}&page=${page}&page_size=${pageSize}`)
    const json = await res.json()
    if (json.code === 0 && json.data) return json.data
    return { items: [], total: 0, page: 1 }
  } catch {
    return { items: [], total: 0, page: 1 }
  }
}

// PI画像
export async function getIntelPiProfiles(q: string, page = 1, pageSize = 20) {
  try {
    const res = await fetch(`${intelBaseURL}/api/intel/pi?q=${encodeURIComponent(q)}&page=${page}&page_size=${pageSize}`)
    const json = await res.json()
    if (json.code === 0 && json.data) return json.data
    return { items: [], total: 0, page: 1 }
  } catch {
    return { items: [], total: 0, page: 1 }
  }
}

// 靶点列表
export async function getIntelTargets(category?: string, sortBy = "paper_count", sortDir = "desc") {
  try {
    let url = `${intelBaseURL}/api/intel/targets?sort_by=${sortBy}&sort_dir=${sortDir}`
    if (category && category !== '全部') url += `&category=${encodeURIComponent(category)}`
    const res = await fetch(url)
    const json = await res.json()
    if (json.code === 0 && json.data) return json.data
    return []
  } catch {
    return []
  }
}

// 靶点分类
export async function getIntelTargetCategories() {
  try {
    const res = await fetch(`${intelBaseURL}/api/intel/targets/categories`)
    const json = await res.json()
    if (json.code === 0 && json.data) return ['全部', ...json.data]
    return ['全部']
  } catch {
    return ['全部']
  }
}
```

### 2. 修改 `web/src/components/intel/PaperSearchTab.tsx`

将 `import { papers } from "../../api/mockIntel"` 改为调用 `getIntelPapers`。
在组件内部用 useEffect 在挂载和搜索时调用 API，替代本地静态筛选。

### 3. 修改 `web/src/components/intel/PiProfileTab.tsx`

将 `import { piProfiles } from "../../api/mockIntel"` 改为调用 `getIntelPiProfiles`。
用 useEffect + API 替代本地静态筛选。

### 4. 修改 `web/src/components/intel/TargetHeatmapTab.tsx`

将 `import { targets, type Target } from "../../api/mockIntel"` 改为调用 `getIntelTargets` 和 `getIntelTargetCategories`。
用 useEffect 在挂载和筛选时调用 API，替代本地静态数据。

### 5. 验证

`npm run build` 通过
