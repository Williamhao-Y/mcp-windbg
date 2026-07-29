# mcp-windbg：面向 WinDbg 崩溃分析的 MCP 服务

[![CI](https://github.com/svnscha/mcp-windbg/actions/workflows/ci.yml/badge.svg)](https://github.com/svnscha/mcp-windbg/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-windbg)](https://pypi.org/project/mcp-windbg/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)

`mcp-windbg` 是一个 [Model Context Protocol（MCP）](https://modelcontextprotocol.io/) 服务，将 AI 客户端与 Windows 调试器连接起来。它通过 `cdb.exe` 分析用户态转储和远程用户态目标，通过 `kd.exe` 连接内核调试目标；AI 可以调用真实的调试器命令并基于结果协助分析。

> 这不是自动修复工具。它是对 WinDbg/CDB/KD 的 Python 封装，最终诊断结论仍应结合转储、符号和源码人工确认。

<!-- mcp-name: io.github.svnscha/mcp-windbg -->

## 能力

- 分析 `.dmp`、`.mdmp`、`.hdmp` 崩溃转储，并执行 `!analyze -v`、调用栈、模块和线程等初步诊断。
- 连接由 `cdb -server` 提供的用户态远程调试服务，可按需中断并执行调试命令。
- 使用 KDNET、命名管道或串口连接内核调试目标。
- 在已打开的会话中执行 WinDbg/KD 命令，例如 `kb`、`!heap`、`lm` 和 `!process 0 0`。
- 同时管理多个会话；每个打开操作都会返回一个会话 ID。
- 扫描、筛选和比较目录中的多个转储文件。
- 可选的文本过滤脚本，用于在参数和工具输出离开本机前脱敏。
- 支持默认的本地 `stdio` MCP 传输，以及 streamable HTTP 传输。

## 前置条件

- Windows。
- 已安装 [Debugging Tools for Windows](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) 或 Microsoft Store 版 [WinDbg](https://apps.microsoft.com/detail/9pgjgd53tn86)，并具备 `cdb.exe`；使用内核调试还需要 `kd.exe`。
- Python 3.10 或更高版本。
- 一个支持 MCP 的 AI 客户端，例如 Codex、Claude Code、GitHub Copilot、Claude Desktop、Cursor、Windsurf 或 Cline。

服务会尝试自动发现调试器。若调试器路径不在常见位置，建议显式传入 `--cdb-path` 和（需要内核调试时）`--kd-path` 的绝对路径，避免依赖系统 `PATH`。

## 安装与启动

### 使用 Codex 安装（推荐）

需要让 AI 工具在当前工作目录为 Codex 安装本 MCP 时，请完整提供以下提示词：

```text
请先阅读 GitHub 仓库 https://github.com/Williamhao-Y/mcp-windbg 的 README 和使用手册，然后在当前工作目录安装并配置 mcp-windbg，供 Codex 使用。

要求：
1. 优先采用工作目录内的隔离方案：Python 运行时、虚拟环境、依赖缓存、符号缓存都尽量放在当前目录下；不要修改系统 PATH、注册表、系统 Python，也不要安装全局 pip 包。
2. 不要只阅读 GitHub 仓库后假设已安装：可以按手册从 PyPI 安装发布包；启动方式应使用工作目录内的 Python 执行 `python -m mcp_windbg`。
3. 先检查本机是否已有 `cdb.exe`、`kd.exe`；若存在，配置时显式传入其绝对路径，避免依赖 PATH。
4. 将符号缓存配置在当前目录，例如 `.windbg-symbols`，符号服务器使用微软官方地址。
5. MCP 仅供 Codex 使用。优先写入当前目录的 `.codex/config.toml`；如 Codex 必须通过用户级配置标记当前目录为 trusted 才能加载项目配置，可以这样做，但不要把 mcp-windbg 注册成对所有项目生效的全局 MCP。
6. 安装后验证：私有 Python 能导入 `ssl` 和 `mcp_windbg`，并确认 `python -m mcp_windbg --help` 能正常执行。若 PyPI 自动解析到不兼容的 MCP 2.x，请固定为与 mcp-windbg 兼容的 MCP 1.x。
7. 不要启动 MCP 后一直挂在终端等待协议输入；说明在新开的 Codex 会话中如何通过 `open_cdb_dump` 分析当前目录的 dump 文件。
8. 任何会扩大到用户级或系统级配置、需要下载独立 Python、或无法确定的配置，请先询问我。
9. 完成后报告：改动了哪些文件、MCP 实际启动命令、WinDbg 路径、符号缓存位置、验证结果，以及尚未验证的项。
```

### 手动安装

最简单的安装方式：

```powershell
python -m pip install mcp-windbg
python -m mcp_windbg --help
```

推荐由 MCP 客户端启动服务，而不是手工运行后停在终端中等待 stdio 协议输入。可用的主要参数如下：

| 参数 | 用途 |
| --- | --- |
| `--cdb-path PATH` | `cdb.exe` 的完整路径。 |
| `--kd-path PATH` | `kd.exe` 的完整路径。 |
| `--symbols-path PATH` | 符号搜索路径；未提供时使用 `_NT_SYMBOL_PATH`。 |
| `--no-dump-dir-symbols` | 不自动把转储所在目录加入符号路径。 |
| `--filter-script PATH` | 加载处理工具文本的本地脱敏脚本。 |
| `--timeout SECONDS` | 设置命令和连接的基准超时时间。 |
| `--transport {stdio,streamable-http}` | 选择传输方式，默认 `stdio`。 |

Microsoft 公共符号服务器的典型配置为：

```text
SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols
```

将其中的 `C:\Symbols` 换成你希望存放符号缓存的本地目录。MCP 进程启动时也可以通过 `--symbols-path` 传入相同的值。

## MCP 客户端配置示例

下面是使用项目内虚拟环境的通用 `stdio` 配置。将路径替换为本机实际路径；若已发现调试器，保留绝对路径参数。

```toml
[mcp_servers.mcp-windbg]
command = "E:\\work\\my-project\\.venv\\Scripts\\python.exe"
args = [
  "-m", "mcp_windbg",
  "--cdb-path", "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\cdb.exe",
  "--kd-path", "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\kd.exe",
  "--symbols-path", "SRV*E:\\work\\my-project\\.windbg-symbols*https://msdl.microsoft.com/download/symbols"
]
```

不同客户端的配置文件格式可能不同，但启动命令应保持为：

```text
<项目内 Python> -m mcp_windbg [服务参数]
```

不要把普通 `stdio` 服务手工启动后长期挂在终端中；MCP 客户端会负责启动它，并通过标准输入输出交换协议消息。

## 常用工具与使用方式

| 工具 | 作用 |
| --- | --- |
| `list_dumps` | 列出目录中的转储文件。 |
| `open_cdb_dump` | 打开并初步分析用户态崩溃转储。 |
| `open_cdb_remote` | 连接用户态远程调试服务。 |
| `open_kd_session` | 连接内核调试目标。 |
| `run_cdb_command` / `run_kd_command` | 对指定会话执行调试命令。 |
| `close_cdb_session` / `close_kd_session` | 关闭会话；关闭 KD 会话会继续目标机执行。 |
| `send_ctrl_break` | 中断正在执行的实时调试会话。 |

在新开的、已加载此 MCP 的 Codex 会话中，可以直接提出类似请求：

```text
使用 open_cdb_dump 分析当前工作目录中的 app.dmp；先执行默认初步诊断，
再说明异常代码、故障线程、最可疑的调用栈帧和还需要的符号或源码。
```

`open_cdb_dump` 返回的 `session_id` 应传给后续的 `run_cdb_command` 和关闭工具。例如，可以继续要求 Codex 对该会话执行 `kb`、`lm` 或 `!heap`。



## 符号、隐私与安全

- 符号缓存可能很大，应放在有足够空间且受版本控制忽略的目录中。
- 转储和调试输出可能包含内存、路径、用户名、令牌或其他敏感信息。需要将输出发给外部 AI 服务时，请先评估数据合规性；可使用 `--filter-script` 进行文本脱敏。
- streamable HTTP 传输不带认证。除非有额外的认证保护，否则仅绑定 `127.0.0.1`，不要暴露给不可信网络。
- 内核调试会影响被调试目标的运行状态，应只在可控环境中操作。

## 更多文档

- [英文 README](README.md)
- [入门指南](docs/getting-started.md)
- [命令行参考](docs/reference/cli.md)
- [工具参考](docs/reference/tools.md)
- [客户端配置](docs/reference/clients.md)
- [故障排除](docs/troubleshooting.md)

## 许可证

[MIT](LICENSE)
