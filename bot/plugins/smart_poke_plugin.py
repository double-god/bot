import asyncio
from typing import Dict, List
from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.adapters.onebot.v11.exception import ActionFailed

# 全局变量，用于存储运行的任务
active_poke_loops: Dict[str, asyncio.Task] = {}

#核心戳一戳循环函数
async def _poke_loop(bot: Bot, group_id: str, target_user_id: str, times: int):
    count = 0
    SAFE_SWAIT_SECONDS = 18  # 戳成功一次了，等待18s
    PENALTY_WAIT_SECONDS = 20  # 触发QQ限制后，惩罚等待20s

    while (times == -1) or (count < times):
        try:
            poke_msg = MessageSegment.poke(qq=target_user_id)
            await bot.send_group_msg(group_id=group_id, message=poke_msg)

            count += 1
            logger.info(f"戳了{target_user_id}(群{group_id}◝‿◜)。{count}次/{'那咋了' if times == -1 else times}")

            await asyncio.sleep(SAFE_SWAIT_SECONDS)

        except ActionFailed as e:
            logger.warning(f"戳{target_user_id}失败力 ⸝⸝⸝ ╸▵╺⸝⸝⸝:{e}。等待{PENALTY_WAIT_SECONDS}秒后重试。")
            try:
                await asyncio.sleep(PENALTY_WAIT_SECONDS)
            except asyncio.CancelledError:
                logger.info(f"戳{target_user_id}任务冷却中被取消")
                break
        except asyncio.CancelledError:
            logger.info(f"戳{target_user_id}任务取消")
            break

        except Exception as e:
            logger.error(f"戳一戳发生未知错误力(>_<)")
    if target_user_id in active_poke_loops:
        del active_poke_loops[target_user_id]
        logger.info(f"戳{target_user_id}任务完成啦◝‿◜")

# 开始循环的指令
start_poke = on_command("循环戳", aliases={"戳"}, priority=5, block=True)

@start_poke.handle()
async def handle_start_poke(bot: Bot, event: GroupMessageEvent, message: Message = Message.from_event(event)):
    target_user_id = ""
    plain_text = ""
    full_text = event.get_plaintext().strip()

    if full_text.startswith("循环戳我") or full_text.startswith("戳我"):
        target_user_id = event.get_user_id()
        plain_text = full_text.replace("循环戳我", "").replace("戳我", "").strip()

    else:
        at_segments = message["at"]
        if at_segments:
            target_user_id = at_segments[0].data["qq"]
            text_segments = message["text"]
            plain_text = "".join(seg.data["text"] for seg in text_segments).strip()
        else:
            parts = full_text.split()
            if parts and parts[0].isdigit():
                target_user_id = parts[0]
                plain_text = "".join(parts[1:])

    if not target_user_id:
        await start_poke.finish("@你要戳的人，或输入'戳我'。\n用法:戳[@对方][xx次]")
        return

    if target_user_id == bot.self_id:
        await start_poke.finish("坏喵喵不要戳我>_<")
        return

    if target_user_id in active_poke_loops:
        await start_poke.finish(f"ta正在被我凌辱呢!先用[停止戳@ta]来结束任务吧喵")
        return

    times_str = plain_text.replace("次", "").strip()
    times = -1
    if times_str.isdigit():
        times = int(times_str)
        if times <= 0:
            await start_poke.finish("次数大于0才行")
            return

    group_id = event.group_id
    task = asyncio.create_task(_poke_loop(bot, group_id, target_user_id, times))
    active_poke_loops[target_user_id] = task

    times_display = "无限" if times == -1 else str(times)

    if target_user_id == event.get_user_id():
        await start_poke.finish(f"嘻嘻！我要开始对你进行{times_display}次骚扰啦")
    else:
        notify_msg = MessageSegment.at(event.get_user_id()) + \
                      f"好的喵"
        await bot.send_group_msg(group_id, message=notify_msg)

# 停止对循环的指令
stop_poke = on_command("停止", aliases={"停止啦"}, priority=5, block=True)

@stop_poke.handle()
async def handle_stop_poke(event: GroupMessageEvent, message: Message = Message.from_event(event)):
    target_user_id = ""
    plain_text = event.get_plaintext().strip()

    at_segments = message["at"]
    if at_segments:
        target_user_id = at_segments[0].data["qq"]

    elif plain_text == "别戳我啦":
        target_user_id = event.get_user_id()

    elif plain_text.isdigit():
        target_user_id = plain_text
        return

    if target_user_id in active_poke_loops:
        task_to_cancel = active_poke_loops[target_user_id]
        task_to_cancel.cancel()

        if target_user_id in active_poke_loops:
            del active_poke_loops[target_user_id]

        logger.info(f"戳{target_user_id}的任务被{event.get_user_id()}终止，算你还有点良心")
        await stop_poke.finish(f"停止咯")
    else:
        await stop_poke.finish("ta当前没有被戳欸。")
