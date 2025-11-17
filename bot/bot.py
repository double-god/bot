import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 初始化nonebot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载插件
# 告诉NoneBot去plugins文件夹找到插件
nonebot.load_plugins("plugins")

# 运行bot
if __name__ == "__main__":
    nonebot.run()
