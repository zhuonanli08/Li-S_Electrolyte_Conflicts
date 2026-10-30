# ComBat DME 首轮验证

```text
锁定公开小样 → 本地参考表核对（已完成）→ DME 频率输入（已准备）
  → 核实超算软件/价格/资源 → 限时单任务 → 原始日志与账单 → 能量/频率比较
  → 完整结合能流程 → DOL/DME 配方 MD（后续，尚未开始）
```

用户通过聊天协作，不需要自行编程或安装软件。当前阶段没有超算作业、收费 API 或新计算性质。

## 当前选样与交付

- 首个运行候选：DME（1,2-dimethoxyethane，CAS 110-71-4，C4H10O2），16 个原子、电荷 0、单重态。选择理由是结构和参考能量明确、可与后续常见 DOL/DME 配方衔接；不声称已找到所有候选中的最低成本体系。
- `source.lock.json`：固定 ComBat 提交 `caa1130df2b4feeb9eaafe1565af8e1a4283986a` 的 25 个文件，共 256,118 字节。保存 SHA256 与 Git blob 哈希；原始文件在忽略目录 `simulation_agent/work/combat_source/`。
- `preparation/reference_audit.json`：15 项作者参考数据的一致性核对通过，涉及两组结合能（Hartree→eV/kcal/mol）、五组配位数、五组扩散系数和一个扩散比。不代表新计算、轨迹重分析或实验验证。
- `preparation/dme_reference.xyz`：从作者 JSON 原样提取的坐标，不是本项目生成的新构型。
- `preparation/dme_frequency.gjf`：待平台核查的 Gaussian 频率任务。B3LYP/6-31+G*、GD3、气相及频率 route 取自实际参考文件；在公开优化结构上运行，不重复几何搜索。参考 Gaussian 16 C.01；电子能量 −308.880563451 Hartree，仅为作者参考值。
- `preparation/mispr_request.json`、`mispr_normalized.json`：实际经过本项目 MISPR 适配器的参数；并未启动 MISPR 完整执行工作流。
- `preparation/pilot.json`：任务范围、资源草案、未满足条件和结果核查要求。准备参数中保留 opt 是现有适配器的接口要求，本轮只导出了 freq 任务，不授权隐含执行 opt。

## 首轮边界与验收

资源草案是 2 核、申请 4 GB 内存（Gaussian 使用 3072 MB）、30 分钟。若平台按申请核时计费且没有更高最低分配，单次上界为 1 核时。这个数字不是人民币报价；单价、最低节点分配、额外许可费、实际可用资源及费用上限仍未知。没有生成可提交调度脚本，没有提交命令，`can_submit=false`。只执行一次；超时/内存不足时记录失败，不自动扩大资源或重复收费运行。

本轮检验已知结构的计算链路与费用，不验收多构型搜索、完整结合能或 MD。运行后应保留原始输入/日志、软件版本、任务号、CPU/墙钟耗时、实际费用，并检查能量及全部振动频率。暂设电子能量差超过 1e-5 Hartree 时触发调查；这是复现调查阈值，未经过实跑校准，不是物理模型准确度或自动通过标准。来源摘要中的 `Minimum` 不能替代独立检查。

2026-10-30 后续授权：用户明确允许首个小样在价格仍未知时试跑，运行后核对实际费用，优先确认 Gaussian 可用。此前“未知价格必须先确认”的用户等待项不再适用于该单样本；仍不得扩大批量、自动重试或提高资源。Gaussian 路径、授权和运行环境仍须先确认。通用 Slurm 渲染器的价格闸门暂未改动；真正提交前须记录此单样本例外，不把未知价格填成零或伪造 billing_verified。

## 日志接收与初检（2026-10-30 新增）

`inspect-frequency` 接收普通 Gaussian 单作业 harmonic 日志，检查正常结束、原子数、电荷/多重度、完整 route 回显、42 个唯一有序振动模式、负/零频与参考能量差，并保存输入和原始日志 SHA256。`preparation/frequency_screen.json` 锁定本轮准备输入哈希。支持 D 指数；格式不支持、缺失、重复、拼接日志都转复核。测试夹具为人工合成，不是 Gaussian 实跑。

```powershell
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent inspect-frequency simulation_agent/benchmarks/combat_dme/preparation/frequency_screen.json simulation_agent/work/dme_pilot/engine.log --input simulation_agent/benchmarks/combat_dme/preparation/dme_frequency.gjf --mode production --out simulation_agent/work/dme_pilot/frequency_screen.json
```

命令要求原始日志已经收回，不会提交计算或自动获取文件，且拒绝覆盖已有报告。筛查通过返回退出码 0、需要复核返回 3、输入/写入错误返回 2。所有检查通过也只标为 `SCREEN_PASSED_PENDING_REVIEW`，不能进入结合能计算的 `PASSED` 输入。仍需核对真实输入与日志对应、元素/坐标、梯度和驻点、软件版本以及账单。频率规则依据 [Gaussian 官方振动分析说明](https://gaussian.com/wp-content/uploads/dl/vib.pdf)，不是完整科学质检。

## 已识别的复现问题

1. README 简写 B3LYP/6-31+G*；实际频率输入和作者脚本含 `EmpiricalDispersion=GD3`，试算必须保留。
2. 结合能重算与总表分别相差约 0.000639、0.000654 kcal/mol，在 0.001 kcal/mol 的表间核对容差内；eV 差约 5.4–5.5e-7。差异与单位换算常数精度相容，尚未追溯作者制表常数，不强称逐位相等。
3. 配位数 CSV 有同名的不同原子位点列。脚本逐列相加，不能用字典读法丢掉重复列。`Li - S (PS)` 对应末端硫列，不是所有硫原子。
4. 该版本仓库清单未发现原始 `.log/.out/.dump/.lammpstrj/.dcd/.xtc` 文件。公开 JSON/统计 CSV 不能用来声称原始日志解析或轨迹分析已通过。
5. `scripts/run_md.py` 引用旧 MISPR 入口，以及 `Li.pdb`、`TFSI.pdb`、`DOL.pdb` 等大小写与当前仓库不一致的路径。`epsilon.py` 查找 DOL 行，但锁定 `data.csv` 没有 DOL 行。作者脚本只静态查看，未执行；在解决这些问题前不能原样全库运行。
6. MD 参考体系是 DOL/DME 1:1（体积比）、1 M LiTFSI、0.25 M Li2S8；总表中的电导和黏度属于无多硫化物的另一个体系。原 `nvt.in` 写有 298.15 K、1 fs、5,000,000 步（5 ns），不能缩成短测试后仍宣称完成该物性的复现。
7. 单体的完整 route 与复合物摘要详略不同；同样的 functional/basis 字段只能作初步检查，不能替代完整协议和频率审查。

## Agent 接力命令

准备脚本只用标准库；真实 MISPR 输入整理还要求 `MISPR_REUSE.md` 所述的锁定源码可用。

```powershell
# 新机器加 --download，按 lock 下载公开参考文件；不执行作者脚本。
# --out 必须是新目录，避免覆盖本轮证据。
& 'D:\anaconda\envs\papertrail\python.exe' -m simulation_agent.combat_benchmark --download --out simulation_agent/work/combat_repeat_01
& 'D:\anaconda\envs\papertrail\python.exe' -m unittest discover -s simulation_agent/tests -q
```

用户下一步只需在方便时自行登录并行平台，并告知“已登录”或给出实际使用的入口。不要发送密码。随后由 agent 核对软件、队列及收费规则，确定这一个任务的实际费用上界，再准备限时提交。

## 来源与归属

- Atwi, R.; Rajput, N. N. *Guiding maps of solvents for lithium-sulfur batteries via a computational data-driven approach*. Patterns (2023), DOI: [10.1016/j.patter.2023.100799](https://doi.org/10.1016/j.patter.2023.100799)。
- [固定版本 ComBat](https://github.com/rashatwi/combat/tree/caa1130df2b4feeb9eaafe1565af8e1a4283986a)：数据说明为 CC BY 4.0，仓库 LICENSE 为 MIT，两份原文均保存在本地原始文件中。公开坐标/数值来自作者，本项目只做提取、重排、核对及资源参数调整。
- MISPR 引用与复用边界见 `simulation_agent/MISPR_REUSE.md`。不得把公开参考数值计入本项目新计算结果。
