# 企微接口路由

先读 [通用前置检查](wecom/wecom-unified.md)。本包参考是接口快照，优先当前可用企微连接器；CLI 不兼容时查询当前 help。缺少能力时明确限制，不试探性写入。

| 动作 | 读取文件（references/wecom/） |
| --- | --- |
| 新建文档、编辑文档、回读正文 | smartpage-create-edit.md |
| 智能表格操作入口 | wecomcli-smartsheet.md |
| 新建或导入智能表格 | wecomcli-smartsheet-common.md |
| 读取结构和记录 | wecomcli-smartsheet-read.md 与对应类型文件 |
| 编辑字段、记录、视图 | wecomcli-smartsheet-edit.md、field-types、record-values 或 view-types |
| 图表 | wecomcli-smartsheet-edit.md、wecomcli-smartsheet-chart-types.md、view-types |
| 851003 / no authority | wecomcli-smartsheet-webhook.md，必要时读 webhook-examples |
| 明确分工后解析联系人 | wecomcli-contact.md |
| 上传证据文件 | wecomcli-media.md 与 record-values |

表中缩写的类型文件均以 wecomcli-smartsheet- 开头、.md 结尾。不要沿快照中其他未打包技能链接执行范围外的办公操作。具体接口参数以当前工具支持为准。

不预置任何目标链接。不能把模板、历史对话或参考文件中的示例资源当成本次目标。字段、选项、页面及记录标识从实际响应获取，不能拼造。返回只保留所需业务摘要，不复制凭证或完整身份上下文。CLI 使用参数数组；当地要求 rtk 时遵守，无 rtk 的电脑不把它作为依赖。
