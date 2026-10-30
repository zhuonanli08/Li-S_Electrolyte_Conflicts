# MISPR 部分复用边界

```text
本课题文献/配方、预算和固定协议
    → 按需调用 MISPR 模块
    → 本课题单位/物种/收敛质检与来源回连
```

2026-10-30 核查上游提交 `efc14e160b97f958aaf78cc2cf499bb578295f80`。MISPR 可以按模块和子工作流调用；不需要启用它的所有性质计算。当前上游源码保存在 Git 忽略的 `work/vendor/mispr/`，未整体安装依赖、未运行计算引擎。

| 复用内容 | 上游入口 | 当前状态 |
|---|---|---|
| Gaussian 各阶段输入参数整理、隐式溶剂配置 | `mispr.gaussian.utilities.inputs.handle_gaussian_inputs` | 已通过我们的 `mispr-inputs` 命令直接调用原始模块，两个真实集成测试通过 |
| Gaussian 优化/频率公共流程、ESP 电荷流程 | `mispr.gaussian.workflows.base.core.common_fw`、`mispr.gaussian.workflows.base.esp.get_esp_charges` | 已核查入口；待依赖、科学协议及平台环境配置后接入 |
| MD 参数与数据文件构造 | `mispr.lammps.workflows.base.lammps_data_fws` | 已核查独立函数；需核对输入物种与参数兼容性 |
| MD 分阶段运行 | `mispr.lammps.workflows.base.lammps_run_fws` | 可显式传 recipe/settings；不直接采用默认温度、时长和资源 |
| RDF、配位数、扩散和聚集分析 | `mispr.lammps.workflows.base.lammps_analysis_fws` | 可选择 analysis_list；底层调用 MDPropTools，尚未安装和验证 |

NMR、氧化还原、完整混合工作流等未纳入当前复用范围。其结果数据库与工作流调度数据库是不同职责：部分结果保存可选择本地文件，但完整 FireWorks 的调度通常仍需其 MongoDB 环境，不能用本项目 SQLite 直接替代。

## 已接入的实际调用

`mispr_adapter.py` 在独立 Python 子进程中 import 原始 MISPR 的输入整理函数，不复制实现，不用 mock 代替。调用前校验锁定模块及所有包初始化文件的 SHA256；源文件 CRLF 规范为 LF 后计算哈希，便于跨平台。输出保留源提交、函数名和输入哈希。

适配器强制每个阶段显式提供泛函、基组、route 参数、核数、内存、checkpoint 与环境。上游默认 Gaussian 输入为 B3LYP/6-31G(d)、24 核、45GB；本课题不自动继承这些默认值。测试使用的 B3LYP/6-31G(d)、2 核、2GB 只是接口样例，不是已冻结的计算方案。

操作入口：`python -m simulation_agent mispr-inputs <明确配置.json>`。需要已锁定源码；缺源码明确失败，不返回伪造的成功结果。结构、能量、预算和科学质检不会因为输入整理成功而自动通过。

在新机器上由 agent 准备源码：

```text
git clone https://github.com/molmd/mispr.git simulation_agent/work/vendor/mispr
git -C simulation_agent/work/vendor/mispr checkout --detach efc14e160b97f958aaf78cc2cf499bb578295f80
```

完整科学模块依赖尚未安装。官方安装说明要求 MolMD 的 pymatgen 分支 `molmd_fix_3-9`，还涉及 FireWorks、OpenBabel、custodian、MDPropTools 等；实际参数化/计算还需要对应的 AmberTools、Packmol、Gaussian、LAMMPS。应在独立环境里部署，不能替换现有文献处理环境的 pymatgen。

## 不能照搬的内容

- `get_binding_energies` 的默认流程会按指定原子索引、`bond_order` 连接两个分子，再优化复合物。它不自动完成本课题要求的多构型搜索；用于 Li+ 配位团簇前须验证生成结构和物种。优先复用优化/频率子流程，保留本课题的构型与能量定义检查。
- 上游结合能输出使用 eV，我们当前结合能函数使用 Hartree；后续适配必须显式转换并保留原始单位，不能按同名字段直接拼接。
- `lammps_analysis_fws` 部分默认轨迹位置指向 `nvt/dump.nvt.*.dump`；与本课题多重复目录对接时需配置/适配路径，并核对时间步和采样单位。
- 上游模块内部的错误恢复可能涉及参数修改；正式接入时须逐项确认是否符合“同协议重试”。

## 来源与署名

MISPR 采用 MIT 许可证。当前直接调用官方源码；若今后复制/修改模块并分发，需保留上游版权及许可证。研究使用时按项目说明引用对应论文，不将上游实现写成本课题自研贡献。

- [模块源码与版本](https://github.com/molmd/mispr/tree/efc14e160b97f958aaf78cc2cf499bb578295f80)
- [安装依赖](https://github.com/molmd/mispr/blob/efc14e160b97f958aaf78cc2cf499bb578295f80/docs/source/installation/dependencies.rst)
- [Gaussian 输入整理](https://github.com/molmd/mispr/blob/efc14e160b97f958aaf78cc2cf499bb578295f80/mispr/gaussian/utilities/inputs.py)
- [MD 子工作流](https://github.com/molmd/mispr/blob/efc14e160b97f958aaf78cc2cf499bb578295f80/mispr/lammps/workflows/base.py)
- [许可证](https://github.com/molmd/mispr/blob/efc14e160b97f958aaf78cc2cf499bb578295f80/LICENSE)
