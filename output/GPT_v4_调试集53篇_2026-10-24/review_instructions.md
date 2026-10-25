# 交叉复核指令（独立预测全部保存后再交给不同代理）

**数值处理说明（依方案既定分工）**：评分对象是“冻结提取 + 固定程序判向”的文本流水线，不把模型写的“数值方向待程序复算/不判”当作最终弃权。如果精确A/B数值、同条件和指标语义均正确，先核对 `validation/numeric_directions.json` 的程序判向后对该方向评分；这不是根据参考修正预测。单组数值不能自动拼成配对；近似/界限/冲突不得强判。作者定性仍单列。报告必须说明原始模型预测与程序派生方向的区别。

你是复核者，不是该组论文的首次提取者。用户授权 GPT 交叉核对。按现行方案 §5.7、§14.1a 对首次冻结预测逐项核对原文，比较旧 Claude 参考并找漏项。不得修改 `independent_predictions/`、原人工格、人工 gold 或旧参考。

可读：`sources/{ID}.json`、`independent_predictions/{ID}.json`、manifest 指向的旧参考，以及四篇已有 v4 样例作为参考（S11/S21/S33/S39）、`validation/` 的机械问题。不要把旧参考当作绝对真值。图仅依据本轮代码读图的有效结果；不凭目测填值。

保存 `cross_reviews/{ID}.json`：

```
{
 "paper_id":"...", "reviewer":"...",
 "prediction_sha256":"对当前冻结原文件字节计算SHA256",
 "all_prediction_units_reviewed":true,
 "reference_and_source_reviewed":true,
 "coverage_notes":"具体审阅范围和缺失SI/图限制",
 "units":[
   {"id":"T/<原测试id>","category":"测试及条件","verdict":"TP|FP|UNRESOLVED",
    "reason":"原文核对理由，不能仅称与参考一致", "evidence_ids":[],
    "reference_ids":[], "new_correct":false},
   {"id":"T/<原测试id>/<原结果id>","category":"方向","verdict":"...",
    "reason":"...","evidence_ids":[],"reference_ids":[],"new_correct":true},
   {"id":"M/<原机制id>","category":"机制","verdict":"...",
    "reason":"...","evidence_ids":[],"reference_ids":[],"new_correct":false}
 ],
 "missing":[{"id":"FN1","category":"测试及条件|方向|机制","description":"未被预测覆盖的原文事实",
              "evidence_ids":[],"reference_ids":[],"reason":"为什么属于漏提；排除与现有单位重复"}],
 "reference_errors":[{"reference_id":"旧参考单位","reason":"旧答案错在哪里","evidence_ids":[]}],
 "unresolved":[],"suggested_corrections":[]
}
```

每个测试、每个结果、每个机制都必须出现一次，不能跳过难项。`TP` 必须正确覆盖该单位的关键归属、方向和条件；若原文给了条件但预测漏写或写错，该测试不是完整正确。一个错误单位计 FP，正确目标未被其他单位覆盖时另记 FN，不能只罚 FP 而不计漏。不要因原文未报告条件就判 FP。

结果的数值判向按代码/5%规则与作者定性分列核对；CE不套5%阈值。下列额外 verdict 可用，但必须给具体理由：`SKIP_ABSTENTION`（明确不判或仅图未读，没有提出方向）、`SKIP_DUPLICATE`（重复同一语义单位，说明保留哪个单位）、`SKIP_NONSCORING`（物性观测或单配方数值，不是A/B方向）。合理不判不当成正确方向来抬高精确率；若原文有应能判断的方向仍要记 FN。不要把所有定量结果都计为方向：没有配对或根本没有提出方向的，按上述规则处理。

机制逐句看完整上下文，核实不是转述他人、推测是否被改为确定结论、过程类别有没有多标、性质变化与测试有无牵强挂接。存在引文不自动等于转述；本研究对自身结果的说明可带引文。科学事实错误与编号纯格式问题分别记录。

找漏：先核旧参考每个候选是否原文支持、是否已被预测语义覆盖，再遍历正文结果/讨论/结论与 SI 方法、相关图注找新增漏项。全文通用引言背景不是必须全部收录的本篇机制。有效参考可含预测新发现的正确项，标 new_correct；这样不会因旧参考漏了而把新正确项当FP。只报告实际发现的漏项，别写“可能漏了”然后任造 FN。

不确定不能猜：UNRESOLVED单列，给所需证据。没有完成原文审阅不能把 `reference_and_source_reviewed` 标 true。最终输出是 AI 辅助参考下的暂定调试结果，未经用户逐项人工确认。
