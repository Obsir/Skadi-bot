from skadi.utils.bot_database import DBPixivillust, Result
from skadi.utils.pixiv_utils import PixivIllust


async def add_illust(pid: int, nsfw_tag: int) -> Result.IntResult:
    illust_result = await PixivIllust(pid=pid).get_illust_data()

    if illust_result.success():
        illust_data = illust_result.result
        title = illust_data.get('title')
        uid = illust_data.get('uid')
        uname = illust_data.get('uname')
        url = illust_data.get('url')
        tags = illust_data.get('tags')
        is_r18 = illust_data.get('is_r18')

        if is_r18:
            nsfw_tag = 2

        illust = DBPixivillust(pid=pid)
        _res = await illust.add(uid=uid, title=title, uname=uname, nsfw_tag=nsfw_tag, tags=tags, url=url)
        return _res
    else:
        return Result.IntResult(error=True, info=illust_result.info, result=-1)
