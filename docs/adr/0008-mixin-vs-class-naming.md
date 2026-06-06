# ADR-0008：Mixin 类与独立类的命名区隔

## 日期
2026-05-29

## 状态
已接受

## 背景
Batch 2 拆分 `decision_intel_router.py` 时，将 `IntelAnalyzer` 类拆入 `intel_analyzer.py` 并重命名为 `IntelAnalyzerMixin`。但 `decision_intel_service.py` 中的调用 `IntelAnalyzer(db)` 未被同步修改。两个类名过于相似（`IntelAnalyzer` vs `IntelAnalyzerMixin`），拆分者未察觉差异，导致断链。

## 决策
1. Mixin 类（需要外部注入 `self.db` 或 `self.request` 等）必须声明为 Mixin 后缀
2. 独立类（可自主实例化）不继承 Mixin 命名，通过继承 Mixin 暴露接口
3. Mixin 类**不在模块的 `__init__.py` 中导出**，只导出独立类

## 理由
- **语义明确**：`IntelAnalyzerMixin expecting self.db` 与 `IntelAnalyzer(db)` 是不同的事物
- **防止误用**：Mixin 不对外导出，外部模块永远无法 `from xxx import IntelAnalyzerMixin`，只能 `import IntelAnalyzer`
- **区分设计模式**：Mixin = 代码复用（借用方法），类 = 功能封装（有自己的状态）

## 被否决的方案
- **不用命名区隔，代码里写明逻辑**：代码注释会被忽略，命名是最有效的自文档
- **全用 Mixin 或用全用类**：两个模式各有用途，不能一刀切

## 后果
- 所有现有 Mixin 类需要检查是否在 `__init__.py` 中导出
- 新增 Mixin 类时，开发者和 AI 都需遵守此命名纪律
- 审计时检查 Mixin 类是否对外暴露
