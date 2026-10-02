# Agent entrypoint

Read this file before **every task or message**, then read [CLAUDE.md](CLAUDE.md), the canonical repository constitution.
Human task authorization controls actions; repository workflow defaults do not authorize remote writes or messages.
Use [the package agent workflow](docs/Developer/Agent-Workflow.md) for scientific work and [SETUP.md](SETUP.md) for governance activation.
Review work also reads [.github/copilot-instructions.md](.github/copilot-instructions.md).
Communicate factually: result first, meaning-bearing emphasis, at most twenty lines unless more is requested.
Bash commands are ACP-hooked. Before other tools, call `acp_check` with the tool name and input; proceed only on `allow`.
The meta-tools `acp_check` and `acp_status` are exempt from that precheck.
