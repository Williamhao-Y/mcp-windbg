---
name: windbg-analysis
description: Analyze Windows user-mode dump files with mcp-windbg and generate standardized, evidence-based Markdown reports. Use whenever a user asks to investigate a Windows .dmp for a crash, hang/deadlock, memory growth, high CPU, or a comparison across multiple dump snapshots, and write the report under the workspace output directory.
---

# WinDbg 报告生成

使用 `mcp-windbg` 分析 Windows 用户态转储。统一入口根据任务选择崩溃、卡死、内存暴涨或 CPU 爆高流程；多个时间点的 dump 默认生成一份趋势对比总报告。

## 执行流程

1. 读取工作区 `AGENTS.md`；若其中有报告规则，以其为准。
2. 确认每个 dump 存在；将多快照按 `.lastevent` 的调试时间排序，文件名时间仅作回退。
3. 对每个 dump 调用 `open_cdb_dump` 初检，记录进程、运行时、会话 ID、`.lastevent` 和 `!analyze -v`。
4. 依据用户描述选择一套专项流程；包含多种现象时，以用户指定的主问题为主并在限制中说明次要线索。
5. 对托管转储先加载与目标 CLR 匹配的 SOS。只有成功后才执行托管堆、对象、队列和锁命令。
6. 将同一批快照的原始数据归并到一份报告，按时间线比较指标、线程状态和可疑栈；除非用户明确要求，否则不要按 dump 分拆报告。
7. 按 [专项流程](references/analysis-modes.md) 取证，并按 [报告规格](references/report-spec.md) 写入 `output/`。
8. 验证报告非空、固定章节齐全并关闭所有 CDB 会话。

## 共用初检命令

对每个 dump 至少执行：

```text
.lastevent
!analyze -v
~
~* kbn
!threads
~<faulting-or-suspect-thread>s; !clrstack
lmv m <application-module>
lmv m <relevant-framework-or-system-module>
```

按需执行 `.loadby sos clr`，并在匹配成功后使用 `!syncblk`、`!dso`、`!dumpheap`、`!eeheap -gc`、`!address -summary`、`!runaway`、`!threadpool`、`!gchandles` 或 `!finalizequeue`。不要为了凑模板执行无关命令。

## 结论门槛

- 仅在证据闭环时使用“确诊为”；否则使用“高概率原因是”或“待验证”。
- 将抓取转储的 `0x80000003` 先视为断点现场；除非有异常传播证据，否则不要称为未处理异常。
- 仅在存在等待环或锁拥有者关系时称为死锁。
- 仅在 `ThreadMethodEntry`、队列大小或等价数据支持时称为 `BeginInvoke` 背压。
- 仅在多个快照展示同一进程的持续增长，或单个快照有直接泄漏根证据时称为内存泄漏。
- 单个用户态 dump 不能证明历史 CPU 峰值；仅在捕获到计算热点，或多快照的 `!runaway`/线程身份显示可比时间增量时称为 CPU 热点。
- 将 SOS/CLR 不匹配、缺少 PDB、堆不完整、跨快照进程重启或线程 ID 不可比等情况写入限制。

## 输出规则

阅读 [报告规格](references/report-spec.md) 后再写报告。新增文件必须位于：

```text
output/<topic-or-first-dump-stem>-analysis-YYYYMMDD-HHmm.md
```

同一分钟重跑时追加简短唯一后缀，不得覆盖历史报告。最终回复提供本地报告链接和一句根因摘要。
