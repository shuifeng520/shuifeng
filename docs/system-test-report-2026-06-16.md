# 药店门店智能问答 Demo 系统测试报告

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 测试对象 | 药店门店智能问答 Demo |
| 测试地址 | http://121.40.201.51:10040/ |
| 测试日期 | 2026-06-16 |
| 测试类型 | 黑盒系统测试、冒烟测试、角色权限验证、接口鉴权验证、安全基线检查、性能采样 |
| 测试方式 | 非破坏性测试；未执行新增、修改、删除、上传、知识重建、工单认领/回复等会改变业务数据的操作 |
| 测试工具 | curl、Python 3 urllib、Playwright 1.61.0 + Chromium |
| 测试环境 | Linux 6.12.58+，Cursor Cloud Agent |

## 2. 测试结论

整体结论：**核心演示流程可用，但若按生产系统验收标准，建议修复高/中风险问题后再通过上线验收。**

已验证通过：

- 登录页可访问，内置演示账号可登录。
- 员工、管理员、部门人员三类角色的主工作台均可渲染。
- 员工问答工作台、我的工单、在线考试页面可用。
- 管理后台人员、区域、部门、工单、工单分类、试卷、知识库、统计、敏感词、系统设置等菜单页面可渲染。
- 部门人员工单台可渲染。
- 匿名 API 请求被拦截，员工访问管理员 API 返回 403，基础接口鉴权有效。
- 知识检索与全局搜索接口可对中文关键词返回结果。
- Playwright 浏览器端登录与关键页面冒烟未发现前端运行时错误。

主要问题：

1. **高风险：系统通过明文 HTTP 暴露登录流程，会话 Cookie 未设置 Secure。**
2. **高风险：管理员人员列表接口返回 `passwordHash` 字段。**
3. **中风险：响应缺少常见安全响应头，且暴露 `X-Powered-By: Next.js`。**
4. **中低风险：跨角色访问非本角色页面路径时返回 200 和当前角色首页内容，状态码/路由语义不清晰。**

## 3. 测试账号

| 角色 | 账号 | 密码 | 登录结果 | 默认跳转 |
| --- | --- | --- | --- | --- |
| 药店工作人员 | 药房-张店员 | demo123 | 通过 | `/staff/chat` |
| 管理员 | 管理员 | demo123 | 通过 | `/admin/users` |
| 部门人员 | 营运-张伟 | demo123 | 通过 | `/department/tickets` |
| 无效账号 | 不存在用户 | wrong | 通过，返回 401 | 无 |

## 4. 测试范围

### 4.1 页面范围

| 模块 | 页面/路由 | 结果 |
| --- | --- | --- |
| 登录 | `/`, `/login` | 通过 |
| 员工端 | `/staff/chat` | 通过 |
| 员工端 | `/staff/tickets` | 通过 |
| 员工端 | `/staff/exams` | 通过 |
| 管理后台 | `/admin/users` | 通过 |
| 管理后台 | `/admin/regions` | 通过 |
| 管理后台 | `/admin/departments` | 通过 |
| 管理后台 | `/admin/tickets` | 通过 |
| 管理后台 | `/admin/ticket-categories` | 通过 |
| 管理后台 | `/admin/exams` | 通过 |
| 管理后台 | `/admin/knowledge` | 通过 |
| 管理后台 | `/admin/stats` | 通过 |
| 管理后台 | `/admin/sensitive-words` | 通过 |
| 管理后台 | `/admin/settings` | 通过 |
| 部门端 | `/department/tickets` | 通过 |

### 4.2 接口范围

本次从前端构建产物中识别到以下主要接口，并对只读接口做了鉴权和返回结果验证：

- `/api/auth/login`
- `/api/auth/logout`
- `/api/conversations`
- `/api/messages/*`
- `/api/tickets`
- `/api/tickets/*`
- `/api/tickets/preview`
- `/api/knowledge`
- `/api/knowledge?q=...`
- `/api/knowledge/documents/*`
- `/api/knowledge/chunks/*`
- `/api/knowledge/import-jobs`
- `/api/knowledge/index-tasks?documentId=...`
- `/api/knowledge/index-tasks/retry`
- `/api/knowledge/index-tasks/retry-all-failed`
- `/api/knowledge/rebuild-index`
- `/api/search?q=...`
- `/api/uploads`
- `/api/files/*`
- `/api/admin/users`
- `/api/admin/users/*`
- `/api/notifications/stream`

## 5. 测试用例与结果

### 5.1 登录与会话

| 编号 | 用例 | 步骤 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- | --- |
| ST-LOGIN-001 | 访问首页 | GET `/` | 可进入系统登录入口 | 返回登录页内容 | 通过 |
| ST-LOGIN-002 | 访问登录页 | GET `/login` | 展示登录表单、账号、密码、演示账号说明 | 页面包含“欢迎登录”“演示账号”“密码统一为 demo123” | 通过 |
| ST-LOGIN-003 | 员工登录 | 使用“药房-张店员 / demo123”登录 | 登录成功并进入员工问答工作台 | API 返回 `{"ok":true,"role":"staff","redirectTo":"/staff/chat"}` | 通过 |
| ST-LOGIN-004 | 管理员登录 | 使用“管理员 / demo123”登录 | 登录成功并进入管理后台 | API 返回 `{"ok":true,"role":"admin","redirectTo":"/admin/users"}` | 通过 |
| ST-LOGIN-005 | 部门人员登录 | 使用“营运-张伟 / demo123”登录 | 登录成功并进入部门工单台 | API 返回 `{"ok":true,"role":"department","redirectTo":"/department/tickets"}` | 通过 |
| ST-LOGIN-006 | 无效账号登录 | 使用不存在账号登录 | 返回认证失败，不创建会话 | 返回 401，`{"error":"用户名或密码错误"}` | 通过 |
| ST-LOGIN-007 | 会话 Cookie | 登录后检查 Cookie | 服务端设置会话 Cookie | `pharmacy_demo_session` 已设置，`HttpOnly`、`SameSite=lax`，未设置 `Secure` | 部分通过 |

### 5.2 员工端功能

| 编号 | 用例 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| ST-STAFF-001 | 员工问答工作台 | 显示问答入口、会话历史、新建会话 | 浏览器端显示“问答工作台”“会话历史”“新建会话” | 通过 |
| ST-STAFF-002 | 员工工单列表 | 显示工单概览、工单表格、状态统计 | 页面显示“全部工单 28”“进行中 1”“已结束 27” | 通过 |
| ST-STAFF-003 | 在线考试 | 显示考试列表和考试记录 | 页面显示“在线考试”“医保门诊统筹”“处方销售政策” | 通过 |
| ST-STAFF-004 | 员工查询会话接口 | GET `/api/conversations` | 返回当前员工会话列表 | 返回 200，包含多条会话记录 | 通过 |
| ST-STAFF-005 | 员工查询工单接口 | GET `/api/tickets` | 返回员工相关工单列表 | 返回 200，包含工单列表 | 通过 |

### 5.3 管理后台功能

| 编号 | 用例 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| ST-ADMIN-001 | 人员管理 | 显示人员管理页面 | 页面显示“人员管理”“新增人员”“药店工作人员/部门人员/管理员” | 通过 |
| ST-ADMIN-002 | 区域管理 | 显示区域列表 | 页面显示“新增区域”“十堰/咸宁/孝感/宜昌”等区域 | 通过 |
| ST-ADMIN-003 | 部门管理 | 显示部门列表和筛选 | 页面显示“区域”“新增部门”“人事部”等信息 | 通过 |
| ST-ADMIN-004 | 工单管理 | 显示全部工单、待认领、已结束统计 | 页面显示“全部工单 30”“待认领 1”“已结束 29” | 通过 |
| ST-ADMIN-005 | 工单分类 | 显示分类列表 | 页面显示“新增分类”“医保政策”等分类 | 通过 |
| ST-ADMIN-006 | 试卷管理 | 显示试卷列表 | 页面显示“新建试卷”“医保门诊统筹”“处方销售政策” | 通过 |
| ST-ADMIN-007 | 知识库管理 | 显示知识指标、导入入口、索引队列 | 浏览器等待后显示“知识条目数 70”“图片知识数 8”“重建索引” | 通过 |
| ST-ADMIN-008 | 统计分析 | 显示核心指标 | 页面显示“总提问数 326”“知识库命中数 154”“工单总数 30” | 通过 |
| ST-ADMIN-009 | 敏感词管理 | 显示敏感词分类和新增入口 | 页面显示“新增敏感词”“医保政策核心”等分类 | 通过 |
| ST-ADMIN-010 | 系统设置 | 显示全局参数和个人偏好 | 页面显示“全局参数”“检索与问答参数” | 通过 |
| ST-ADMIN-011 | 管理员查询人员接口 | GET `/api/admin/users` | 管理员可查询用户列表 | 返回 200，但响应包含 `passwordHash` | 不通过 |

### 5.4 部门端功能

| 编号 | 用例 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| ST-DEPT-001 | 部门工单台 | 显示部门工单列表 | 页面显示“AI 营运部工单台”“处理分发到营运部的工单” | 通过 |
| ST-DEPT-002 | 部门人员工单统计 | 显示当前部门工单统计 | 页面显示“全部工单 3”“已结束 3” | 通过 |
| ST-DEPT-003 | 部门人员访问员工/管理员路径 | 不应暴露其他角色数据 | 返回 200，但展示部门工单台内容 | 部分通过 |

### 5.5 接口鉴权与角色边界

| 编号 | 角色 | 接口 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- | --- |
| ST-AUTH-001 | 匿名 | `/api/conversations` | 拒绝访问 | 401，`{"error":"未登录"}` | 通过 |
| ST-AUTH-002 | 匿名 | `/api/tickets` | 拒绝访问 | 401，`{"error":"未登录"}` | 通过 |
| ST-AUTH-003 | 匿名 | `/api/admin/users` | 拒绝访问 | 401，`{"error":"未登录"}` | 通过 |
| ST-AUTH-004 | 员工 | `/api/admin/users` | 拒绝访问 | 403，`{"error":"无权限"}` | 通过 |
| ST-AUTH-005 | 员工 | `/api/knowledge/import-jobs` | 拒绝访问 | 403，`{"error":"仅管理员可操作"}` | 通过 |
| ST-AUTH-006 | 管理员 | `/api/admin/users` | 允许访问，但不应返回敏感字段 | 返回 200，且包含 `passwordHash` | 不通过 |
| ST-AUTH-007 | 管理员 | `/api/knowledge/import-jobs` | 允许访问 | 返回 200，包含导入任务列表 | 通过 |
| ST-AUTH-008 | 部门人员 | `/api/admin/users` | 拒绝访问 | 403，`{"error":"无权限"}` | 通过 |
| ST-AUTH-009 | 部门人员 | `/api/tickets` | 不允许发起员工工单 | 403，`{"error":"只有药店工作人员可以发起工单"}` | 通过 |

### 5.6 检索与搜索

| 编号 | 用例 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| ST-SEARCH-001 | 知识库中文查询 | GET `/api/knowledge?q=头孢` | 返回匹配知识 | 返回 200，命中“头孢类药物和酒精服用需要间隔多久？” | 通过 |
| ST-SEARCH-002 | 全局中文搜索 | GET `/api/search?q=头孢` | 返回工单、知识、会话等匹配项 | 返回 200，包含工单、知识和会话结果 | 通过 |
| ST-SEARCH-003 | 员工/管理员搜索结果隔离 | 不同角色仅返回各自可见数据 | 员工搜索结果包含会话，管理员搜索结果会话为空 | 通过 |

### 5.7 浏览器端冒烟

| 编号 | 用例 | 工具 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| ST-UI-001 | 员工浏览器登录与页面检查 | Playwright Chromium | 登录到 `/staff/chat`，`/staff/chat`、`/staff/tickets`、`/staff/exams` 文本命中，无页面错误 | 通过 |
| ST-UI-002 | 管理员浏览器登录与页面检查 | Playwright Chromium | 登录到 `/admin/users`，`/admin/users`、`/admin/knowledge`、`/admin/settings` 文本命中，无页面错误 | 通过 |
| ST-UI-003 | 部门人员浏览器登录与页面检查 | Playwright Chromium | 登录到 `/department/tickets`，部门工单台文本命中，无页面错误 | 通过 |

说明：Next.js 路由切换期间观测到少量 `_rsc` 请求被浏览器取消，以及通知长连接 `/api/notifications/stream` 在关闭页面时中止，属于页面跳转/关闭场景的正常现象，本次未归类为缺陷。

## 6. 性能采样结果

采样方式：同一登录会话内对核心 SSR 页面连续请求 5 次，统计最小/平均/最大响应时间。

| 角色 | 页面 | 状态码 | 最小(ms) | 平均(ms) | 最大(ms) | 响应体大小 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 员工 | `/staff/chat` | 5/5 为 200 | 1189 | 1488.2 | 2526 | 214480 bytes |
| 管理员 | `/admin/users` | 5/5 为 200 | 1126 | 1658.0 | 2517 | 110070 bytes |
| 部门人员 | `/department/tickets` | 5/5 为 200 | 1116 | 1960.4 | 3759 | 107307 bytes |

结论：

- 核心页面稳定返回 200，未出现请求失败。
- 当前公网环境下核心 SSR 页面平均响应约 1.5-2.0 秒，部门工单台最大值接近 3.8 秒。
- 后台敏感词页面响应体约 480 KB，内容较大，建议后续关注分页、懒加载或压缩策略。

## 7. 安全基线检查

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| HTTPS | 不通过 | 测试地址为明文 HTTP |
| 会话 Cookie `HttpOnly` | 通过 | `pharmacy_demo_session` 设置了 `HttpOnly` |
| 会话 Cookie `SameSite` | 通过 | `SameSite=lax` |
| 会话 Cookie `Secure` | 不通过 | 明文 HTTP 下未设置 `Secure` |
| 未登录 API 访问 | 通过 | 主要 API 返回 401 |
| 越权 API 访问 | 基本通过 | 员工/部门访问管理员 API 返回 403 |
| 密码哈希暴露 | 不通过 | `/api/admin/users` 返回 `passwordHash` |
| CSP | 不通过 | 响应未包含 `Content-Security-Policy` |
| X-Frame-Options | 不通过 | 响应未包含 `X-Frame-Options` |
| X-Content-Type-Options | 不通过 | 响应未包含 `X-Content-Type-Options` |
| Referrer-Policy | 不通过 | 响应未包含 `Referrer-Policy` |
| Permissions-Policy | 不通过 | 响应未包含 `Permissions-Policy` |
| Server fingerprint | 不通过 | 响应包含 `X-Powered-By: Next.js` |
| HTTP 方法约束 | 通过 | 登录接口 GET 返回 405，页面 OPTIONS 返回 400/405/307 |

## 8. 缺陷与风险清单

### BUG-001：登录与会话运行在明文 HTTP 上

- 严重级别：高
- 复现步骤：
  1. 访问 `http://121.40.201.51:10040/login`。
  2. 使用任意演示账号登录。
  3. 检查登录请求与响应头。
- 实际结果：
  - 登录请求通过 HTTP 明文传输。
  - 响应设置 `pharmacy_demo_session=...; HttpOnly; SameSite=lax`，未设置 `Secure`。
- 预期结果：
  - 生产环境必须使用 HTTPS。
  - 会话 Cookie 应设置 `Secure`，并建议配合 HSTS。
- 影响：
  - 在不可信网络中，账号密码和会话可能被窃听或劫持。
- 建议：
  - 为正式环境配置 HTTPS。
  - 设置 `Secure` Cookie。
  - 增加 `Strict-Transport-Security`。

### BUG-002：管理员用户列表接口返回密码哈希

- 严重级别：高
- 复现步骤：
  1. 使用管理员账号登录。
  2. 请求 `GET /api/admin/users`。
- 实际结果：
  - 响应用户对象包含 `passwordHash`，示例字段：`"passwordHash":"$2b$10$..."`。
- 预期结果：
  - 前端不应接收密码哈希、盐值、重置令牌等认证敏感字段。
- 影响：
  - 管理员浏览器、插件、日志或 XSS 一旦被利用，密码哈希可能泄露并被离线爆破。
- 建议：
  - API DTO 层显式剔除 `passwordHash`。
  - 增加接口测试，断言用户列表响应不包含认证敏感字段。

### BUG-003：缺少安全响应头

- 严重级别：中
- 复现步骤：
  1. 请求 `/`、`/login`、`/staff/chat`、`/admin/users`。
  2. 检查响应头。
- 实际结果：
  - 未发现 `Content-Security-Policy`、`X-Frame-Options`、`X-Content-Type-Options`、`Referrer-Policy`、`Permissions-Policy`。
  - 响应包含 `X-Powered-By: Next.js`。
- 预期结果：
  - 设置符合业务场景的安全头。
  - 关闭框架指纹暴露。
- 影响：
  - 增加 XSS、点击劫持、MIME sniffing、隐私泄露等风险。
- 建议：
  - 添加基础安全头策略：
    - `Content-Security-Policy`
    - `X-Frame-Options: DENY` 或 `SAMEORIGIN`
    - `X-Content-Type-Options: nosniff`
    - `Referrer-Policy: no-referrer` 或 `strict-origin-when-cross-origin`
    - `Permissions-Policy`
  - Next.js 配置中关闭 `poweredByHeader`。

### BUG-004：跨角色页面路径返回 200 和当前角色页面内容

- 严重级别：中低
- 复现步骤：
  1. 使用员工登录。
  2. 访问 `/admin/users`、`/admin/knowledge`。
  3. 使用部门人员登录。
  4. 访问 `/admin/users`、`/staff/chat`。
- 实际结果：
  - 响应状态码为 200。
  - 页面内容不是目标路径对应内容，而是当前角色首页/工作台内容。
- 预期结果：
  - 若不允许访问，应返回 403、401，或明确 302/307 跳转到当前角色默认页。
  - 浏览器地址栏和服务端状态码应与访问控制结果保持一致。
- 影响：
  - 不利于监控、SEO、审计和前端路由一致性判断。
  - 自动化测试或外部系统可能误判受限页面可访问。
- 建议：
  - 对跨角色页面访问使用显式 redirect 或 forbidden 页面。
  - 补充页面级访问控制测试。

### BUG-005：演示账号密码预填在登录页 HTML 中

- 严重级别：低；若为生产环境则升为高
- 复现步骤：
  1. GET `/login`。
  2. 查看 HTML 中输入框默认值。
- 实际结果：
  - 页面 HTML 包含默认账号 `药房-张店员` 和密码 `demo123`。
- 预期结果：
  - 演示环境可以展示演示账号；生产环境不得预填密码或暴露默认凭据。
- 建议：
  - 明确区分 demo 与 production 配置。
  - 生产构建禁用演示账号展示和密码预填。

## 9. 未覆盖项与限制

受非破坏性原则限制，本次未执行以下操作：

- 新增、编辑、删除人员、区域、部门、分类、试卷、敏感词、系统参数。
- 新建会话、发送问答消息、重新生成回答、停止生成。
- 发起、认领、回复、转派、关闭工单。
- 上传文件、导入知识、预览切片、重建索引、重试索引任务。
- 并发压测、长时间稳定性测试、弱网测试。
- 第三方依赖漏洞扫描、源码级安全审计、数据库一致性检查。

这些项目建议在可回滚的测试环境或具备测试数据隔离的环境中执行。

## 10. 复测建议

修复上述缺陷后，建议至少复测：

1. HTTPS、Secure Cookie、HSTS 是否生效。
2. `/api/admin/users` 是否移除 `passwordHash` 等敏感字段。
3. 安全响应头是否覆盖页面和 API。
4. 员工、管理员、部门人员的页面级和 API 级访问控制是否一致。
5. 管理后台 CRUD、知识导入、工单流转、问答生成等会改动数据的完整业务闭环。
6. 核心页面响应时间和大页面响应体大小是否优化。

