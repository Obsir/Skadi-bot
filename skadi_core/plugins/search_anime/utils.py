import datetime
from nonebot import logger
from skadi_core.utils.plugin_utils import HttpFetcher, PicEncoder
from skadi_core.utils.bot_database import Result

API_URL = 'https://api.trace.moe/search?anilistInfo'

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/89.0.4389.114 Safari/537.36'}


# 图片转base64
async def pic_2_base64(url: str) -> Result.TextResult:
    fetcher = HttpFetcher(timeout=10, flag='search_anime_get_image', headers=HEADERS)
    bytes_result = await fetcher.get_bytes(url=url)
    if bytes_result.error:
        return Result.TextResult(error=True, info='Image download failed', result='')

    encode_result = PicEncoder.bytes_to_b64(image=bytes_result.result)

    if encode_result.success():
        return Result.TextResult(error=False, info='Success', result=encode_result.result)
    else:
        return Result.TextResult(error=True, info=encode_result.info, result='')


# 获取识别结果
async def get_identify_result(img_url: str) -> Result.ListResult:
    fetcher = HttpFetcher(timeout=10, flag='search_anime', headers=HEADERS)

    payload = {'url': img_url}
    result_json = await fetcher.get_json(url=API_URL, params=payload)
    if not result_json.success():
        return Result.ListResult(error=True, info=result_json.info, result=[])

    _res = result_json.result
    if _res.get('error'):
        return Result.ListResult(error=True, info=_res.get('error'), result=[])

    _result = []
    for anime in _res.get('result')[:5]:
        try:
            synonyms = anime["anilist"]["synonyms"]
            for x in synonyms:
                _count_ch = 0
                for word in x:
                    if "\u4e00" <= word <= "\u9fff":
                        _count_ch += 1
                if _count_ch > 3:
                    anime_name = x
                    break
            else:
                anime_name = anime["anilist"]["title"]["native"]
            from_ = int(anime["from"])
            episode = anime["episode"]
            m, s = divmod(from_, 60)
            similarity = '{:.2%}'.format(anime["similarity"])
            _result.append({
                'at': (m, s),
                'similarity': similarity,
                'episode': episode if episode else "?",
                'anime_name': anime_name,
                'is_adult': anime['anilist']['isAdult'],
                'image': anime['image'],
                'video': anime['video'],
            })
        except Exception as e:
            logger.warning(f'result parse failed: {repr(e)}, raw_json: {anime}')
            continue

    return Result.ListResult(error=False, info='Success', result=_result)
