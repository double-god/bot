## 快速目标

让 AI 代理能快速在此代码库中做出有价值的更改：定位 bot 启动点、插件约定、外部集成（gocqhttp）和常见运行方式。

## 项目概览（大局）

- 主程序：`bot/bot.py`。使用 NoneBot2，注册 OneBot v11 适配器并通过 `nonebot.load_plugins("plugins")` 加载插件目录。
- 插件目录：`bot/plugins/`。每个插件是一个 Python 模块，使用 NoneBot 的 `on_command` / matcher API。
- 外部对接：`gocqhttp/config.yml` 配置了反向 WebSocket（ws-reverse）指向 `ws://bot:8080/onebot/v11/ws`，并定义了 `access-token`。这意味着 gocqhttp 预计能解析服务名 `bot`（Docker 网络或同一主机名解析）。
- 运行/容器化：`bot/Dockerfile` 将 `bot.py` 作为容器入口（CMD ["python","bot.py"]），并通过 `requirements.txt` 安装依赖。

## 关键开发工作流（可直接执行）

- 本地快速运行：
  - 在项目根或 `bot` 目录下安装依赖并运行：
    - pip install -r bot/requirements.txt
    - python bot/bot.py
- 使用 Docker（基础说明）：
  - 构建镜像：`docker build -t mybot ./bot`
  - 运行（注意网络/主机名解析）：容器需要能被 `gocqhttp` 通过主机名 `bot` 或适当的地址访问到（或把 gocqhttp 与 bot 放到同一 Docker 网络/compose 服务）。

## 项目特定约定与模式（必须遵守）

- 插件加载：始终把插件放到 `bot/plugins/`，NoneBot 会根据 `nonebot.load_plugins("plugins")` 自动加载。
- 消息处理：插件使用 `nonebot.adapters.onebot.v11` API（类型如 `Bot`, `GroupMessageEvent`, `MessageSegment`）。修改插件时，优先使用这些 adapter 类型以保证类型和行为一致。
- 全局状态：当前插件（示例 `smart_poke_plugin.py`）会在模块级保存运行任务状态（`active_poke_loops: Dict[str, asyncio.Task]`）。若修改或迁移为持久化，请注意并发与取消逻辑（`asyncio.CancelledError`）。

## 可发现的代码示例（用来做修改/测试）

- 插件命令样例（来自 `bot/plugins/smart_poke_plugin.py`）：
  - 启动命令：`循环戳` / `戳`，支持 `戳我`（目标为发言者）或 @ 指定目标或直接输入 QQ 号。次数用法如 `10次`，缺省为无限（-1）。
  - 停止命令：`停止` / `停止啦`，或文本 `别戳我啦`。
  - 发送戳操作：`MessageSegment.poke(qq=...)` 并调用 `bot.send_group_msg(group_id=..., message=...)`。
  - 错误与重试：对 `ActionFailed` 做了退避等待（20s），并对 `asyncio.CancelledError` 做了取消处理。

## 对 AI 代理的具体指令（写给 Copilot / 代码改写模型）

1. 当要增加或修改功能时，只修改 `bot/plugins/*.py` 中的插件，除非你确实需要变更框架初始化(`bot/bot.py`)或依赖。
2. 若要新增一个命令：遵循 `on_command("命令名", aliases={...}, priority=..., block=True)` 的模式，并使用 `MessageSegment` / `bot.send_group_msg` 与 `GroupMessageEvent` 类型处理群消息。
3. 不要随意删除模块级全局状态；若需要持久化，请保留取消和异常处理（见 `smart_poke_plugin.py` 中的 `asyncio.CancelledError` 与 `ActionFailed` 分支）。
4. 修改与 gocqhttp 的交互时，检查 `gocqhttp/config.yml` 中的 `access-token` 与 `ws-reverse`，并确保容器/部署环境中服务名解析一致（例如 docker-compose 中 service 名称为 `bot`）。
5. 任何修改后，可使用 `python bot/bot.py` 本地快速验证；若在容器环境测试，先在 `bot` 目录 build 镜像并确保 gocqhttp 指向正确的 WebSocket 地址。

## 质量与调试提示（与本仓库相关）

- 常见问题：若插件没有被加载，先确认 `nonebot.load_plugins("plugins")` 的相对路径是否正确以及插件文件是否有语法错误。
- 日志与错误：插件中使用 `nonebot.log.logger`；查看容器或本地控制台日志来排查 `ActionFailed` 或网络连接问题。

## 变更提交建议

- 小粒度 PR：每次修改插件或添加命令时，包含一个简单的说明（命令样例、预期行为、任何依赖变更）。

---

需要我把这份文件直接写入仓库吗？或者你希望我把更多运行/compose 示例（docker-compose）也一并添加？
