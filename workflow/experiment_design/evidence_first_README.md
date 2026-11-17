# 先补证、再选择的单案例工作流

## v2.2 当前实现（2026-11-16）

用户最新明确：token用于能推进判断的必要工作，不为机械少用而省略核对，不反复铺长方案。问题及核心判别应适合多数锂硫实验室；`routine_discrimination`先论证常规方法可区分什么及其限制，`minimum_equipment`区分常规核心和可选高端增强。科学意义仍优先，不能因容易做而立题，也不能将容量/极化/EIS相关性当作唯一归因。run02的局部光谱—转化速率候选由用户否定，已撤回，不再审旧题或补参数。

实跑暴露了方法抓取错误：v2.0曾把摘要和参考文献当作方法窗口，导致ACS Cent. Sci. 2017的“catholyte”用语被赋予过强的初始体系含义。v2.1起改抓实际活性物、电极制备和装配语句，保留原位XRD用S正极的方法；不得仅凭单词认定预配正极液。另将预算预留不足作为明确停止状态，不抛成通用程序失败。v2.2在此基础上加入普遍可实施性要求。18项检查通过；工程检查不认证科学语义。

run02完成两次真实调用，32429 tokens，独立审查未启动；OpenAlex Q0为429，Q1按规则未请求。当前会话另完成两条网页查询，核读PNAS 2023相关正文与S电池方法，未计入run02模型输入。run03仅在最新用户纠正后重新提炼一次，不重跑旧题审查；结果和实际用量以其outcome/receipt为准。公开正文自动获取代码完成单元验证，但本轮因OpenAlex限流未走通真实端到端取文，不宣称已验证成功。

最新纠偏：以S为目标电池初始活性物；先识别所引体系和变量角色，再论证观察关系和认识增量。`system_map`保留配方—观察—作者解释—适用条件；未知不补猜。多硫化物演变放在中间状态；外加正极液、预沉积、换液实验另记机理模型及迁移边界。语义由科学角色审查，程序只检查结构及显式角色，不能阻止模型把错误因素误标成配方。

候选生成0–2条且不排序；全部补证后可在`lineage/reformed_candidates`淘汰、合并、新增，重建候选使用N编号。先写现象、已有解释边界、认识变化，实验另列。全部hold时实验/配方/干预数组必须为空；审查后停止，不为跑满五轮修补参数。新候选依据不足时保留hold及重启条件，不冒称已充分查新。

默认按G01内排序纸号等距固定抽12篇，保存完整摘要和system_scope，不截头尾。样本和未读范围冻结，不能称59篇完整比较。可用`--sample-size`改变起始范围；`--token-ceiling`默认50000，最多5次调用，调用前保守预留，实际用量来自回执；这是观测停止预算，不是服务端硬上限。

文献依据不限本地库。每条OpenAlex查询取前3条完整题录/摘要，候选全部原始引用均回正文/SI，并为每查询再追最多一条新来源：本地有则复用，否则尝试OpenAlex公开链接。匿名单次请求、最大8 MB/60页；失败留档，PDF只抽文本，网页可能只是摘要页，未读图或完整SI不外推。公开文件留在本轮`public_sources`，不更改原文缓存。公开链接身份未核对或被拒绝时，不绕过访问限制。

运行示例（解释器用本机实际路径）：

```powershell
python scripts/evidence_first_design.py init --run output/new_v2_run --sample-size 12 --token-ceiling 50000
python scripts/evidence_first_design.py run --run output/new_v2_run
python scripts/evidence_first_design.py verify --run output/new_v2_run
python scripts/test_evidence_first_design.py
```

本轮路径：`output/体系变量角色修正小试_2026-11-16/`。run01为网络失败尝试，run02为两阶段实跑，run03_routine_reframe为用户追加纠正后的一次重新提炼。结论以其回执和根目录进度为准。修改前副本和哈希在`before/`。以下为v1历史实现与实跑说明，不作为v2的当前样本、预算或字段定义。

run03已完成：14463 tokens，零候选；三次已完成调用合计46892 tokens，均有原始回执，未执行独立审查。已撤回run02问题，不将其conditional_draft状态恢复为当前推荐。最新处置在本轮根目录`current_status.json`，易读结论为`summary.html`。新字段、工程测试与这次零候选结果不证明已具备可靠科学发现能力。

## v1 历史说明

现行入口：`scripts/evidence_first_design.py`。这是已选大矛盾范围内的下游工作流；当前 `init` 固定读取本项目 G01 和其59篇上游逐篇摘要，尚不是任意数据库的通用批处理入口。规则以根目录主方案、细则和最新进度为准。

## 实际执行顺序

1. LLM根据上游摘要摘录提出2–3个候选，不排名、不选中；登记各候选待改变的判断、停止条件及英文查询，另给一个范围内开放查询。
2. 程序冻结全部查询，逐项访问OpenAlex，各取首页前5条。按DOI回查本地正文/SI；每候选最多一个原有来源、一个外检命中且本地有全文的来源。所有补证尝试结束后才允许选择；访问失败与无命中分别记载。
3. 新上下文比较全部候选、记录判断是否改变，选出或改写一个具体问题，并生成初版实验方案。比较与初版设计为同一次调用，不能称作两次独立运行。允许全部暂缓。
4. 新上下文审查：最多3个实质异议，最多1条补证查询。
5. 保存补证，修订逐条回应；另一上下文再审，保留未解决问题和停止/重启条件。

合计最多5次模型调用、5个OpenAlex查询任务；网络传输失败最多尝试两次。每轮提示、证据、schema、原始模型响应、结果、实际用量、异议和修改都留档。不同上下文使用同一模型，不等于独立领域专家。

问题用语要求写清体系、变量和响应，记录英文文献短语、中文含义与来源。程序检查出处及文字对应，模型审查语境和测量含义；这不等于专业术语或科学结论已获专家认证。用户举例和历史答案不放入规则或任务模板。

## 运行与离线核验

需要Python 3.10+、Codex CLI、项目指定模型权限、现有ChatGPT文件式登录 `auth.json`，以及本项目上游资料和正文缓存。临时登录副本随角色结束清理；不调用付费模型API，不自动注册OpenAlex。系统钥匙串登录、其他数据库路径与跨机器部署尚未适配。

在项目根目录执行；本机 `python` 须替换为实际解释器路径：

```powershell
python scripts/evidence_first_design.py init --run output/new_evidence_first_run
python scripts/evidence_first_design.py run --run output/new_evidence_first_run
python scripts/evidence_first_design.py verify --run output/new_evidence_first_run
python scripts/test_evidence_first_design.py
```

`init` 冻结输入、代码及辅助模块哈希。已接受步骤只在输入一致时复用；失败保留日志并停止，不自动重抽科学答案。代码改变后禁止直接续跑旧目录。不要手工修改原始科学输出以通过校验。

本次完成的历史运行使用归档版本核验：

```powershell
python scripts/evidence_first_design.py verify --archived --run output/候选补证后选择_OpenAlex小试_2026-11-16/run01
python scripts/audit_evidence_first_pilot.py
```

预算固定9万输入＋输出tokens，调用前预留保守估算，调用后记录实际量；这是观察与停止预算，CLI没有本程序可用的服务端严格总token上限，单次用量仍可能超出估算。以摘要摘录和少量原文窗口压缩输入，可能遗漏选题线索；不能把节省token等同科学质量不变。

## 本次实跑与版本边界

`output/候选补证后选择_OpenAlex小试_2026-11-16/run01` 已完成5次真实调用，输入＋输出74434 tokens，最终再审暂缓。原始科学输出、引用窗口、查询响应和修订全部保存。阅读入口为同目录 `summary.html`，详细原始结果为 `report.html`，审计为 `run_audit.json`。

实际实跑从v1.0修复到v1.0.1：共享schema别名误将普通ID限制为证据ID，导致模型显式使用替代映射。依据模型原文映射，仅规范9个标识符字段，无新增模型调用、无科学文字改写；原schema、响应及修复记录保留。最终 `validated_runner.py` 与运行清单哈希一致。不能称为无故障的一键验证。

原冻结清单生成后追加了一条 `cycle_closed`，仅根事件日志哈希不符；离线审计确认旧日志字节与追加前完全一致，原冻结清单未改写。完成后的 `final_scientific_freeze.json` 另行冻结全部原产物。旧 `outcome.json` 保留初版问句；最终问题以 `stages/revise/result.json` 为准，审计分别保存两者。

当前v1.1另修补英文检索字段、空页眉片段过滤、最终问题摘要及冻结顺序，11项工程测试通过。**v1.1新增修补没有再做模型实跑**，以避免追加消耗和反复试到期望答案。现有测试和一例带修复实跑，不证明批量稳定性、查新充分性或显著优于直接问AI。

## 检索与证据边界

OpenAlex采用公开 `/works?search=…` 接口，保存URL、参数、时间、原始响应、返回排名和稳定ID。401/403/429后停止外检，不绕过访问限制；具体可用性依服务当前政策。仅首页前5条，不作全面召回承诺。题录/摘要用于发现候选文献，不替代全文方法判断。参见[OpenAlex搜索说明](https://help.openalex.org/api/searching/)和[访问认证说明](https://help.openalex.org/api/authentication/)。

本地阅读只打开明确DOI对应正文/SI，保存原文件哈希、行号和窗口；不重新审读或重判全库。同预算并不保证同等证据质量；单一DOI、机械窗口及上游缩略摘要仍可能带来选题偏差。当前不含自动下载全文、前后向引文扩展、完整SI审读或有效的全面新颖性排查。

科学角色通过临时目录与独立CLI上下文隔离，关闭shell、web及不需要的MCP，使用简短科研指令替代编码助手指令；配置依据[官方配置说明](https://learn.chatgpt.com/docs/config-file/config-reference.md)。父会话知道历史答案，故只是角色输入隔离的开发测试，不是完全独立盲测。

方法上采用 literature-review 与 hypothesis-generation skills 中的检索留痕、证据分层、竞争解释、可区分预测与修改记录。引用技能库方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。技能指导不等于本流程已被论文验证。
