# 智能文档：新建、编辑与回读

用于普通验收文档与连接验证。以下为随包 CLI 接口基线；当前版本不支持时先查 help，或使用功能相同的当前连接器，不猜参数。

## 新建文档

```text
wecom-cli smartpage create --json '{"name":"工作协作助手连接验证（本次时间）"}'
```

create 使用 name，不接受正文或 file_path。取得实际返回的编辑链接，从中解析 docid。不能使用示例标识或发布页标识替代。编辑入口通常是 doc.weixin.qq.com/smartpage/…；page.weixin.qq.com 发布链接不能直接当编辑目标。用户只给发布链接时先取得实际可编辑目标。

## 发现页面

```text
wecom-cli smartpage pages get --json '{"docid":"实际文档标识"}'
```

从实际 pages 响应读取主页面 page_id；不能假设固定页号。该调用列出页面结构，不代表已读取正文。

## 编辑内容

先把本次验证文字写入本地 UTF-8 Markdown 文件，再调用：

```text
wecom-cli smartpage pages append --json '{"docid":"实际文档标识","page_id":"实际页面标识","content_type":"markdown","file_path":"实际绝对文件路径"}'
```

append 是独立编辑操作。连接验证只追加本次无敏感内容的验证文字，不覆盖旧文档。对已有验收文档编辑时，先回读正文、确定目标位置及变更范围；本快照仅覆盖追加，其他局部编辑需查当前正式接口或连接器能力。

## 回读正文

```text
wecom-cli smartpage pages get --json '{"docid":"实际文档标识","page_id":"实际页面标识","content_type":"markdown"}'
```

检查返回的 content_file_inner；若正文以 file_path 返回，读取该实际本地文件。必须在正文中核对预期文字与本次验证标记。字段结构变化时查看当前返回契约，不能把成功码当正文。

## 新建有内容的验收文档

已确定完整 Markdown 时可使用：

```text
wecom-cli smartpage import --json '{"name":"本次验收文档标题","file_path":"实际绝对Markdown路径"}'
```

导入后同样回读。连接验证若使用导入创建，仍需另做一次独立编辑与回读，不能仅导入就报告编辑通过。

所有示例参数都是说明，不可原样执行。实际调用用 argv 数组传 JSON，避免 Markdown 中的命令字符被 shell 执行。创建/追加超时先查状态；无可确认状态时停在待确认，不反复新增。
