# Codex AI Installation Prompt

Copy the prompt in the language you prefer and give it to an AI tool.

## 中文

```text
请先阅读 GitHub 仓库 https://github.com/Williamhao-Y/mcp-windbg 的 README 和使用手册，然后在当前工作目录安装并配置 mcp-windbg，供 Codex 使用。

要求：
1. 优先采用工作目录内的隔离方案：Python 运行时、虚拟环境、依赖缓存、符号缓存都尽量放在当前目录下；不要修改系统 PATH、注册表、系统 Python，也不要安装全局 pip 包。
2. 不要只阅读 GitHub 仓库后假设已安装：可以按手册从 PyPI 安装发布包；启动方式应使用工作目录内的 Python 执行 `python -m mcp_windbg`。
3. 先检查本机是否已有 `cdb.exe`、`kd.exe`；若存在，配置时显式传入其绝对路径，避免依赖 PATH。
4. 将符号缓存配置在当前目录，例如 `.windbg-symbols`，符号服务器使用微软官方地址。
5. 下载 https://raw.githubusercontent.com/Williamhao-Y/mcp-windbg/main/docs/redact.py 到当前工作目录，文件名保持为 `redact.py`。在 MCP 配置的 `args` 列表中追加 `"--filter-script"` 和该文件的绝对路径；不要使用相对路径，以免 MCP 的启动目录变化导致加载失败。
6. MCP 仅供 Codex 使用。优先写入当前目录的 `.codex/config.toml`；如 Codex 必须通过用户级配置标记当前目录为 trusted 才能加载项目配置，可以这样做，但不要把 mcp-windbg 注册成对所有项目生效的全局 MCP。
7. 安装后验证：私有 Python 能导入 `ssl` 和 `mcp_windbg`，并确认 `python -m mcp_windbg --help` 能正常执行；同时确认 `.codex/config.toml` 的 `args` 中包含 `--filter-script` 和当前目录 `redact.py` 的绝对路径。若 PyPI 自动解析到不兼容的 MCP 2.x，请固定为与 mcp-windbg 兼容的 MCP 1.x。
8. 不要启动 MCP 后一直挂在终端等待协议输入；说明在新开的 Codex 会话中如何通过 `open_cdb_dump` 分析当前目录的 dump 文件。
9. 任何会扩大到用户级或系统级配置、需要下载独立 Python、或无法确定的配置，请先询问我。
10. 完成后报告：改动了哪些文件、`redact.py` 的保存路径、MCP 实际启动命令和完整 `args` 列表、WinDbg 路径、符号缓存位置、验证结果，以及尚未验证的项。
```

配置中的相关片段应与下例等价（路径替换为实际绝对路径）：

```toml
[mcp_servers.mcp-windbg]
command = "E:\\work\\my-project\\.venv\\Scripts\\python.exe"
args = [
  "-m",
  "mcp_windbg",
  "--cdb-path",
  "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\cdb.exe",
  "--kd-path",
  "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\kd.exe",
  "--symbols-path",
  "srv*E:\\work\\my-project\\.windbg-symbols*https://msdl.microsoft.com/download/symbols",
  "--filter-script", "E:\\work\\my-project\\redact.py"
]
```

## English

```text
First read the README and user guide for the GitHub repository https://github.com/Williamhao-Y/mcp-windbg, then install and configure mcp-windbg in the current working directory for use by Codex.

Requirements:
1. Prefer an isolated setup within the working directory: keep the Python runtime, virtual environment, dependency cache, and symbol cache in or as close as practical to the current directory. Do not modify the system PATH, registry, system Python, or install global pip packages.
2. Do not assume the server is installed merely because you read the GitHub repository. You may install the published package from PyPI according to the guide. The launch method must use the working-directory Python to run `python -m mcp_windbg`.
3. First check whether `cdb.exe` and `kd.exe` already exist on this machine. If found, pass their absolute paths explicitly in the configuration instead of relying on PATH.
4. Configure the symbol cache in the current directory, for example `.windbg-symbols`, and use Microsoft's official symbol server.
5. Download https://raw.githubusercontent.com/Williamhao-Y/mcp-windbg/main/docs/redact.py into the current working directory, keeping the filename `redact.py`. Append `"--filter-script"` and this file's absolute path to the MCP configuration `args` list. Do not use a relative path, because the MCP server's startup directory can vary.
6. The MCP server is for Codex only. Prefer writing to `.codex/config.toml` in the current directory. If Codex must use a user-level setting to mark the current directory as trusted before it can load project configuration, that is allowed; however, do not register mcp-windbg as a global MCP server for every project.
7. After installation, verify that the private Python can import both `ssl` and `mcp_windbg`, and that `python -m mcp_windbg --help` succeeds. Also confirm that `.codex/config.toml` includes `--filter-script` and the absolute path to the current directory's `redact.py` in `args`. If PyPI resolves an incompatible MCP 2.x release, pin a compatible MCP 1.x release.
8. Do not leave the MCP server running in a terminal waiting for protocol input. Explain how to use `open_cdb_dump` in a new Codex session to analyze dump files in the current directory.
9. Before any action that expands into user-level or system-level configuration, requires downloading a standalone Python runtime, or has uncertain configuration, ask me first.
10. Report when finished: files changed, the saved `redact.py` path, the actual MCP launch command and complete `args` list, WinDbg paths, symbol-cache location, validation results, and anything not yet verified.
```

The relevant configuration must be equivalent to the following, with actual absolute paths:

```toml
[mcp_servers.mcp-windbg]
command = "E:\\work\\my-project\\.venv\\Scripts\\python.exe"
args = [
  "-m",
  "mcp_windbg",
  "--cdb-path",
  "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\cdb.exe",
  "--kd-path",
  "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\kd.exe",
  "--symbols-path",
  "srv*E:\\work\\my-project\\.windbg-symbols*https://msdl.microsoft.com/download/symbols",
  "--filter-script", "E:\\work\\my-project\\redact.py"
]
```
