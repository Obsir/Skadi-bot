import re
import nonebot
from bs4 import BeautifulSoup
from nonebot import logger
from skadi_core.utils.plugin_utils import HttpFetcher, PicEncoder
from skadi_core.utils.bot_database import Result


global_config = nonebot.get_driver().config
API_KEY = global_config.saucenao_api_key
API_URL = 'https://saucenao.com/search.php'
API_URL_ASCII2D = 'https://ascii2d.net/search/url/'


HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/89.0.4389.114 Safari/537.36'}


# 图片转base64
async def pic_2_base64(url: str) -> Result.TextResult:
    fetcher = HttpFetcher(timeout=10, flag='search_image_get_image', headers=HEADERS)
    bytes_result = await fetcher.get_bytes(url=url)
    if bytes_result.error:
        return Result.TextResult(error=True, info='Image download failed', result='')

    encode_result = PicEncoder.bytes_to_b64(image=bytes_result.result)

    if encode_result.success():
        return Result.TextResult(error=False, info='Success', result=encode_result.result)
    else:
        return Result.TextResult(error=True, info=encode_result.info, result='')


# 获取识别结果 Saucenao模块
async def get_saucenao_identify_result(url: str) -> Result.ListResult:
    fetcher = HttpFetcher(timeout=10, flag='search_image_saucenao', headers=HEADERS)

    if not API_KEY:
        logger.opt(colors=True).warning(f'<r>Saucenao API KEY未配置</r>, <y>无法使用Saucenao API进行识图!</y>')
        return Result.ListResult(error=True, info='Saucenao API KEY未配置', result=[])

    __payload = {'output_type': 2,
                 'api_key': API_KEY,
                 'testmode': 1,
                 'numres': 6,
                 'db': 999,
                 'url': url}
    saucenao_result = await fetcher.get_json(url=API_URL, params=__payload, force_proxy=True)
    if saucenao_result.error:
        logger.warning(f'get_saucenao_identify_result failed, Network error: {saucenao_result.info}')
        return Result.ListResult(error=True, info=f'Network error: {saucenao_result.info}', result=[])

    __result_json = saucenao_result.result

    if __result_json['header']['status'] != 0:
        logger.error(f"get_saucenao_identify_result failed, DataSource error, "
                     f"status code: {__result_json['header']['status']}")
        return Result.ListResult(
            error=True, info=f"DataSource error, status code: {__result_json['header']['status']}", result=[])

    __result = []
    for __item in __result_json['results']:
        try:
            if int(float(__item['header']['similarity'])) < 75:
                continue
            else:
                __result.append({'similarity': __item['header']['similarity'],
                                 'thumbnail': __item['header']['thumbnail'],
                                 'index_name': __item['header']['index_name'],
                                 'ext_urls': __item['data']['ext_urls'] if __item['data'].get('ext_urls') else None})
        except Exception as res_err:
            logger.warning(f"get_saucenao_identify_result failed: {repr(res_err)}, can not resolve results")
            continue
    return Result.ListResult(error=False, info='Success', result=__result)


# 获取识别结果 ascii2d模块
async def get_ascii2d_identify_result(url: str) -> Result.ListResult:
    fetcher = HttpFetcher(timeout=10, flag='search_image_ascii2d', headers=HEADERS)

    search_url = f'{API_URL_ASCII2D}{url}'
    saucenao_redirects_result = await fetcher.get_text(url=search_url, allow_redirects=False)
    if saucenao_redirects_result.error:
        logger.error(f'get_ascii2d_identify_result failed: 获取识别结果url发生错误, 错误信息详见日志.')
        return Result.ListResult(error=True, info=f'Get identify result url failed', result=[])

    ascii2d_color_url = saucenao_redirects_result.headers.get('Location')
    if not ascii2d_color_url:
        logger.error(f'get_ascii2d_identify_result failed: 获取识别结果url发生错误, 可能被流量限制.')
        return Result.ListResult(error=True, info=f'Get identify result url failed, may be limited', result=[])
    ascii2d_bovw_url = re.sub(
        r'https://ascii2d\.net/search/color/', r'https://ascii2d.net/search/bovw/', ascii2d_color_url)

    color_res = await fetcher.get_text(url=ascii2d_color_url)
    bovw_res = await fetcher.get_text(url=ascii2d_bovw_url)

    pre_bs_list = []
    if color_res.success():
        pre_bs_list.append(color_res.result)
    if bovw_res.success():
        pre_bs_list.append(bovw_res.result)
    if not pre_bs_list:
        logger.error(f'get_ascii2d_identify_result ERROR: 获取识别结果异常, 错误信息详见日志.')
        return Result.ListResult(error=True, info=f'Get identify result data failed', result=[])

    __result = []

    for result in pre_bs_list:
        try:
            gallery_soup = BeautifulSoup(result, 'lxml')
            # 模式
            search_mode = gallery_soup.find('h5', {'class': 'p-t-1 text-xs-center'}).get_text(strip=True)
            # 每一个搜索结果
            row = gallery_soup.find_all('div', {'class': 'row item-box'})
        except Exception as page_err:
            logger.warning(f'get_ascii2d_identify_result failed: {repr(page_err)}, 解析结果页时发生错误.')
            continue
        # ascii2d搜索偏差过大,pixiv及twitter结果只取第一个
        pixiv_count = 0
        twitter_count = 0
        for row_item in row:
            # 对每个搜索结果进行解析
            try:
                detail = row_item.find('div', {'class': 'detail-box gray-link'})
                is_null = detail.get_text(strip=True)
                if not is_null:
                    continue
                # 来源部分,ascii2d网页css调整大概率导致此处解析失败,调试重点关注
                source_type = detail.find('h6').find('small').get_text(strip=True)
                if source_type == 'pixiv':
                    if pixiv_count > 0:
                        break
                    else:
                        pixiv_count += 1
                elif source_type == 'twitter':
                    if twitter_count > 0:
                        break
                    else:
                        twitter_count += 1
                else:
                    continue
                source = detail.find('h6').get_text('/', strip=True)
                source_url = detail.find('h6').find('a', {'title': None, 'style': None}).get('href')
                # 预览图部分,ascii2d网页css调整大概率导致此处解析失败,调试重点关注
                preview_img_url = row_item. \
                    find('div', {'class': 'col-xs-12 col-sm-12 col-md-4 col-xl-4 text-xs-center image-box'}). \
                    find('img').get('src')
                __result.append({'similarity': 'null',
                                 'thumbnail': f'https://ascii2d.net{preview_img_url}',
                                 'index_name': f'ascii2d - {search_mode} - {source}',
                                 'ext_urls': source_url})
            except Exception as row_err:
                logger.warning(f'get_ascii2d_identify_result ERROR: {repr(row_err)}, 解搜索结果条目时发生错误.')
                continue
    return Result.ListResult(error=False, info=f'Success', result=__result)
