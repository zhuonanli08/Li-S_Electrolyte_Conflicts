# Codex 云端与 GitHub

2026-11-17：已将本机入口从 Claude 改为 Codex/ChatGPT。仓库仍为 [zhuonanli08/Li-S_Electrolyte_Conflicts](https://github.com/zhuonanli08/Li-S_Electrolyte_Conflicts)。

## 已核实与待完成

- 本机 `codex login status` 显示使用 ChatGPT 登录。
- 账号可见可运行的默认云环境，但环境返回的仓库列表为空；这不证明 GitHub 已连接。
- GitHub 已连接：认证账号 zhuonanli08，仓库 ID 1425575474，已实际读取 main 的进度.md。接口返回 pull/push 权限，本次仅验证读取，未写入。专用环境已关联此仓库 main，但当前工具仍返回 runnable=false；原因未确定，不据此断言用户未发布。观察到的环境配置 ID 单独记录，尚未作为 CLI 可运行 ID 使用。
- 当前会话 HTTP_PROXY/HTTPS_PROXY 指向 `127.0.0.1:7890`，连接失败；一次不使用代理的只读 `git ls-remote` 成功。未改系统代理或全局 Git 配置，也未验证写入权限。
- 尚未启动云任务、提交或推送，未完成云端端到端验证。

## 使用

双击 `双击上云.bat`：显示 Codex 地址、仓库和交接任务。到 [Codex](https://chatgpt.com/codex) 使用 ChatGPT 登录并连接 GitHub，选择本仓库；当前官方界面也支持在聊天里选择 Work in → Cloud。脚本不自动打开窗口、覆盖剪贴板或上传本地文件。

`to_cloud.ps1 -DryRun` 是纯预览。连接并核验环境后，可使用 `-Submit -EnvironmentId <真实环境ID> -Task <明确任务>` 通过本机 Codex CLI 提交。该操作会启动云任务；本轮未执行。CLI 是本机已安装版本的接口，环境兼容性仍需实际核验。

双击 `双击同步回本机.bat` 列出云任务；`from_cloud.ps1 -TaskId <id>` 预览差异，增加 `-Apply` 才应用到干净工作区。不自动拉取、合并或提交 main。

云端只看到已提供的仓库版本，不会自动得到本机未提交结果、被忽略的 PDF/SI、历史归档或提取数据。当前还有其他聊天在本地进行提取，因此本次不采用旧脚本的 `git add -A` 整库快照。资料同步应针对具体云任务另行选择明确范围。

旧脚本及其 SHA256 保存在 `历史版本/整理记录_2026-11-17/修改前/`。旧版 `-DryRun` 在检查前仍会提交甚至推送，现已修正。

官方依据：[Codex Cloud](https://learn.chatgpt.com/docs/cloud)。配置保存于同目录 `codex-cloud.json`，不含凭据。

