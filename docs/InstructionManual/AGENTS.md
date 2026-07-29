# Windows Dump Analysis Report Rules

## Scope

Apply these rules after each Windows user-mode dump analysis. Use `mcp-windbg`
and `open_cdb_dump` for the initial triage. Write one user-facing Markdown
report under `output/`; do not overwrite previous reports.

## Required report format

1. **Title and metadata**: dump filename, analysis date/time, process, runtime,
   debugger commands used, and evidence sources.
2. **Conclusion first**: state the confirmed root cause in one sentence. If the
   evidence is insufficient, label the conclusion as a hypothesis rather than a
   fact.
3. **Analysis process**: present the investigation in chronological steps. Each
   step must include the debugger command, selected raw output, what it proves,
   and how it directs the next command.
4. **Evidence chain**: trace from the faulting/blocked thread through framework
   frames to the application method, control/object, queued work, and concrete
   input when available.
5. **Thread and queue assessment**: distinguish a UI message-loop blockage,
   managed lock deadlock, worker-thread stall, and a queued `BeginInvoke`/
   `Invoke` backlog. For WinForms, inspect `!threads`, `~* kbn`, `!dso`,
   `!dumpheap -type System.Windows.Forms.Control+ThreadMethodEntry`, and the
   relevant `System.Collections.Queue` when the CLR/SOS version permits it.
6. **Modules and limitations**: list relevant application and system modules,
   versions when known, symbol/SOS mismatches, missing heap data, and anything
   that could weaken a conclusion.
7. **Recommendations and verification**: give prioritized, actionable code or
   operational changes and a concrete reproduction/regression test plan.

## Evidence standards

- Never infer a deadlock only from a hung UI; show lock ownership/waits or
  explicitly state that none was found.
- Never infer `BeginInvoke` backlog only from `InvokeMarshaledCallback`; prove
  it with `ThreadMethodEntry`/queue data, or label it as unverified.
- Preserve important commands and concise, relevant output in fenced blocks;
  do not paste indiscriminate full thread dumps.
- State whether numbers were collected in the current run or supplied as a
  previously verified manual analysis of the same dump.
- Use a timestamped filename such as
  `output/<dump-stem>-analysis-YYYYMMDD-HHmm.md`.

## Minimum CDB command sequence

```text
.lastevent
!analyze -v
~
~* kbn
!threads
~<faulting-thread>s; !clrstack
lmv m <application-module>
lmv m <relevant-system-module>
!dso
!dumpheap -type System.Windows.Forms.Control+ThreadMethodEntry
!DumpObj /d <queue-or-entry-address>
```

Use the CLR-matching SOS before the managed-heap commands. If it cannot be
loaded, record that limitation and do not fabricate managed-object results.
