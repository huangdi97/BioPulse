# 执行计划：B+C+E

## 背景
用户指令：B（全量测试）+ C（Flutter 构建）+ E（性能基线）

## 任务拆解

### B — 全量测试
- **范围**: `cloud/app/tests/` 全部测试用例
- **命令**: `python -m pytest cloud/app/tests/ -v --tb=short -q`
- **预期**: 400+ passed（含 AgentBench 11 + Rollback 1）
- **耗时**: ~3-4 分钟
- **输出**: 通过的用例数 + 失败列表（如有）

### C — Flutter 构建（APK + EXE）
- **当前状态**: Flutter SDK 3.27.4 安装在本地，但缺乏 Android SDK（不能本地构建 APK）
- **策略**: 
  1. `git push origin master` 推已提交的 2 个 commit（Reflector 集成 + 端口表同步）
  2. GitHub Actions CI 自动触发 `mobile-apk` job（ubuntu-latest）和 `mobile-exe` job（windows-latest）
  3. CI 完成后，从 GitHub Actions artifact 下载 APK 和 EXE
- **CI workflow 配置**: `.github/workflows/ci.yml`
  - `mobile-apk`: subosito/flutter-action@v2 → flutter build apk --debug → upload artifact
  - `mobile-exe`: subosito/flutter-action@v2 → flutter build windows --debug → upload artifact
- **注意**: 
  - 只推已 commit 的内容（当前工作目录有 36 个未提交的改动文件，不包含在推送范围内）
  - CI 运行时 AI 路由等功能依赖远程 API，测试 job 可能因环境差异有失败

### E — 性能基线
- **范围**: `cloud/app/tests/test_benchmark_core_api.py`（9 项 benchmark）
- **命令**: `python -m pytest cloud/app/tests/test_benchmark_core_api.py --benchmark-only -q`
- **数据用途**: 记录 Reflector 集成后的性能基线，与后续迭代对比

## 依赖关系
- B 和 E 无依赖，可并行
- C 需在 B 和 E 都通过后执行（确认代码健康再推送）

## 风险
- CI 环境与本地环境有差异，APK/EXE 构建可能在 CI 端失败
- 工作目录有 36 个未提交改动文件，推 git 时需要处理
