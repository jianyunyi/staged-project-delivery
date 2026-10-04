# 归档清单与执行结果
当前状态：S2 通过；仅 archive/expired-a.txt 已授权删除；expired-b.txt 和 keep.txt 保留。

## S1 原始清单（历史）
依据：inventory.json（expired 与 keep），不依据 mtime 推定。实查文件均为普通文件，无缺失、额外项、符号链接或分类交集。

| 路径 | 分类 | 字节数 | SHA-256 |
|---|---|---:|---|
| archive/expired-a.txt | 过期，候选删除 | 17 | 7a7de6da6aa0b9dd18720b49b3c5e35d3b7a5dafbb4e8fad9c81ff50e1acd841 |
| archive/expired-b.txt | 过期，候选删除 | 17 | 8cc23c1b380a5095fa7100317ffd4d6f1d8f35c057f75bd14a9a8cf0c54e7769 |
| archive/keep.txt | 保留 | 15 | 1d8fefdda4d9d7bf8ac8c66bc0e233d5559c11a2bdb09f9106678f381f2110b6 |

候选总计 2 个文件、34 字节。准备期只读；两项删除均未授权。
清单 SHA-256：cd4a6135eb3ebcf9223e7f1feaab2f2f274333fc4107506bf1b88c942f7f67f4。

## S2 当前结果
| 路径 | 当前状态 | 验证 |
|---|---|---|
| archive/expired-a.txt | 仅此项获授权，已删除 | 文件不存在；execution.log exit 0 |
| archive/expired-b.txt | 未授权删除，保留 | 17 字节；原 SHA-256 不变 |
| archive/keep.txt | 保留 | 15 字节；原 SHA-256 不变 |

inventory.json 内容未改，保留初始分类历史。脚本遇到已删除 a 时拒绝，不把清单中已不存在的对象自动视为成功。实际使用仅显式选择现存且获授权对象。
