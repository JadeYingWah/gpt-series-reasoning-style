# 实时协作白板（Collab Whiteboard）

多用户实时协作白板：WebSocket 实时同步、绘制矩形/圆形/箭头/文字、撤销重做、房间分享链接。**前后端零第三方依赖**（Node 原生实现 HTTP + WebSocket）。

## 启动

```bash
node server/server.js        # 或 npm start
# 默认 http://localhost:3000，可用 PORT 环境变量改端口
```

打开浏览器访问 `http://localhost:3000`，把地址栏链接发给其他人即可进入同一房间协作。

## 功能

| 功能 | 说明 |
| --- | --- |
| 多用户实时同步 | 任何人添加/移动/删除图形，其他成员实时可见 |
| 绘制工具 | 选择（拖动/删除）、矩形、圆形、箭头、文字 |
| 撤销/重做 | Ctrl+Z / Ctrl+Y（或工具栏按钮）；只撤销自己的操作，不干扰协作者 |
| 房间分享 | 首次进入自动生成房间号写入 URL，"🔗 分享"按钮复制邀请链接 |
| 在线成员 | 侧栏实时显示成员列表，各成员有固定标识色 |
| 远端光标 | 实时显示其他成员的光标位置与昵称 |
| 绘制预览 | 其他成员正在拖拽绘制时，能看到半成品轮廓 |
| 导出 | 一键导出 PNG |

## 快捷键

- `V` 选择 / `R` 矩形 / `O` 圆形 / `A` 箭头 / `T` 文字
- `Ctrl+Z` 撤销 / `Ctrl+Y`（或 `Ctrl+Shift+Z`）重做 / `Delete` 删除选中

## 架构

```
server/
  server.js      HTTP 静态服务 + WebSocket 升级 + 房间/广播/权威状态
  websocket.js   零依赖 RFC6455 最小实现（握手/帧编解码/分片/ping-pong）
public/
  index.html     UI 骨架（工具栏 / 侧栏 / 画布 / 文字输入框）
  style.css      深色主题样式
  js/
    main.js      入口：装配 + 事件绑定 + 消息分发
    network.js   WS 客户端：连接、指数退避重连、发送
    editor.js    交互状态机：绘制/拖拽/选择/文字输入、op 提交与应用
    history.js   撤销/重做栈（undo/redo 双栈，op 互逆）
    render.js    世界坐标系渲染、letterbox 适配、远端光标层、PNG 导出
    shapes.js    图形模型：构造/命中测试/平移/Canvas 绘制
    util.js      randId / throttle / toast
test/
  smoke.js       端到端冒烟测试（多客户端连接、广播、快照、错误处理）
  unit.js        撤销重做栈与命中测试的单元验证
```

### 同步模型

- **世界坐标系**：白板固定 1600×1000 逻辑坐标，各客户端等比缩放（letterbox）适配窗口，保证不同屏幕看到的内容完全对齐。
- **op 复制**：客户端产生的操作（add/update/remove）乐观本地应用后广播；服务器将其应用到房间权威状态并转发给同房间其他人。
- **快照兜底**：新成员加入时，服务器下发权威快照（init），无需回放历史。
- **冲突策略**：以图形 id 为粒度 last-write-wins。
- **撤销语义**：只撤销本人操作（undo/redo 双栈记录互逆 op），不会回滚协作者的修改。

## 测试

```bash
npm test        # 端到端冒烟测试（12 项断言）
node test/unit.js   # 逻辑单元验证（16 项断言）
```

## 已知边界

- 房间数据存于内存，服务器重启后清空（无持久化）。
- 冲突采用 last-write-wins，不做 CRDT 合并；对白板场景足够。
- 浏览器需支持 ES Modules 与 WebSocket（现代浏览器均满足）。
