# Flutter Batch 1：基URL + 补路由

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 任务

### 1. lib/main.dart — 改默认基URL
当前 26-31 行 defaultUrls 全是 `https://api.example.com`。
改为指向腾讯云实际地址：
- sales_assistant: `http://43.153.166.191:8004`
- cloud: `http://43.153.166.191:8000`
- opportunity: `http://43.153.166.191:8002`
- sales_coach: `http://43.153.166.191:8001`
- sync: `http://43.153.166.191:8000`

### 2. lib/app.dart — 补路由（添加 11 个子屏路由）
在 `_onGenerateRoute` 的 switch 中添加以下 case：
```
/pharma/visit-list       → VisitListScreen
/pharma/hcp-list         → HcpListScreen
/pharma/compliance       → ComplianceScreen
/surgery/scan            → ScanScreen
/surgery/list            → SurgeryListScreen
/surgery/detail          → SurgeryDetailScreen  (需传id参数)
/surgery/form            → SurgeryFormScreen
/research/pi-search      → PISearchScreen
/research/product-match  → ProductMatchingScreen
/research/quotation      → QuotationScreen
/coach/training-list     → TrainingListScreen
/coach/analysis-report   → AnalysisReportScreen
/coach/recommendation    → RecommendationScreen
```

需要添加的 import（文件顶部）：
```dart
import 'package:one_cloud_app/screens/surgery/surgery_list_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_detail_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_form_screen.dart';
import 'package:one_cloud_app/screens/research/pi_search_screen.dart';
import 'package:one_cloud_app/screens/research/product_matching_screen.dart';
import 'package:one_cloud_app/screens/research/quotation_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/training_list_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/analysis_report_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/recommendation_screen.dart';
```

现有路由保留不动。

### 3. lib/services/sync_service.dart — 改同步基URL
第21行 `serverUrl = prefs.getString(_serverUrlKey) ?? 'https://api.example.com'`
改为 `serverUrl = prefs.getString(_serverUrlKey) ?? 'http://43.153.166.191:8000'`

## 验收标准
- main.dart 中所有 example.com 被替换
- app.dart 新增的 11 个路由 case 能跳转到正确的 Screen 类
- app.dart 语法正确（import 不冲突）
- sync_service.dart 默认服务器地址更新
