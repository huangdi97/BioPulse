# ADR-0007：大文件拆分后必须运行全量测试

## 日期
2026-05-29

## 状态
已接受

## 背景
Batch 2 拆分了 22 个超过 300 行的大文件。拆分过程中，每个文件的 import 在独立模块层面验证通过（`python -c "import xxx"` 无报错）。但未运行 `pytest` 全量测试，导致 241 个测试因级联 import 断裂而失败。根因：`intel_analyzer.py` 拆分后丢失了 `IntelAnalyzer` 类，只导出了 `IntelAnalyzerMixin`，`decision_intel_service.py` 的导入断裂 → 连锁到 `main.py` 加载失败 → 所有导入 `main` 的测试全部 ERR。

## 决策
任何涉及**文件结构变动**（新增/删除/重命名文件、修改文件间导入关系）的 commit，必须运行全量测试：

```bash
cd cloud && python -m pytest app/tests/ -q --tb=line
```

## 理由
- **级联断链难以在单模块测试中发现**：`from xxx import yyy` 在 Python 语法检查层面是合法的，只有运行时才知道 yyy 是否存在
- **241 个测试伪报 = 1 个遗漏**：修复成本极低（7 行代码），发现成本极高（30 分钟定位）
- **纪律防漏**：每次提交前跑一次全量测试的时间成本 < 2 分钟（增量缓存），远比出问题后 debug 快

## 被否决的方案
- **只跑改过的文件相关测试**：import 断链是级联的，"改了 A"不知道会影响到 Z
- **依赖 CI 发现**：CI 在远端，发现问题 → 修复 → 再提交的循环太慢
- **不建纪律，下次注意**：人的注意力不可靠，需要自动化纪律

## 后果
- CI 配置中保留 pytest 步骤
- pre-commit hook 可以考虑加 pytest（但全量跑耗时 ~80s，当前不强制）
- 提交前至少手动跑一次 `python -m pytest cloud/app/tests/ -q`
