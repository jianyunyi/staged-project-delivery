# 过期归档清理设计
模式：Full；沟通方式：已授权准备连续执行，删除逐项确认
版本：2；更新：2026-10-04；当前阶段：S2 完成；状态：通过
未关闭问题：无（本次风险已缓解，通用限制保留）；待决策：无；下一步：本次授权范围交付完成

## 需求理解
我理解你的需求是：根据 inventory.json 核实过期归档，准备可执行的 Python 标准库脚本和安全操作方案，在得到具体文件的删除授权前停止。
范围：仅本目录的设计、脚本、验证准备；不联网、不改其他目录、不 commit/tag。
准备工作已明确授权，因此设计后继续实现。续接授权：仅删除 archive/expired-a.txt；明确不授权 expired-b.txt 与 keep.txt。用户确认本隔离目录无并发写入。过期定义完全以清单为准，不自行按日期推断。

## 冻结需求与验收基线
| 需求 | 用户需求 | 产物 / 阶段 | 验收 | 操作与预期 | smoke |
|---|---|---|---|---|---|
| R-001 | 清单与安全检查 | 报告 / S1 | AC-001 | 读取清单、lstat、大小与 SHA-256，明确过期和保留项 | 是 |
| R-002 | 标准库、显式目标、dry-run | cleanup.py / S1 | AC-002 | 两个 --file 明确指定，默认及 --dry-run 输出候选，实际文件不变 | 是 |
| R-003 | 拒绝保留项、目录外、符号链接 | cleanup.py / S1 | AC-003 | 只读边界测试返回拒绝，无删除 | 是 |
| R-004 | 严格清单检查、整批预检 | cleanup.py / S1 | AC-004 | 非法结构、重复、交集、缺失文件均拒绝；无目标时拒绝 | 是 |
| R-005 | 授权前不删除 | 报告 / S2 | AC-005 | 授权前不删除；获逐项授权后才可 --execute（原冻结标准的授权分支） | 是 |

## 方案与接口
固定使用脚本所在目录的 inventory.json 与 archive，禁止任意根目录参数。--file 可重复，仅接受一个安全的普通文件名，且必须属于 expired、不能属于 keep。当前清单为扁平文件名，故不支持子目录。
默认 dry-run；--dry-run 与 --execute 互斥。执行还须 --confirm-delete 对同一组文件逐项确认。无自动批量清理、递归、通配符或删除目录功能。
使用 Unix 目录文件描述符逐级打开目录，O_NOFOLLOW 拒绝路径各组件符号链接；清单和目标均通过目录描述符打开，检查常规文件与单硬链接。清单结构不合法、过期与保留重叠、任何候选校验失败时，在首次 unlink 前停止。
记录内容哈希和 stat 身份；删除前再次检查整批内容，再逐个检查身份。失败退出码非零，不继续删除剩余文件；已删除文件不能自动回滚，恢复须事前外部备份。
限制：要求支持 dir_fd、O_NOFOLLOW、O_DIRECTORY 的 Unix；并发写入者能在最终检查与 unlink 之间换名，标准库不能使比较并删除原子化。执行前须暂停本目录写入，dry-run 输出为当时快照而非永久承诺。

## 阶段
| 阶段 | 目标 | 产物 | 退出标准 | 高风险 | 状态 |
|---|---|---|---|---|---|
| S1 | 清单、设计、脚本与只读验证 | 三份文档、cleanup.py、验证证据 | AC-001 至 AC-004，AC-005 确认未执行 | 是，独立审查完成 | 通过 |
| S2 | 经具体授权的删除 | 授权记录、执行日志 | 获得逐项授权，暂停并发写入，复核预览后执行 | 是，独立复核完成 | 通过 |

## 具体操作方案（仅本次明确授权）
1. 保存 checkpoints/s2-recovery/expired-a.txt 恢复副本并核对 SHA-256；记录三文件原始哈希于 s2-before.json。
2. 用户确认无并发写入。运行 python cleanup.py --dry-run --file expired-a.txt，预览只含一项。
3. 运行 python cleanup.py --execute --file expired-a.txt --confirm-delete expired-a.txt。
4. 验证 archive/expired-a.txt 消失、expired-b.txt 与 keep.txt 内容哈希不变，保存日志。
检查点：checkpoints/s1/ 准备产物副本；checkpoints/s2-recovery/ 为授权文件恢复副本；不 commit/tag。
不可逆操作授权：用户本次明确授权 archive/expired-a.txt。expired-b.txt 与 keep.txt 明确未获授权，不执行。此前两项方案保存在 checkpoints/s1/project-design.md，仅作历史，不能据此扩大授权。

## 决策记录
| 日期 | 决策 | 来源 | 影响 |
|---|---|---|---|
| 2026-10-04 | 准备阶段直接实施；实际删除必须具体授权 | 用户明确指令 | S1 已授权，S2 等答复 |
| 2026-10-04 | 安全优先，扁平文件名、固定根目录、拒绝多硬链接 | 实现选择，按现有清单 | R-003、R-004 |
| 2026-10-04 | 方案确认；只授权实际删除 archive/expired-a.txt，不授权 expired-b.txt 与 keep.txt；无并发写入 | 用户明确答复 | S2 限定一项，验收基线保持授权分支，不扩大范围 |

## 最终结果
仅 archive/expired-a.txt 已删除，expired-b.txt 与 keep.txt 内容哈希不变。S2 独立复核通过；详细证据见 stage-report.md、s2-verification.json、s2-regression.log。检查点 checkpoints/s2/，恢复副本 checkpoints/s2-recovery/expired-a.txt。
