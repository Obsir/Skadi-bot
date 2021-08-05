import re
from nonebot import on_command, export, logger
from nonebot.typing import T_State
from nonebot.adapters.cqhttp.bot import Bot
from nonebot.adapters.cqhttp.event import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE_FRIEND
from nonebot.adapters.cqhttp import MessageSegment, Message
from skadi.utils.plugin_utils import init_export, init_permission_state
from .utils import get_identify_result, pic_2_base64


# Custom plugin usage text
__plugin_name__ = '识番'
__plugin_usage__ = r'''【识番助手】
使用 trace.moe API 识别番剧
群组/私聊可用

**Permission**
Friend Private
Command & Lv.50
or AuthNode

**AuthNode**
basic

**Usage**
/识番'''

# 声明本插件可配置的权限节点
__plugin_auth_node__ = [
    'basic'
]

# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__, __plugin_auth_node__)


# 注册事件响应器
search_anime = on_command(
    '识番',
    aliases={'搜番', '番剧识别'},
    # 使用run_preprocessor拦截权限管理, 在default_state初始化所需权限
    state=init_permission_state(
        name='search_anime',
        command=True,
        level=50,
        auth_node='basic'),
    permission=GROUP | PRIVATE_FRIEND,
    priority=20,
    block=True)


# 修改默认参数处理
@search_anime.args_parser
async def parse(bot: Bot, event: MessageEvent, state: T_State):
    args = str(event.get_message()).strip().split()
    if not args:
        await search_anime.reject('你似乎没有发送有效的消息呢QAQ, 请重新发送:')
    state[state["_current_key"]] = args[0]
    if state[state["_current_key"]] == '取消':
        await search_anime.finish('操作已取消')


@search_anime.handle()
async def handle_first_receive(bot: Bot, event: MessageEvent, state: T_State):
    # 响应引用回复图片
    if event.reply:
        img_url = str(event.reply.message).strip()
        if re.match(r'^(\[CQ:image,file=[abcdef\d]{32}\.image,url=.+?])$', img_url):
            state['image_url'] = img_url

    args = str(event.get_plaintext()).strip().lower().split()
    if args:
        await search_anime.finish('该命令不支持参数QAQ')


@search_anime.got('image_url', prompt='请发送你想要识别的番剧截图:')
async def handle_draw(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
    else:
        group_id = 'Private event'

    image_url = state['image_url']
    if not re.match(r'^(\[CQ:image,file=[abcdef\d]{32}\.image,url=.+?])$', image_url):
        await search_anime.reject('你发送的似乎不是图片呢, 请重新发送, 取消命令请发送【取消】:')

    # 提取图片url
    image_url = re.sub(r'^(\[CQ:image,file=[abcdef\d]{32}\.image,url=)', '', image_url)
    image_url = re.sub(r'(])$', '', image_url)

    await search_anime.send('获取识别结果中, 请稍后~')

    res = await get_identify_result(img_url=image_url)
    if not res.success():
        logger.info(f"{group_id} / {event.user_id} search_anime failed: {res.info}")
        await search_anime.finish('发生了意外的错误QAQ, 请稍后再试')

    if not res.result:
        logger.info(f"{group_id} / {event.user_id} 使用了search_anime, 但没有找到相似的番剧")
        await search_anime.finish('没有找到与截图相似度足够高的番剧QAQ')

    for item in res.result:
        try:
            raw_at = item.get('raw_at')
            at = item.get('at')
            anilist_id = item.get('anilist_id')
            anime = item.get('anime')
            episode = item.get('episode')
            tokenthumb = item.get('tokenthumb')
            filename = item.get('filename')
            similarity = item.get('similarity')
            title_native = item.get('title_native')
            title_chinese = item.get('title_chinese')
            is_adult = item.get('is_adult')

            thumb_img_url = f'https://trace.moe/thumbnail.php?' \
                            f'anilist_id={anilist_id}&file={filename}&t={raw_at}&token={tokenthumb}'

            img_b64 = await pic_2_base64(thumb_img_url)
            if not img_b64.success():
                msg = f"识别结果: {anime}\n\n原始名称:【{title_native}】\n中文名称:【{title_chinese}】\n" \
                      f"相似度: {int(similarity)}\n\n来源文件: {filename}\nEpisode: 【{episode}】\n" \
                      f"截图时间位置: {at}\n绅士: {is_adult}"
                await search_anime.send(msg)
            else:
                img_seg = MessageSegment.image(img_b64.result)
                msg = f"识别结果: {anime}\n\n原始名称:【{title_native}】\n中文名称:【{title_chinese}】\n" \
                      f"相似度: {int(similarity)}\n\n来源文件: {filename}\nEpisode: 【{episode}】\n" \
                      f"截图时间位置: {at}\n绅士: {is_adult}\n{img_seg}"
                await search_anime.send(Message(msg))
        except Exception as e:
            logger.error(f"{group_id} / {event.user_id} 使用命令search_anime时发生了错误: {repr(e)}")
            continue
    logger.info(f"{group_id} / {event.user_id} 使用search_anime进行了一次搜索")
