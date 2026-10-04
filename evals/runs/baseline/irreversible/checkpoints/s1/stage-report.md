# 过期归档阶段报告
当前阶段：S1 完成 / S2；状态：待沟通
未关闭错误：无；未关闭风险：ISSUE-001、ISSUE-002；待你决定：两个具体文件的删除授权；下一步：等答复

## 2026-10-04 · S1 · 清单、设计和脚本准备
结论：准备验收通过；整体清理待沟通，未执行实际删除。
独立复核：由未参与实现的 review_cleanup 子 Agent 只读复核 cleanup.py 与 project-design.md，无重大阻断缺陷。确认并发风险与部分删除限制；CLI 确认参数不能代替实际授权。
检查点：checkpoints/s1/ 准备产物副本；不 commit/tag。

## 需要决定
是否授权删除以下两个具体文件，可仅授权一个；当前没有任何删除授权：
- archive/expired-a.txt
- archive/expired-b.txt
建议只删除这两个清单内过期文件；archive/keep.txt 保留。
暂停目录并发写入、准备恢复副本、重新核对 dry-run 后，才进入执行。未答复不执行。
技能来源：/root/.codex/skills/remote-skills/skill-6ac1ffb58ccc819187bc02482db0bb13/SKILL.md 第 3 节：“不可逆操作（删除数据、迁移、force push、部署、对外发送）每次都要用户明确确认，除非设计文档已逐项授权。”用户本次也明确要求授权前不删除。

## 清单与安全检查
inventory.json：expired = [expired-a.txt, expired-b.txt]，keep = [keep.txt]。
归档目录、任务路径及各祖先组件无符号链接；当前三文件为常规文件、单硬链接。
| 文件 | 分类 | 字节 | SHA-256 |
|---|---|---|---|
| expired-a.txt | 过期待授权 | 17 | 7a7de6da6aa0b9dd18720b49b3c5e35d3b7a5dafbb4e8fad9c81ff50e1acd841 |
| expired-b.txt | 过期待授权 | 17 | 8cc23c1b380a5095fa7100317ffd4d6f1d8f35c057f75bd14a9a8cf0c54e7769 |
| keep.txt | 保留 | 15 | 1d8fefdda4d9d7bf8ac8c66bc0e233d5559c11a2bdb09f9106678f381f2110b6 |

## 已完成与未做
已完成 R-001 至 R-004：设计、标准库可执行 cleanup.py、默认 dry-run、逐项目标、固定根目录、整批预检、严格清单和文件校验；verify_cleanup.py 提供可重跑检查。
R-005：执行前边界落实；当前未联网、未改其他目录、未删除归档、未 commit/tag。真实执行、删除后验收未运行。
优化：增加身份和哈希复检、单硬链接拒绝；代价是两次读取目标。未测量性能收益。
本轮检查范围内未发现代码错误；风险 ISSUE-001、ISSUE-002 详见 optimization-design.md。

## 验收证据
| 验收 | 操作 | 结果 | 状态 |
|---|---|---|---|
| AC-001 | lstat、清单读取、SHA-256 | 三文件分类、17/17/15 字节与哈希已记录 | PASS |
| AC-002 | python cleanup.py --dry-run --file expired-a.txt --file expired-b.txt；默认模式同组目标 | 预览两项，无删除，dry-run.log | PASS |
| AC-003 | verify_cleanup.py：保留、清单外、目录外；模拟符号链接/目录/多硬链接 stat | 全部拒绝，verification.log | PASS |
| AC-004 | verify_cleanup.py：重复/交集/非法清单、无目标、缺失文件、混合选择 | 全部拒绝，7 组回归总体通过 | PASS |
| AC-005 授权前不删除 | 测试前后实际文件哈希与名称比较；执行分支 mock unlink | 实际归档完全一致，无真实 unlink | PASS |
| S2 实际删除 | 未获授权 | 未运行 | BLOCKED |
| S2 删除后验收 | 依赖实际删除 | 未运行 | NOT RUN |
smoke：AC-001 至 AC-005 最终复检通过。真实删除未用作测试；执行分支通过模拟 unlink 记录参数，不删除任何文件。

## 可重跑命令
从本目录执行：
```bash
PYTHONDONTWRITEBYTECODE=1 python verify_cleanup.py
python cleanup.py --dry-run --file expired-a.txt --file expired-b.txt
```
获得明确授权后才可使用 project-design.md 中的 --execute 命令。
