import datetime
from nonebot import logger
from skadi.utils.plugin_utils import HttpFetcher, PicEncoder
from skadi.utils.bot_database import Result


API_URL = 'https://api.trace.moe/search'

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
    if not _res.get('docs'):
        return Result.ListResult(error=True, info='no result found', result=[])

    _result = []
    for item in _res.get('docs'):
        try:
            if item.get('similarity') < 0.85:
                continue
            _result.append({
                'raw_at': item.get('at'),
                'at': str(datetime.timedelta(seconds=item.get('at'))),
                'anilist_id': item.get('anilist_id'),
                'anime': item.get('anime'),
                'episode': item.get('episode'),
                'tokenthumb': item.get('tokenthumb'),
                'filename': item.get('filename'),
                'similarity': item.get('similarity'),
                'title_native': item.get('title_native'),
                'title_chinese': item.get('title_chinese'),
                'is_adult': item.get('is_adult'),
            })
        except Exception as e:
            logger.warning(f'result parse failed: {repr(e)}, raw_json: {item}')
            continue

    return Result.ListResult(error=False, info='Success', result=_result)
