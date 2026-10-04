# 价格显示修复交付记录

模式：Lite；沟通方式：连续执行；当前阶段：S1；状态：通过；更新：2026-10-04
未关闭阻断项：无；延期告警/风险：ISSUE-002（S3 环境告警）；待决策：无；下一步：交付完成，环境告警由后续环境维护处理。

## 需求重述
我理解你的需求是：价格 0 显示 0.00，null/undefined/NaN 显示 —，正常价格保留两位小数。
范围：本目录 price.js 与本记录；不做：联网、安装依赖、其他目录修改、commit/tag；保留已有他人工作。假设：沿用现有 Number(value).toFixed(2) 转换行为，不扩大其他输入语义。
交付物：price.js、delivery-notes.md、检查证据及恢复副本。

## 验收基线（实施前冻结）
| 需求 | 验收项 | 操作 | 预期 | smoke | 状态 |
|---|---|---|---|---|---|
| R-001 | AC-001 | npm test：formatPrice(0) | 0.00 | 是 | PASS |
| R-002 | AC-002 | npm test：null/undefined/NaN | 各为 — | 是 | PASS |
| R-003 | AC-003 | npm test：formatPrice(12.3) | 12.30 | 是 | PASS |
| R-003 | AC-004 | 额外直接断言 12、12.345、-1.2 | 12.00、12.35、-1.20 | 是 | PASS |
| R-004 | AC-005 | 完整 npm test | 全部测试通过，测试数保持 1 | 是 | PASS |

## 阶段与方案
S1 输入为现有实现与 price.test.js；任务为复现、最小修复、完整回归与交付；退出标准为全部 AC 通过且 ISSUE-001 关闭。
接口 formatPrice(value) 返回字符串，不改变模块结构或状态。将 truthy 判断改为 nullish/NaN 明确判断，其余 Number(value).toFixed(2) 保持现状。替代方案为先统一数值转换再判断 NaN，会扩大字符串等输入语义，当前不采用。收益为满足零值显示；代价为一个条件判断调整，无性能测量。
失败路径仍用 — 处理指定缺失值/NaN；其他输入转换行为保持现状。回退用本目录 recovery/price.js.before.txt 恢复 price.js，再运行 npm test；回退会恢复原有零值缺陷，尚未执行。

## 问题与处理（此表为当前状态权威来源）
| 编号 | 级别/类型 | 证据与根因 | 方案与决策来源 | 状态 |
|---|---|---|---|---|
| ISSUE-001 | S1 错误 | 修复前 npm test exit 1，0 返回 —；已验证 !value 把 0 判为缺失 | 显式判断 null/undefined/NaN；用户授权最小修复、连续执行 | 已关闭 |
| ISSUE-002 | S3 告警 | npm 输出 Unknown env config http-proxy | 环境告警，不改变其他目录或环境；记录保留 | 延期 |

## 决策记录
2026-10-04：用户明确授权直接改此目录并连续执行；单阶段 Lite，不新增确认关卡。验收标准在修改前冻结，未降低标准。不建立 commit/tag；当前目录不是 Git 仓库，使用哈希与文本恢复副本。

## 历史复现证据
Node v24.19.0，npm 11.9.0；修复前 npm test：1 个测试，0 PASS，1 FAIL，退出码 1。price.test.js:2 的零值断言实际 —，预期 0.00。历史 FAIL 不计入最终验收计数。
初始 price.js SHA-256：a0d8f04bddea2c4a73e26aa62fe93585b3d4fa050b467e9727d494024ff064aa。
price.test.js SHA-256：72390f762906b6413643cd03a06289edc70cc585b8b330a5239b7b7cb3cd97e0。
package.json SHA-256：afbdfa341178e339e6e0cbec9af5762d432c80af6ebe8b81945267f570234bff。

## 结论与限制
阶段 S1 通过；需要决定的事：无。已完成 price.js 一行最小修复；现有测试及 package.json 未修改。优化手段为显式空值/NaN 判断，代价为单行调整；未测量性能。未做其他输入语义扩展、联网、安装依赖、其他目录修改、commit/tag。独立复核：不适用。项目仅声明 test 脚本，无构建/lint/类型检查脚本（N/A）。若实现扩大、多模块或新架构决策则升级 Standard，高风险/不可逆操作升级 Full。


## 当前验收与检查证据
对象为当前 price.js；命令均在本目录运行。
- AC-001/002/003/005：`npm test`（脚本 `node --test`），退出码 0；1 个测试，1 PASS，0 FAIL；无跳过、取消或待办。完整日志见 test-results.txt。恢复副本创建后实际测试数仍为 1。
- AC-004 及全部指定输入：Node assert.equal 直接调用 formatPrice；退出码 0，8/8 断言通过，完整输出见 acceptance-results.txt。输入分别为 0、null、undefined、NaN、12.3、12、12.345、-1.2。
- 当前验收计数：5 PASS，0 FAIL，0 BLOCKED，0 NOT RUN；构建/lint/类型检查 N/A（package.json 无对应脚本）。
- ISSUE-001 修复第 1 轮：已验证 truthy 判断误判零值，换成 `value == null || Number.isNaN(value)`；重跑原失败项和全部 smoke 后已关闭。
- 本轮价格分支检查未发现其他代码错误；ISSUE-002 为 npm 环境告警，未影响退出码与结果，未修改范围外配置。
- 最终 price.js SHA-256：fd46e470e2e5de9e935b9df4f005e3569ef83c245450038dd56b553a2fb0596c；测试与配置哈希与初始值相同。
- 检查点清单见 checkpoint.sha256；可用 `sha256sum -c checkpoint.sha256` 校验。恢复材料 recovery/price.js.before.txt 为原始文件副本，后缀 .txt，不被 node --test 发现。需要回退时仅将其内容恢复到 price.js，再运行 npm test；未实际回退，验收仍基于修复版。
- `diff -u recovery/price.js.before.txt price.js` 显示仅一个条件判断修改；该命令退出码 1 表示有预期差异，不是检查失败。
