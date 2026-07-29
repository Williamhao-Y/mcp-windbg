# 专项流程

## 崩溃

目标：确定异常来源、故障线程、应用调用点和涉及模块。

```text
!analyze -v
.exr -1
.ecxr
~<faulting-thread>s; kb
~<faulting-thread>s; !clrstack
!pe
lmv m <faulting-module>
lmv m <application-module>
```

检查异常码、异常记录、寄存器上下文、原生/托管栈、首个应用帧和模块版本。只有异常确实传播到未处理边界时，才将 `!analyze -v` 的异常称为崩溃根因。

## 卡死或死锁

目标：区分 UI 消息循环阻塞、锁死、同步跨线程调用、异步队列背压和业务线程等待。

```text
!threads
~* kbn
!syncblk
~<suspect-thread>s; !clrstack
!dso
!dumpheap -type System.Windows.Forms.Control+ThreadMethodEntry
!dumpheap -type System.Collections.Queue
!DumpObj /d <relevant-entry-or-queue>
```

记录所有可疑线程的等待 API、锁拥有者、线程单元模型和调用环。WinForms 条目必须按 `synchronous`、`isCompleted`、`caller`、`resetEvent` 解释，不能仅凭 UI 无响应定性死锁。

## 内存暴涨

目标：在同一进程实例的多个快照中确认增长池、主要对象类型和可能保留根。

对每个快照执行：

```text
!eeheap -gc
!dumpheap -stat
!dumpheap -type <top-suspect-type>
!gchandles
!finalizequeue
!address -summary
!threads
```

对候选对象按需执行：

```text
!DumpObj /d <object-address>
!gcroot <object-address>
!DumpArray /d <array-address>
```

比较对象数量、总大小、Gen 2/LOH、私有提交和根路径。不要仅因单个大对象就称为泄漏；需要持续增长、不能合理回收的根或明确的未释放资源链路。

## CPU 爆高

目标：识别捕获时仍在执行的热点线程，并在多快照可比时量化累计 CPU 增量。

对每个快照执行：

```text
!runaway
~* kbn
!threads
~<top-cpu-or-runnable-thread>s; !clrstack
~<top-cpu-or-runnable-thread>s; !clrstack -a
!threadpool
!syncblk
```

将 `!runaway` 的用户/内核时间与 OS 线程 ID 一起记录。只对同一进程实例、可映射的同一线程比较增量。若单快照的线程停在计算循环、解析、序列化、GC 或特定业务方法，可报告“捕获时热点”；若没有时间序列或运行栈证据，只能报告“无法确认历史 CPU 爆高根因”。

## 证据门槛

| 结论 | 必要证据 |
| --- | --- |
| 双向同步 `Invoke` 死锁 | 至少两线程均在 `Control.Invoke`/`WaitOne`；两侧未完成条目为 `synchronous=1`、`isCompleted=0`；可说明等待环 |
| 异步 UI 队列背压 | `ThreadMethodEntry` 或 `Queue._size` 明显增长；存在 `synchronous=0` 条目和持续生产或未完成证据 |
| 内存泄漏 | 同一实例多快照中同类对象/堆持续增长，且有 `!gcroot`、句柄、静态集合或资源链路支持保留原因 |
| CPU 热点 | 捕获时热点线程栈，或可比较多快照中同一线程的 `!runaway` 时间增量及稳定栈 |
| `Monitor` 死锁 | `!syncblk` 显示锁拥有者和相互等待，或有等价的锁证据 |

不满足必要证据时，只能写“待验证”或“高概率”，不得确诊。
