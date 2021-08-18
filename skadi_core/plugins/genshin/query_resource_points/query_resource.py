from typing import Tuple, Optional, List
from ..utils import IMAGE_PATH, TXT_PATH
from PIL.Image import UnidentifiedImageError
from ..utils import image
from nonebot import logger
from .map import Map
from ..image_utils import CreateImg
import asyncio
from pathlib import Path
from asyncio.exceptions import TimeoutError
from asyncio import Semaphore
from aiohttp.client import ClientSession
from ..user_agent import get_user_agent
from ..image_utils import is_valid
import nonebot
import aiohttp
import aiofiles
import os

try:
    import ujson as json
except ModuleNotFoundError:
    import json

driver: nonebot.Driver = nonebot.get_driver()

LABEL_URL = "https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/map/label/tree?app_sn=ys_obc"
POINT_LIST_URL = "https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/map/point/list?map_id=2&app_sn=ys_obc"
MAP_URL = "https://api-static.mihoyo.com/common/map_user/ys_obc/v1/map/info?map_id=2&app_sn=ys_obc&lang=zh-cn"

icon_path = Path(IMAGE_PATH) / "genshin" / "genshin_icon"
map_path = Path(IMAGE_PATH) / "genshin" / "map"
resource_label_file = Path(TXT_PATH) / "genshin" / "resource_label_file.json"
resource_point_file = Path(TXT_PATH) / "genshin" / "resource_point_file.json"
resource_type_file = Path(TXT_PATH) / "genshin" / "resource_type_file.json"

# 地图中心坐标
CENTER_POINT: Optional[Tuple[int, int]] = None

resource_name_list: List[str] = []

MAP_RATIO = 0.5


# 查找资源
async def query_resource(resource_name: str) -> str:
    global CENTER_POINT
    planning_route: bool = False
    if resource_name and resource_name[-2:] in ["路径", "路线"]:
        resource_name = resource_name[:-2].strip()
        planning_route = True
    if not resource_name or resource_name not in resource_name_list:
        return f"未查找到 {resource_name} 资源，可通过 “原神资源列表” 获取全部资源名称.."
    map_ = Map(
        resource_name, CENTER_POINT, planning_route=planning_route, ratio=MAP_RATIO
    )
    count = map_.get_resource_count()
    rand = await asyncio.get_event_loop().run_in_executor(
        None, map_.generate_resource_icon_in_map
    )
    return (
        f"{image(f'genshin_map_{rand}.png', 'temp')}"
        f"\n\n※ {resource_name} 一共找到 {count} 个位置点\n※ 数据来源于米游社wiki"
    )


# 原神资源列表
def get_resource_type_list():
    with open(resource_type_file, "r", encoding="utf8") as f:
        data = json.load(f)
    temp = {}
    for id_ in data.keys():
        temp[data[id_]["name"]] = []
        for x in data[id_]["children"]:
            temp[data[id_]["name"]].append(x["name"])

    mes = "当前资源列表如下：\n"

    for resource_type in temp.keys():
        mes += f"{resource_type}：{'，'.join(temp[resource_type])}\n"
    return mes


@driver.on_startup
async def init(flag: bool = False):
    global CENTER_POINT, resource_name_list
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession(headers=get_user_agent()) as session:
        await download_map_init(session, semaphore, MAP_RATIO, flag)
        await download_resource_data(session, semaphore)
        await download_resource_type(session)
        if not CENTER_POINT:
            CENTER_POINT = json.load(open(resource_label_file, "r", encoding="utf8"))[
                "CENTER_POINT"
            ]
        with open(resource_type_file, "r", encoding="utf8") as f:
            data = json.load(f)
        for id_ in data:
            for x in data[id_]["children"]:
                resource_name_list.append(x["name"])


# 图标及位置资源
async def download_resource_data(session: ClientSession, semaphore: Semaphore):
    icon_path.mkdir(parents=True, exist_ok=True)
    resource_label_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with session.get(POINT_LIST_URL, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                if data["message"] == "OK":
                    data = data["data"]
                    for lst in ["label_list", "point_list"]:
                        resource_data = {"CENTER_POINT": CENTER_POINT}
                        tasks = []
                        file = (
                            resource_label_file
                            if lst == "label_list"
                            else resource_point_file
                        )
                        for x in data[lst]:
                            id_ = x["id"]
                            if lst == "label_list":
                                img_url = x["icon"]
                                tasks.append(
                                    asyncio.ensure_future(
                                        download_image(
                                            img_url,
                                            f"{icon_path}/{id_}.png",
                                            session,
                                            semaphore,
                                            True,
                                        )
                                    )
                                )
                            resource_data[id_] = x
                        await asyncio.gather(*tasks)
                        with open(file, "w", encoding="utf8") as f:
                            json.dump(resource_data, f, ensure_ascii=False, indent=4)
                else:
                    logger.warning(f'获取原神资源失败 msg: {data["message"]}')
            else:
                logger.warning(f"获取原神资源失败 code：{response.status}")
    except TimeoutError:
        logger.warning("获取原神资源数据超时...已再次尝试...")
        await download_resource_data(session, semaphore)


# 下载原神地图并拼图
async def download_map_init(
    session: ClientSession, semaphore: Semaphore, ratio: float = 1, flag: bool = False
):
    global CENTER_POINT, MAP_RATIO
    map_path.mkdir(exist_ok=True, parents=True)
    _map = map_path / "map.png"
    if _map.exists() and os.path.getsize(_map) > 1024 * 1024 * 30:
        _map.unlink()
    async with session.get(MAP_URL, timeout=5) as response:
        if response.status == 200:
            data = await response.json()
            if data["message"] == "OK":
                data = json.loads(data["data"]["info"]["detail"])
                CENTER_POINT = (data["origin"][0], data["origin"][1])
                if not _map.exists():
                    # padding_w, padding_h = data['padding']
                    data = data["slices"]
                    idx = 0
                    for x in data:
                        idj = 0
                        for j in x:
                            await download_image(
                                j["url"],
                                f"{map_path}/{idx}_{idj}.png",
                                session,
                                semaphore,
                                force_flag=flag,
                            )
                            idj += 1
                        idx += 1
                    map_width, map_height = CreateImg(
                        0, 0, background=f"{map_path}/0_0.png"
                    ).size
                    map_width = map_width * MAP_RATIO
                    map_height = map_height * MAP_RATIO
                    lens = len(
                        [x for x in os.listdir(f"{map_path}") if x.startswith("0")]
                    )
                    background_image = CreateImg(
                        map_width * lens, map_height * lens, map_width, map_height
                    )
                    for i in range(idx):
                        for j in range(idj):
                            x = CreateImg(
                                0,
                                0,
                                background=f"{map_path}/{i}_{j}.png",
                                ratio=MAP_RATIO,
                            )
                            background_image.paste(x)
                    background_image.save(f"{map_path}/map.png")
            else:
                logger.warning(f'获取原神地图失败 msg: {data["message"]}')
        else:
            logger.warning(f"获取原神地图失败 code：{response.status}")


# 下载资源类型数据
async def download_resource_type(session: ClientSession):
    resource_type_file.parent.mkdir(parents=True, exist_ok=True)
    async with session.get(LABEL_URL, timeout=5) as response:
        if response.status == 200:
            data = await response.json()
            if data["message"] == "OK":
                data = data["data"]["tree"]
                resource_data = {}
                for x in data:
                    id_ = x["id"]
                    resource_data[id_] = x
                with open(resource_type_file, "w", encoding="utf8") as f:
                    json.dump(resource_data, f, ensure_ascii=False, indent=4)
                logger.info(f"更新原神资源类型成功...")
            else:
                logger.warning(f'获取原神资源类型失败 msg: {data["message"]}')
        else:
            logger.warning(f"获取原神资源类型失败 code：{response.status}")


# 初始化资源图标
def gen_icon(icon: str):
    A = CreateImg(0, 0, background=f"{icon_path}/box.png")
    B = CreateImg(0, 0, background=f"{icon_path}/box_alpha.png")
    icon_ = icon_path / f"{icon}"
    icon_img = CreateImg(115, 115, background=icon_)
    icon_img.circle()
    B.paste(icon_img, (17, 10), True)
    B.paste(A, alpha=True)
    B.save(icon)
    logger.info(f"生成图片成功 file：{str(icon)}")


# 下载图片
async def download_image(
    img_url: str,
    path: str,
    session: ClientSession,
    semaphore: Semaphore,
    gen_flag: bool = False,
    force_flag: bool = False,
):
    async with semaphore:
        try:
            if not os.path.exists(path) or not is_valid or force_flag:
                async with session.get(img_url, timeout=5) as response:
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await response.read())
                        logger.info(f"下载原神资源图标：{img_url}")
                        if gen_flag:
                            gen_icon(path)
        except TimeoutError:
            logger.warning("下载原神资源图片超时...已再次尝试...")
            await download_image(img_url, path, session, semaphore, gen_flag)
        except UnidentifiedImageError:
            logger.warning(f"原神图片打开错误..已删除，等待下次更新... file: {path}")
            if os.path.exists(path):
                os.remove(path)


#
# def _get_point_ratio():
#
