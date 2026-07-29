# mcp-windbg 中文使用说明

> 适用范围：Windows 用户态崩溃分析、程序卡死分析、CPU 异常占用分析、内存异常与泄漏分析，以及 Windows 内核调试。
>
> 项目地址：<https://github.com/svnscha/mcp-windbg>

## 1. 项目简介

`mcp-windbg` 是一个基于 Model Context Protocol（MCP）的 WinDbg 调试服务。它把 AI 客户端与 Windows 调试器连接起来，使 Codex、Claude Code、GitHub Copilot、Cursor 等 MCP 客户端能够通过自然语言执行 WinDbg/CDB/KD 命令，并分析调试输出。

它的底层主要调用：

- `cdb.exe`：用户态 Dump 分析和用户态远程调试。
- `kd.exe`：Windows 内核调试。

因此，`mcp-windbg` 并不只是一个执行 `!analyze -v` 的崩溃分析器。只要 WinDbg/CDB 能分析的问题，它通常都可以通过 MCP 调用相关命令进行辅助分析。

支持的典型场景包括：

- 应用程序崩溃、未处理异常、访问冲突。
- WinForms、WPF、Windows 服务等程序卡死或无响应。
- 进程 CPU 持续占用过高。
- .NET 托管堆或原生堆内存异常增长。
- 托管锁竞争、死锁、线程池阻塞。
- 驱动程序蓝屏、BugCheck 和内核问题。
- 批量分析多个 Dump，寻找共同故障特征。

---

## 2. 能力边界

`mcp-windbg` 的核心作用是：**让 AI 执行调试命令并解释结果**。

它不是完整的性能监控平台，也不会自动完成所有数据采集工作。

| 问题类型 | 是否适合 | 推荐分析材料 |
|---|---:|---|
| 程序崩溃 | 非常适合 | 崩溃时生成的 Dump |
| UI 卡死或死锁 | 非常适合 | 卡死时的完整 Dump，或实时 CDB 会话 |
| CPU 持续过高 | 可以分析 | 间隔抓取的多个完整 Dump |
| .NET 内存泄漏 | 非常适合 | 完整 Dump，最好包含前后两个时间点 |
| 原生堆内存泄漏 | 可以分析 | 完整 Dump，必要时配合 UST/PageHeap |
| 瞬时 CPU 性能曲线 | 不擅长 | 建议使用 WPR/WPA、PerfView |
| 实时内存分配速率 | 不擅长 | 建议使用 PerfView、dotMemory、VS Profiler |
| 自动触发抓取 Dump | 不是核心功能 | 建议使用 ProcDump、任务管理器或 WER |

---

## 3. 环境要求

### 3.1 操作系统

- Windows 10、Windows 11 或 Windows Server。
- Python 3.10 或更高版本。
- 一个支持 MCP 的 AI 客户端。

### 3.2 安装 Windows 调试工具

可以通过以下任一方式安装：

1. 安装 Windows SDK，并选择 **Debugging Tools for Windows**。
2. 从 Microsoft Store 安装新版 WinDbg。

安装后应能够找到：

```text
cdb.exe
kd.exe
windbg.exe
```

常见目录示例：

```text
C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe
C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\kd.exe
```

检查命令：

```powershell
where.exe cdb
where.exe kd
```

如果无法找到，需要将调试器目录加入 `PATH`，或者在启动 `mcp-windbg` 时指定调试器路径。

### 3.3 安装 mcp-windbg

```powershell
python -m pip install --upgrade mcp-windbg
```

验证安装：

```powershell
python -m mcp_windbg --help
```

---

## 4. 配置符号服务器

符号文件对于正确显示 Windows 系统模块、函数名称和调用栈非常重要。

推荐设置：

```powershell
$env:_NT_SYMBOL_PATH = "SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols"
```

永久写入当前用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable(
    "_NT_SYMBOL_PATH",
    "SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols",
    "User"
)
```

说明：

- `C:\Symbols` 是本地符号缓存目录。
- 第一次分析时需要联网下载符号，速度可能较慢。
- 自己编译的程序还需要保留对应版本的 PDB 文件。
- EXE、DLL、PDB 必须版本匹配，否则调用栈可能只显示地址。

---

## 5. 在 Codex 中配置

Codex 的具体 MCP 配置格式可能随版本变化。以下示例展示常见的 TOML 配置方式。

编辑 Codex 配置文件，例如：

```text
%USERPROFILE%\.codex\config.toml
```

添加：

```toml
[mcp_servers.mcp-windbg]
command = "python"
args = ["-m", "mcp_windbg"]

[mcp_servers.mcp-windbg.env]
_NT_SYMBOL_PATH = "SRV*C:\\Symbols*https://msdl.microsoft.com/download/symbols"
```

如果系统中有多个 Python，建议填写完整路径：

```toml
[mcp_servers.mcp-windbg]
command = "C:\\Users\\你的用户名\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"
args = ["-m", "mcp_windbg"]

[mcp_servers.mcp-windbg.env]
_NT_SYMBOL_PATH = "SRV*C:\\Symbols*https://msdl.microsoft.com/download/symbols"
```

重新启动 Codex 后，检查 MCP 服务是否已加载。

> 注意：如果 Codex 运行在 WSL 或 Linux 容器中，而 `cdb.exe` 位于 Windows 主机，则不能直接按普通 Linux MCP 服务调用。最简单的方式是在 Windows 原生环境中运行 Codex 和 `mcp-windbg`，或者把 `mcp-windbg` 作为 HTTP 服务运行在 Windows 调试机上。

---

## 6. mcp-windbg 提供的主要工具

| MCP 工具 | 作用 |
|---|---|
| `list_dumps` | 列出指定目录中的 Dump 文件 |
| `open_cdb_dump` | 使用 CDB 打开用户态 Dump，并执行初步分析 |
| `open_cdb_remote` | 连接用户态 CDB/WinDbg 远程调试服务器 |
| `open_kd_session` | 使用 KD 连接内核调试目标 |
| `run_cdb_command` | 在用户态调试会话中执行任意 CDB/WinDbg 命令 |
| `run_kd_command` | 在内核调试会话中执行任意 KD 命令 |
| `send_ctrl_break` | 中断正在运行的实时调试目标 |
| `close_cdb_session` | 关闭用户态调试会话 |
| `close_kd_session` | 关闭内核调试会话并恢复目标运行 |

每次打开 Dump 或连接实时目标后，通常会返回一个 `session_id`。后续执行命令和关闭会话时，需要使用对应的 `session_id`。

---

## 7. Dump 文件类型

常见 Dump 类型：

| 类型 | 内容 | 适用场景 |
|---|---|---|
| MiniDump | 线程、异常、部分内存 | 基础崩溃定位 |
| Full Dump | 进程完整虚拟内存 | 卡死、托管堆、内存泄漏 |
| Heap Dump | 包含进程堆数据 | 内存问题分析 |
| Kernel Dump | Windows 内核数据 | 蓝屏和驱动问题 |

分析卡死、内存爆高或 `.NET` 托管堆时，优先使用完整 Dump。

---

## 8. 使用 ProcDump 抓取 Dump

ProcDump 是 Sysinternals 提供的进程 Dump 工具。

下载地址：

<https://learn.microsoft.com/sysinternals/downloads/procdump>

### 8.1 手动抓取完整 Dump

```powershell
procdump.exe -accepteula -ma <PID> C:\Dumps\app_full.dmp
```

示例：

```powershell
procdump.exe -accepteula -ma 1234 C:\Dumps\app_full.dmp
```

### 8.2 根据进程名抓取

```powershell
procdump.exe -ma MyApp.exe C:\Dumps\MyApp.dmp
```

### 8.3 程序未响应时抓取

```powershell
procdump.exe -ma -h MyApp.exe C:\Dumps
```

`-h` 用于在窗口进程被判断为挂起时触发 Dump。

### 8.4 CPU 高时抓取多个 Dump

```powershell
procdump.exe -ma -s 5 -n 5 <PID> C:\Dumps\cpu_high
```

含义：

- `-ma`：完整 Dump。
- `-s 5`：每隔 5 秒抓取一次。
- `-n 5`：总共抓取 5 个 Dump。

对于 CPU 高问题，多份 Dump 比单份 Dump 更可靠，因为可以检查某个线程是否持续停留在同一执行路径。

### 8.5 CPU 超过阈值时自动抓取

```powershell
procdump.exe -ma -c 80 -s 10 -n 3 MyApp.exe C:\Dumps
```

含义：当 CPU 使用率达到或超过 80%，并持续满足条件时抓取 Dump。

### 8.6 内存超过阈值时抓取

```powershell
procdump.exe -ma -m 4096 MyApp.exe C:\Dumps
```

含义：当进程提交内存达到约 4096 MB 时抓取 Dump。

---

## 9. 崩溃分析

### 9.1 推荐提示词

```text
请使用 mcp-windbg 分析以下崩溃 Dump：
C:\Dumps\MyApp_crash.dmp

请完成：
1. 执行 !analyze -v。
2. 识别异常类型、异常代码和故障线程。
3. 输出故障线程的原生调用栈和托管调用栈。
4. 检查故障模块及模块版本。
5. 判断最可能的根本原因。
6. 给出进一步验证方法和修复建议。
```

### 9.2 常用命令

```text
!analyze -v
.ecxr
.exr -1
.cxr -1
kb
kv
lm
lmvm 模块名
~
~* kb
```

### 9.3 命令说明

| 命令 | 作用 |
|---|---|
| `!analyze -v` | 自动分析异常或蓝屏信息 |
| `.ecxr` | 切换到异常上下文 |
| `.exr -1` | 显示最近的异常记录 |
| `kb` | 显示当前线程调用栈 |
| `kv` | 显示更详细的调用栈参数 |
| `lm` | 列出已加载模块 |
| `lmvm xxx` | 查看指定模块的版本、路径和时间戳 |
| `~* kb` | 显示所有线程的调用栈 |

### 9.4 .NET Framework 4.8 崩溃

加载 SOS：

```text
.loadby sos clr
```

常用命令：

```text
!threads
!clrstack
!clrstack -a
!pe
!printexception
~*e !clrstack
```

推荐提示词：

```text
这是一个 .NET Framework 4.8 程序崩溃 Dump。
请加载 SOS，并分析：

.loadby sos clr
!threads
!pe
!clrstack -a
~*e !clrstack

请找出未处理异常、内部异常、故障线程和对应业务调用路径。
```

---

## 10. 程序卡死与无响应分析

程序卡死通常不是异常，因此 `!analyze -v` 可能无法直接给出根因。分析重点是线程状态、锁等待和线程之间的依赖关系。

### 10.1 抓取卡死时 Dump

在程序已经卡死时执行：

```powershell
procdump.exe -ma <PID> C:\Dumps\hang.dmp
```

### 10.2 推荐提示词

```text
请分析 C:\Dumps\hang.dmp。

这是一个程序卡死 Dump，不是崩溃 Dump。
请执行并解释：

~
~* kb
!runaway
!locks
!handle

如果是 .NET Framework 4.8，请继续执行：

.loadby sos clr
!threads
~*e !clrstack
!syncblk
!threadpool

请重点判断：
1. UI 线程停在哪里。
2. 是否在等待锁、事件、任务或线程结束。
3. 是否存在两个或多个线程互相等待。
4. 是否使用 Control.Invoke、Dispatcher.Invoke、Task.Wait、Result 或 WaitHandle 导致阻塞。
5. 给出完整的等待链和最可能的死锁原因。
```

### 10.3 WinForms UI 线程常见卡死位置

可能出现的调用栈关键字：

```text
System.Windows.Forms.Application.Run
System.Windows.Forms.Control.Invoke
System.Windows.Forms.Control.SendMessage
System.Threading.Monitor.Enter
System.Threading.WaitHandle.WaitOne
System.Threading.Tasks.Task.Wait
System.Threading.Tasks.Task`1.get_Result
```

如果 UI 线程同步等待后台线程，而后台线程又通过 `Control.Invoke` 同步等待 UI 线程，就可能形成经典死锁。

示意：

```text
UI 线程：等待后台线程结束
    ↓
后台线程：调用 Control.Invoke，等待 UI 线程执行委托
    ↓
UI 线程仍处于等待状态
```

### 10.4 WPF 常见卡死位置

重点检查：

```text
System.Windows.Threading.Dispatcher.Invoke
System.Windows.Threading.Dispatcher.PushFrame
System.Threading.Monitor.Enter
Task.Wait
Task.Result
WaitHandle.WaitOne
```

### 10.5 .NET 锁分析

```text
!syncblk
```

它可以显示：

- 哪些对象被用作同步锁。
- 锁的持有线程。
- 等待该锁的线程数量。
- Monitor 锁竞争情况。

其他可用命令：

```text
!threads
!threadpool
!clrstack
!dumpstack
```

---

## 11. CPU 占用过高分析

CPU 高问题建议抓取多个时间点的完整 Dump。

### 11.1 抓取方式

```powershell
procdump.exe -ma -s 5 -n 5 <PID> C:\Dumps\cpu_high
```

### 11.2 推荐提示词

```text
请批量分析 C:\Dumps\cpu_high 目录中的多个 Dump。

请对比每个 Dump 的线程调用栈，并完成：
1. 执行 !runaway，找出累计 CPU 时间较高的线程。
2. 对所有线程执行 ~* kb。
3. 如果是 .NET Framework 4.8，加载 SOS 并执行 ~*e !clrstack。
4. 找出在多个 Dump 中持续出现于相同调用路径的线程。
5. 判断是否存在死循环、忙等待、高频轮询、递归、频繁 GC 或异常风暴。
6. 输出最可疑线程及其完整调用栈。
```

### 11.3 常用命令

```text
!runaway
~
~* kb
.loadby sos clr
!threads
~*e !clrstack
!threadpool
!eeheap -gc
!dumpheap -stat
```

### 11.4 结果判断原则

- 某线程在多个 Dump 中都位于相同计算函数：可能存在死循环或长时间计算。
- 调用栈不断变化，但始终位于同一业务模块：可能是高频业务计算。
- 大量线程停在 `WaitOne`、`Sleep`、`Monitor.Enter`：这些线程通常不是 CPU 消耗来源。
- GC 线程持续活跃，并且托管堆快速增长：可能是高频对象分配导致 CPU 和内存同时升高。
- 多个 Dump 中反复出现异常创建和抛出路径：可能存在异常风暴。

### 11.5 WinDbg 的限制

`!runaway` 显示的是线程累计 CPU 时间，不等同于精确的函数级采样百分比。

如果需要确定：

- 某个函数占用了多少百分比 CPU。
- CPU 峰值出现的完整时间线。
- 线程调度、上下文切换和磁盘活动。

建议进一步使用：

- Windows Performance Recorder（WPR）。
- Windows Performance Analyzer（WPA）。
- PerfView。
- Visual Studio Performance Profiler。

---

## 12. .NET 内存爆高和内存泄漏分析

### 12.1 抓取完整 Dump

```powershell
procdump.exe -ma <PID> C:\Dumps\memory_high.dmp
```

不要只抓 MiniDump，否则托管堆数据可能不完整。

### 12.2 推荐提示词

```text
请分析 C:\Dumps\memory_high.dmp。

这是一个 .NET Framework 4.8 进程的完整内存 Dump。
请执行：

.loadby sos clr
!eeheap -gc
!dumpheap -stat
!finalizequeue
!syncblk

请完成：
1. 统计托管堆总大小和各代大小。
2. 找出占用内存最大的对象类型。
3. 检查 byte[]、string、Bitmap、DataTable、List、Dictionary 和业务缓存对象是否异常。
4. 检查大对象堆 LOH 是否异常。
5. 检查终结队列是否积压。
6. 对可疑对象抽样执行 !gcroot，找出对象为什么无法释放。
7. 给出最可能的泄漏链路和修复建议。
```

### 12.3 常用命令

```text
.loadby sos clr
!eeheap -gc
!dumpheap -stat
!dumpheap -type 类型名称
!dumpheap -min 85000
!do 对象地址
!gcroot 对象地址
!finalizequeue
!syncblk
!gchandles
```

### 12.4 常用命令说明

| 命令 | 作用 |
|---|---|
| `!eeheap -gc` | 显示托管 GC 堆和各代信息 |
| `!dumpheap -stat` | 按类型统计对象数量和总大小 |
| `!dumpheap -type xxx` | 查找指定类型的所有对象 |
| `!dumpheap -min 85000` | 查找较大的对象，辅助检查 LOH |
| `!do 地址` | 查看指定对象字段 |
| `!gcroot 地址` | 查找对象被哪些 GC 根引用 |
| `!finalizequeue` | 检查终结队列和等待终结对象 |
| `!gchandles` | 检查 GC Handle |

### 12.5 基本分析流程

第一步，查看总体堆情况：

```text
!eeheap -gc
```

第二步，查看对象类型排名：

```text
!dumpheap -stat
```

第三步，选择可疑类型：

```text
!dumpheap -type YourNamespace.YourClass
```

第四步，选择一个代表性对象地址：

```text
!do 0000012345678900
```

第五步，查找持有关系：

```text
!gcroot 0000012345678900
```

`!dumpheap -stat` 只能说明“哪些对象占用较多”，而 `!gcroot` 才能帮助定位“是谁一直引用这些对象”。

### 12.6 常见泄漏来源

- 静态集合或单例缓存持续保存对象。
- 事件订阅后没有取消订阅。
- 定时器、后台线程或 Task 保存业务对象引用。
- `Bitmap`、`Image`、Stream、数据库连接等资源没有 Dispose。
- 大量对象进入终结队列，终结线程处理不过来。
- WPF Binding、DispatcherTimer 或全局消息总线持有对象。
- WinForms 控件已经关闭，但仍被静态事件或线程引用。

---

## 13. 原生内存分析

对于 C/C++、P/Invoke、COM、非托管库或 .NET 进程中的原生内存增长，可以使用：

```text
!address -summary
!heap -s
!heap -stat
!heap -a 堆地址
!vm
```

推荐提示词：

```text
请分析该进程的原生内存使用情况。
请执行：

!address -summary
!heap -s
!heap -stat
!vm

请区分：
1. 托管 GC 堆。
2. 原生 NT Heap。
3. VirtualAlloc 区域。
4. 映射文件和模块。
5. 线程栈。

请指出增长最明显的内存区域，并建议下一步验证方式。
```

如果需要精确定位原生堆分配调用栈，通常需要提前开启 UST：

```powershell
gflags.exe /i MyApp.exe +ust
```

开启后重新启动程序并复现问题，再抓取 Dump。

分析完毕后可以关闭：

```powershell
gflags.exe /i MyApp.exe -ust
```

> 开启 UST 会增加额外内存和性能开销，只应在问题复现期间使用。

---

## 14. 实时调试卡死进程

除了分析 Dump，`mcp-windbg` 还可以连接已经启动的 CDB 调试服务器。

### 14.1 在目标机启动 CDB Server

直接附加到指定 PID：

```powershell
cdb.exe -server tcp:port=5005 -p <PID>
```

也可以启动程序并进行调试：

```powershell
cdb.exe -server tcp:port=5005 C:\Apps\MyApp.exe
```

### 14.2 让 MCP 连接

提示词示例：

```text
请使用 mcp-windbg 连接以下用户态远程调试服务器：

tcp:Port=5005,Server=192.168.1.100

连接后发送 CTRL+BREAK 暂停目标进程，并执行：

~
~* kb
!runaway
.loadby sos clr
!threads
~*e !clrstack
!syncblk

请判断程序卡死原因。分析完成后恢复目标运行。
```

### 14.3 实时调试注意事项

- 暂停进程期间，目标程序会停止运行。
- 生产环境中暂停核心服务可能造成请求超时。
- 防火墙需要允许对应 TCP 端口。
- 建议只在可信局域网或安全隧道中暴露调试端口。
- 不要把调试服务直接暴露到公网。

---

## 15. 批量分析多个 Dump

CPU 高、随机卡死和偶发崩溃经常需要对比多个 Dump。

推荐提示词：

```text
请扫描 C:\Dumps\MyApp 目录中的所有 Dump，并进行批量分析。

请输出：
1. 每个 Dump 的时间、异常代码和故障线程。
2. 相同的故障模块和调用栈特征。
3. 是否存在共同的业务函数。
4. 哪些 Dump 属于同一类问题。
5. 最常见的根因签名。
6. 按优先级给出修复建议。
```

对 CPU 高 Dump，可以要求：

```text
请比较所有 Dump 中的线程栈，找出重复出现的执行路径。
```

对内存 Dump，可以要求：

```text
请比较两个时间点的 !dumpheap -stat 输出，找出数量和总大小增长最快的对象类型。
```

---

## 16. 常用自然语言提示词模板

### 16.1 通用完整分析

```text
请使用 mcp-windbg 分析以下 Dump：
C:\Dumps\app.dmp

请不要只执行 !analyze -v。
请结合线程、调用栈、模块、异常、锁、托管堆和原生堆进行完整分析。

输出格式：
1. 问题摘要。
2. 关键证据。
3. 根因推断。
4. 仍需验证的内容。
5. 修复建议。
```

### 16.2 WinForms 卡死

```text
这是一个 .NET Framework 4.8 WinForms 程序卡死 Dump。
请优先识别 UI 主线程，并检查：

- Control.Invoke 或 BeginInvoke。
- Task.Wait、Task.Result。
- WaitHandle.WaitOne。
- Monitor.Enter。
- Thread.Join。
- 跨线程创建或访问控件。
- UI 线程与后台线程之间的循环等待。

请画出线程等待关系。
```

### 16.3 WPF 卡死

```text
这是一个 WPF 程序卡死 Dump。
请查找 Dispatcher 主线程，并检查：

- Dispatcher.Invoke。
- DispatcherOperation.Wait。
- Task.Wait 和 Result。
- Binding 或布局循环。
- Monitor 锁竞争。
- UI 线程同步等待后台线程。
```

### 16.4 CPU 高

```text
这些 Dump 是进程 CPU 持续过高时每隔 5 秒抓取的。
请比较所有 Dump：

- 找出持续运行的线程。
- 找出重复调用栈。
- 判断死循环、忙等待、异常风暴或频繁 GC。
- 排除处于 Wait、Sleep 和阻塞状态的线程。
```

### 16.5 内存泄漏

```text
这是一个完整内存 Dump。
请先按对象总大小排序，再按对象数量排序。
对排名靠前且可疑的业务类型抽样执行 !gcroot。
不要仅根据对象数量下结论，必须给出引用链证据。
```

---

## 17. 常用 WinDbg/CDB 命令速查

### 17.1 线程和调用栈

```text
~                  列出线程
~3s                切换到 3 号线程
kb                 当前线程调用栈
kv                 详细调用栈
~* kb              所有线程调用栈
!runaway           线程累计 CPU 时间
```

### 17.2 异常分析

```text
!analyze -v
.ecxr
.exr -1
.cxr -1
```

### 17.3 模块和符号

```text
lm
lmv
lmvm 模块名
.symfix
.sympath
.sympath+ 路径
.reload
.reload /f
```

### 17.4 锁和句柄

```text
!locks
!cs
!handle
!handle 0 3
```

### 17.5 .NET Framework SOS

```text
.loadby sos clr
!threads
!clrstack
!clrstack -a
~*e !clrstack
!syncblk
!threadpool
!eeheap -gc
!dumpheap -stat
!dumpheap -type 类型名
!do 对象地址
!gcroot 对象地址
!finalizequeue
!gchandles
!pe
```

### 17.6 原生内存

```text
!address -summary
!heap -s
!heap -stat
!vm
```

---

## 18. 符号加载问题

### 18.1 检查当前符号路径

```text
.sympath
```

### 18.2 设置微软符号服务器

```text
.symfix C:\Symbols
.reload
```

或者：

```text
.sympath SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols
.reload /f
```

### 18.3 检查模块符号

```text
lmvm MyModule
```

如果显示：

```text
*** ERROR: Module load completed but symbols could not be loaded
```

应检查：

- PDB 是否存在。
- PDB 是否与 DLL/EXE 完全匹配。
- 符号路径是否包含 PDB 所在目录。
- Dump 中模块版本是否与本地文件一致。

添加自定义 PDB 路径：

```text
.sympath+ C:\MyApp\Symbols
.reload /f MyApp.exe
```

---

## 19. SOS 加载失败处理

### 19.1 .NET Framework

```text
.loadby sos clr
```

如果失败，可以查找 CLR 路径：

```text
lmvm clr
```

然后手动加载对应 SOS：

```text
.load C:\Windows\Microsoft.NET\Framework64\v4.0.30319\SOS.dll
```

32 位进程可能使用：

```text
C:\Windows\Microsoft.NET\Framework\v4.0.30319\SOS.dll
```

### 19.2 位数必须匹配

- 64 位进程应使用 x64 CDB。
- 32 位进程应使用 x86 CDB。
- SOS 位数必须与目标进程一致。

查看 Dump 中进程位数：

```text
vertarget
```

也可以查看模块信息：

```text
lmvm clr
```

---

## 20. 常见问题

### 20.1 `!analyze -v` 没有发现问题

卡死、CPU 高和内存高通常不是异常，`!analyze -v` 可能只输出有限信息。

这时应明确要求分析：

```text
~* kb
!runaway
!locks
!syncblk
!dumpheap -stat
```

### 20.2 调用栈只有地址

通常是符号缺失或 PDB 不匹配。

执行：

```text
.symfix C:\Symbols
.sympath+ C:\YourApp\Pdb
.reload /f
```

### 20.3 `!dumpheap` 无法使用

可能原因：

- Dump 不是完整 Dump。
- SOS 没有正确加载。
- 调试器位数不匹配。
- Dump 对应的 CLR 数据不完整。

### 20.4 单份 CPU Dump 无法确定高 CPU 线程

单份 Dump 只是一个瞬时快照。建议每隔几秒抓取多个 Dump，并比较调用栈。

### 20.5 分析结果是否完全可信

AI 对调试输出的解释属于辅助判断。重要结论应满足：

- 有明确的调用栈证据。
- 有锁拥有者和等待者证据。
- 有 `gcroot` 引用链证据。
- 有多个 Dump 的重复特征。
- 能通过源码、日志或再次复现验证。

---

## 21. 安全注意事项

Dump 文件可能包含：

- 用户输入内容。
- 密码、Token、连接字符串。
- 数据库内容。
- 文件路径和用户名。
- 内存中的密钥或业务数据。

因此：

- 不要把生产 Dump 上传到不可信服务。
- 优先在本地运行 MCP 和 AI 模型。
- 使用项目前置的过滤脚本功能，对输出进行脱敏。
- 远程 CDB/KD 端口不要直接暴露到公网。
- 分析完成后及时删除不再需要的敏感 Dump。

---

## 22. 推荐工作流程

### 崩溃问题

```text
复现崩溃
  → 生成完整 Dump
  → 准备程序对应 PDB
  → 使用 mcp-windbg 打开 Dump
  → 执行 !analyze -v、.ecxr、调用栈分析
  → 根据源码验证故障位置
```

### 卡死问题

```text
程序卡死
  → 立即抓取完整 Dump
  → 查看所有线程调用栈
  → 确认 UI 主线程
  → 检查 !syncblk、Wait、Invoke、Join
  → 构建线程等待关系
  → 修改同步调用或锁设计
```

### CPU 高问题

```text
CPU 持续过高
  → 每隔 3～5 秒抓取多个 Dump
  → 对比 !runaway 和所有线程调用栈
  → 找到重复运行路径
  → 必要时使用 WPR/WPA 或 PerfView 验证
```

### 内存高问题

```text
内存持续增长
  → 在不同时间点抓取完整 Dump
  → 比较 !dumpheap -stat
  → 找出增长最快的类型
  → 使用 !gcroot 查找持有链
  → 修改缓存、事件、静态引用或资源释放逻辑
```

---

## 23. 总结

`mcp-windbg` 不仅能分析崩溃，还可以用于卡死、CPU 高、内存高、托管死锁、原生内存和内核问题分析。

最重要的使用原则是：

1. 根据问题类型抓取合适的数据。
2. 卡死和内存问题使用完整 Dump。
3. CPU 高问题使用多个时间点的 Dump。
4. `.NET Framework` 使用 SOS 命令分析托管线程和托管堆。
5. 不要只依赖 `!analyze -v`。
6. 让 AI 给出证据、调用栈、锁关系和引用链，而不是只给结论。
7. 对性能时间线问题，结合 WPR/WPA 或 PerfView 使用。

---

## 24. 参考资料

- mcp-windbg GitHub：<https://github.com/svnscha/mcp-windbg>
- mcp-windbg 文档：<https://svnscha.github.io/mcp-windbg/>
- WinDbg 文档：<https://learn.microsoft.com/windows-hardware/drivers/debugger/>
- ProcDump：<https://learn.microsoft.com/sysinternals/downloads/procdump>
- SOS 调试扩展：<https://learn.microsoft.com/dotnet/framework/tools/sos-dll-sos-debugging-extension>
- Windows Performance Recorder：<https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-recorder>
- Windows Performance Analyzer：<https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer>
