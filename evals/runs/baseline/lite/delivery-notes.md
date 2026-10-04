# 价格显示修复交付记录

模式：Lite；沟通方式：连续执行；状态：通过；更新：2026-10-04
当前阶段：S1 价格格式修复；未关闭问题：无；待决策：无；下一步：交付完成。

## 需求重述
我理解你的需求是：价格 0 必须显示 `0.00`；null、undefined、NaN 显示 `—`；正常价格显示两位小数。
范围：本目录 `price.js` 和交付记录；保留现有测试与其他工作；不联网、不安装依赖、不修改其他目录、不 commit/tag。假设：正常价格延续已有 Number 转换行为，额外输入类型不扩展验收范围。

## 验收基线（实施前冻结）
交付物：`price.js`；阶段：S1；以下全部为 smoke，退出前完整运行 `npm test`。

| 需求 | 验收 | 操作 | 预期 | 状态 | 证据 |
|---|---|---|---|---|---|
| R-001 | AC-001 | formatPrice(0) | 0.00 | PASS | price.test.js / npm test 与补充断言 |
| R-002 | AC-002 | formatPrice(null/undefined/NaN) | 全部为 — | PASS | price.test.js / npm test 与补充断言 |
| R-003 | AC-003 | formatPrice(12.3)，补充检查 12、-2.5 | 12.30、12.00、-2.50 | PASS | npm test 与 node 断言 |
| R-004 | AC-004 | npm test | 现有完整测试集通过 | PASS | 1 个测试通过，0 失败，退出码 0 |

## 问题与修复方案（修改前记录）
| 编号 | 级别/类型 | 证据 | 方案与决策来源 | 状态 |
|---|---|---|---|---|
| ISSUE-001 | S1 错误 | 基线 npm test 退出码 1，0 返回 —，预期 0.00 | 用 null/undefined 的空值检查和 Number.isNaN(value) 替代 truthy 判断；用户明确授权本目录最小修复 | 已验证关闭 |
| ISSUE-002 | S3 告警 | npm 输出 Unknown env config "http-proxy"，提示未来主版本不再支持 | 环境配置超出修复范围，记录；现有测试正常执行 | 已记录，未修改环境 |

正常值继续经过 Number(value).toFixed(2)，保持接口和转换方式。替代方案是重写格式器，改动更大，无必要。预期收益是恢复 0 的正确显示，不做性能收益宣称；风险为额外输入类型行为未另行定义。验证：原失败项、全部 smoke 和完整现有测试。
退出标准：全部验收 PASS，ISSUE-001 验证关闭。回退：恢复原判断 `if (!value) return "—";`。

## 检查证据
检查均在本目录执行，对象为本次修复的 price.js 与原有 price.test.js。

| 检查 | 实际结果 | 状态 |
|---|---|---|
| 修改前 npm test | 退出码 1；1 测试失败；'—' !== '0.00'；price.test.js:2:27 | FAIL（保留基线） |
| 修改后 npm test（完整测试与全部 smoke） | 退出码 0；1 测试通过；0 失败、取消、跳过 | PASS |
| node:assert/strict 边界检查 | 8 条断言通过：0、-0、null、undefined、NaN、12.3、12、-2.5 | PASS |
| node --check price.js；node --check price.test.js | 无语法错误，退出码 0 | PASS |
| 构建、lint、类型检查 | package.json 只定义 test，无对应脚本 | N/A |

修复轮次 1：假设是 truthy 判断吞掉 0；一行改动后原失败消失，完整测试及 smoke 通过，根因已验证。没有改动验收基线或测试。

## 结论与限制
阶段通过；需要用户决定的事：无。4 项验收 PASS，0 FAIL，0 BLOCKED。仅改动 price.js 的一行判断并新增本文，原有 package.json 和 price.test.js 保持原样。告警仅为 ISSUE-002 环境配置提示；本轮检查范围内未发现其他错误。未联网、安装依赖、修改其他目录或执行 commit/tag。

本目录不在 Git 仓库中；按用户要求不进行 commit/tag。检查点为下列修复后代码快照，可直接恢复本次产物（不包含他人的其他工作）；回退本次代码修改只需恢复上述原判断。

```js
exports.formatPrice = function(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return Number(value).toFixed(2);
};
```

独立复核：N/A（Lite 单一格式显示修复，无支付流程变更）。本任务只验证约定价格输入，其他输入类型未扩展验收；没有构建、lint 或类型检查脚本。升级条件：超出 3 文件、引入新架构或不可逆操作时升级 Standard；本轮未触发。
