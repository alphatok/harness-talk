# Managed Agents 架构最佳实践

> 基于 Anthropic Managed Agents 生产经验提炼的核心落地要点

---

## 一、核心设计原则

### 1.1 虚拟化三组件

| 组件 | 角色 | 生命周期 |
|------|------|----------|
| **Session** | 持久事件日志 | 超越任何 harness/sandbox |
| **Harness** | 无状态控制循环 | 可从任意点恢复 |
| **Sandbox** | 可替换执行环境 | 按需创建、失败可重建 |

**关键**：接口稳定，实现可自由演进。

### 1.2 大脑与双手解耦

| 解耦前 | 解耦后 |
|--------|--------|
| Harness 在容器内 | Harness 调用容器（如调用其他工具） |
| 容器失败 = Session 丢失 | 容器失败 = 错误传回 Claude → 可 retry |
| 凭证在沙箱内暴露 | 凭证在 vault 或绑定资源，沙箱不可达 |

---

## 二、接口设计

### 2.1 核心接口

```
Session:
  wake(sessionId)       # 重启 harness
  getSession(id)        # 获取事件日志
  emitEvent(id, event)  # 写入持久记录
  getEvents()           # 查询上下文（位置切片）

Sandbox:
  execute(name, input) → string  # 工具调用
  provision({resources})         # 标准配方创建
```

### 2.2 设计要点

- **接口对形态有立场，对实现无立场**
- `execute()` 不知道沙箱是容器、手机还是模拟器
- Harness 无状态 → 可 cattle 化
- Session 在 harness 外 → 恢复不依赖 harness 存活

---

## 三、安全边界设计

### 3.1 凭证隔离原则

**铁律**：沙箱中 Claude 生成的代码永远不能接触凭证。

| 模式 | 实现 | 适用 |
|------|------|------|
| **凭证绑定资源** | Git: 初始化时注入 token 到 remote，push/pull 无需暴露 token | 资源有天然凭证机制 |
| **Vault + Proxy** | MCP: 代理从 vault 取 token，harness 不知道凭证存在 | 自定义工具、OAuth |

### 3.2 防攻击路径

- 提示词注入 → 让 Claude 读环境变量 → 获取 token → 生成新 session
- **结构性修复**：token 从沙箱代码可达性上物理隔离

---

## 四、上下文管理

### 4.1 Session ≠ Context Window

| 问题 | Session 解决方案 |
|------|------------------|
| 上下文窗口溢出 | `getEvents()` 外部上下文对象 |
| 不可逆压缩丢失信息 | 日志追加式，可回溯任意位置 |
| 不知未来需要哪些 token | 先存后选，由 harness 决定传什么给 Claude |

### 4.2 分离关注点

- **Session**：可恢复的持久存储
- **Harness**：任意的上下文工程（压缩、裁剪、缓存命中率优化）

**原因**：无法预测未来模型需要什么上下文工程，但持久存储是永恒需求。

---

## 五、性能优化

### 5.1 TTFT 优化

| 指标 | 解耦后效果 |
|------|-----------|
| p50 TTFT | -60% |
| p95 TTFT | -90% |

### 5.2 策略

| 解耦前 | 解耦后 |
|--------|--------|
| 每大脑 = 一容器 | 容器只在需要时 `execute()` 创建 |
| 推理前必须等容器初始化 | 推理从拉取 session 事件开始，延迟加载沙箱 |

---

## 六、扩展性设计

### 6.1 多大脑

- Harness 无状态 → 可随意启动多个
- Session 共享 → 大脑可交接任务

### 6.2 多双手

- 每个双手 = 一个工具调用 `execute()`
- 支持容器、MCP server、自定义工具
- 大脑可传递双手给其他大脑

---

## 七、落地检查清单

### 架构设计

- [ ] Session/Harness/Sandbox 三组件接口分离
- [ ] Harness 无状态，可从任意 session 恢复
- [ ] Sandbox 作为工具调用，不与大脑耦合

### 安全设计

- [ ] 凭证不在沙箱环境中可达
- [ ] Git token 绑定到 remote 或使用 vault+proxy
- [ ] 提示词注入攻击路径阻断

### 性能设计

- [ ] 沙箱延迟加载（按需 `execute()`）
- [ ] Session 日志追加式、可切片查询
- [ ] Harness 可 cattle 化（失败可重建）

### 可维护性

- [ ] 模型假设变化时只需改 harness 实现
- [ ] Session 接口不随模型演进过时
- [ ] Sandbox 实现可替换（容器→手机→其他）