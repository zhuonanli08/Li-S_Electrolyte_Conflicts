# DFT / MD 自动化 agent：工作流框架

```text
文献体系候选 → 身份/组成核对 → 协议与预算确定 → 计算软件/超算接口
                                             ↓
任务登记 → 输入生成 → 提交/续算 → 日志解析 → 科学质检 → 结果与文献关联
```

2026-10-30，版本 0.2.0。依据现行课题方案 §7.17 开始实施。用户没有计算经验及现成脚本，有“并行”和通过 Xshell 连接的教学服务器，均要求少花钱；已授权先试一个样本、记录费用后再决定规模。最新指示：登录信息晚些提供，当前先把整体工作流搭好。

**当前接入位置（2026-10-30 已更新）**：用户已在应用内浏览器自行登录并行，并通过 WebSSH 进入绑定的浙江超算云 M6。只读核实了 Slurm、开放队列 `amd_512`、公共 ORCA 6.0.1 与 LAMMPS 可执行文件；当前 shell 未加载 module，Gaussian 在限定目录搜索中未找到。控制台子账号资源关联/配额与 SSH 可登录状态不一致，单价、最低分配、实际额度和提交权限尚不能确认。详情见 [平台观察记录](platforms/paratera_m6.observed.json)。未运行引擎、未提交试算。用户对单样本试算的意图保留，后续先核实资源和费用边界，不重复询问是否要做小样。

**完整阶段依赖与本地演示已搭好，还不能自动完成真实 DFT/MD。** 已有 Gaussian/ORCA 输入渲染、三种引擎日志初检、单节点 Slurm 脚本导出。尚无真实构型生成、力场参数化、轨迹分析、SSH/Slurm/PBS 提交与轮询、LLM API；渲染/解析还需真实软件验证。没有提交超算、安装计算软件或生成科学数值。软件、物理方法和预算都仍待确认。

## 当前可用功能

- **MISPR 部分复用**：已直接调用锁定版本的 Gaussian 输入整理函数；其他子流程的适用边界见 [MISPR_REUSE.md](MISPR_REUSE.md)。这不代表已接入它的真实 DFT/MD 执行。
- `doctor`：检查 Python 与本机 PATH；未发现命令不等于超算未安装。
- `plan`：检查输入合同，列出缺失项、流程阶段、质检项目和资源申请上界。
- `register/list/show`：SQLite 持久登记和查询，保留状态、重试次数、来源与事件。
- `estimate`：支持核时/GPU 时/节点时计价，计入独立重复和最大尝试次数；未知单价返回未知，不返回零元。
- 缓存键覆盖结构、配方、温度、多硫化物状态、软件/协议/分析版本，以及 DFT 电荷/自旋/构型、MD 种子/重复。不同论文可回连同一任务。
- 测试专用状态流验证成功待质检、缺项转复核、文件哈希检查、有限同协议重试。`synthetic` 与 `production` 分开，测试不能启动真实计算。
- DFT 13 阶段、MD 15 阶段（两个规划重复）的依赖图和整链演示；跳过完成阶段，失败阻塞下游，上游产物变化使依赖结果转待复核。
- `render-dft`：显式给出坐标、电荷/自旋、方法关键词和资源，渲染 Gaussian/ORCA 单作业文件并检查电子数奇偶性；不选择方法。
- `render-slurm`：核实平台后导出限时脚本；按计费资源和单价计算费用上界并与上限比对，不调用 sbatch。LAMMPS 多核 MPI 启动待平台适配，当前仅导出单核试验脚本。
- `inspect-log`：Gaussian/ORCA/LAMMPS 单作业日志初检，正常退出最多标为 SUCCESS_PENDING_QC。
- `analysis.binding_energy`：相同协议、单位且已通过对象质检的孤立优化片段电子能量汇总；检查元素与电荷守恒，不混入 E_int 或溶剂化自由能。

所有写入在 `simulation_agent/` 内，默认数据库位于被 Git 忽略的 `work/`。不修改已有文献候选、冻结结果或人工 gold。

## 本机使用

用户只需在聊天中说明需求，无需自己操作命令。以下命令供 agent 接力及开发使用，在项目根目录运行：

```powershell
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent doctor
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent plan simulation_agent/examples/dft_draft.json
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent register simulation_agent/examples/dft_draft.json
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent list
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent demo
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent workflow simulation_agent/examples/dft_draft.json --out simulation_agent/work/plans/dft
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent workflow simulation_agent/examples/md_draft.json --out simulation_agent/work/plans/md
& 'D:\anaconda\envs\papertrail\python.exe' -m unittest discover -s simulation_agent/tests -v
```

仅依赖 Python 标准库，要求 Python 3.10+；已用本机 Python 3.11 验证。根 Anaconda 的 Python 3.7 不适用。示例中的空值必须保留到来源明确，不能为消除提示随便填参数。

## 输入与状态约定

示例是待讨论草稿，不是选定的小样或可执行输入。`protocol.status=frozen` 表示协议在外部完成科学审查；当前程序仅检查必填项存在，不证明该协议、SMILES、力场或几何正确。生产后端接入前，无论合同是否齐全，`can_submit` 始终为 false。

```text
缺输入 → NEEDS_REVIEW
合同齐全 → PENDING → RUNNING → SUCCEEDED_PENDING_QC → PASSED
                          ↓                      ↓
                        FAILED              NEEDS_REVIEW
                          ↓
              有原因、未超过次数、同协议 → PENDING
```

本版 `start_synthetic`、`finish_synthetic`、`qc` 仅供程序测试。测试里的布尔质检标记不属于科学质检实现，不能接收真实数据后直接宣称计算合格。真实实现须用输出文件、单位、解析器版本和测量指标产生质检证据。

`demo` 的所有阶段执行模拟处理器，`numeric_results` 始终为 null，最终状态为 DRY_RUN_PASSED，不执行物理计算。DFT：身份→协议→预算→构型→复合物/片段优化→构型质检→复合物/片段能量→基组误差→结合能→科学质检→归档。MD：身份→协议→预算→参数化→组成计量→建盒→最小化→各重复的平衡/生产→结构/输运分析→科学质检→归档。阶段数不等于实际作业数，多构型和单点任务仍需展开。

当前支持状态恢复和审计，尚未实现计算软件 checkpoint 的续算。RUNNING 任务重启后仍为 RUNNING，不盲目重新提交。以后须先向调度器查询作业是否存在，再决定续算。

SQLite 仅用于本地单一控制端，不部署到超算共享文件系统。计算节点运行引擎；控制端接收并核验产物后更新数据库。注册同一科学任务时保留第一次资源/重试设置，新增来源合并；资源修改接口尚未实现。缓存按输入中已规范化的标识去重，尚不能自行识别化学同义词或等价 SMILES。

`work/tasks.sqlite3` 是任务登记表；`work/demo/<workflow_id>/workflow.sqlite3` 是演示阶段表；真实阶段回写任务表的适配仍待实现。配置模板 `examples/slurm_site.template.json` 和 `examples/dft_render.template.json` 保留空值，渲染器拒绝未配置项及覆盖旧文件。通用输入渲染预留 25% 调度内存，ORCA 剩余内存按核分配；这不是内存充足保证。Slurm 算价只包含计算费；最低分配、计费取整、许可/存储等额外费用必须在标记 billing_verified 之前核实，不能视为账户总扣费保证。

## 接入真实计算的下一步

2026-10-30：已开始 [ComBat DME 首轮复现准备](benchmarks/combat_dme/README.md)。25 个公开参考文件已锁定；15 项表间核对通过；使用真实 MISPR 输入整理并导出一个 DME 频率任务。尚未跑 Gaussian、MD 或提交超算。该基准准备优先于直接扩展文献配方计算；已知旧接口/文件名/原始轨迹缺失等问题见小样说明。

1. 确认超算名称/网址、可用软件和计费方式；先估价再定费用上限。
2. 按 `pilot_candidates.json` 讨论小样；补齐结构、组成基准与参考参数。该文件由 `prepare_pilot.py` 从本地原文缓存生成，不依赖旧提取结论。
3. 有许可证且平台提供时沿用 Gaussian；否则核实 ORCA 可用性。MD 优先评估 LAMMPS。这是方案延续的候选路线，不是已冻结的软件决定。
4. 接入一个 DFT 后端和一个 MD 后端：输入模板、版本检查、资源限制、调度状态、幂等提交、checkpoint、原始输出解析。
5. 实现真实质检：DFT 收敛/构型/物种与能量定义；MD 参数覆盖、电中性、平衡、重复/分块收敛。用户已要求单样本试算；先核实计费、配置限额和运行时限，再在该范围内执行，不能据此扩大批量。若采用 UI 提交，按相应工具的交易确认规则处理。
6. 先用一个小任务测实耗，再估算整个小样批次；通过科学验证后扩展，不直接全库开算。

首轮建议把配位/RDF作为 MD 优先目标，扩散作为通过采样验证后的目标；黏度、电导率、介电响应与多硫化物探针逐步扩展。具体模拟时长和收敛阈值由试算决定。

## 技术参考

- [MISPR 官方仓库](https://github.com/molmd/mispr)：已下载锁定源码并直接复用一个输入整理模块，未安装完整计算栈；后续按 MISPR_REUSE.md 的子模块边界接入。
- [LAMMPS 日志文档](https://docs.lammps.org/Run_output.html)：运行结束时的耗时和统计信息可辅助预算；正常结束不代表科学收敛。
- [LAMMPS MSD 文档](https://docs.lammps.org/compute_msd.html)：扩散分析须正确处理周期边界、参考位置和续算；不能仅拿一个斜率自动判定可靠。
- 输入/调度格式：[ORCA 官方](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/input.html)、[CSC Gaussian](https://docs.csc.fi/apps/gaussian/)、[LAMMPS 命令行](https://docs.lammps.org/Run_options.html)、[Slurm sbatch 官方](https://slurm.schedmd.com/sbatch.html)。实际版本以用户平台为准。

参考核查日期：2026-10-30。现行科学方案仍以根目录唯一方案文件为准。

## 验证记录

现为 0.2.1，57 项本地测试通过、无跳过（其中两个直接调用真实上游 MISPR 输入整理函数）；DFT 13/13、MD 15/15 阶段演示跑通。两份草稿仍为 NEEDS_REVIEW、尝试次数 0。详情见 `verification.json`。不覆盖量化精度、MD 收敛、远程调度或真实账单。首次测试因 Windows 沙箱临时目录无法创建 SQLite 失败，改用本项目 `work/tests/` 后通过。

本机 papertrail 环境有 NumPy，未发现 RDKit/ASE；暂未安装新包。三维结构生成仍需补齐，不能把草稿中的分子名称直接当作已验证的计算结构。
