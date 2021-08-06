from skadi_core.utils.plugin_utils import HttpFetcher

API_URL = 'https://lab.magiconch.com/api/nbnhhsh/guess/'


async def get_guess(guess: str) -> HttpFetcher.FetcherJsonResult:
    data = {'text': guess}

    fetcher = HttpFetcher(timeout=10, flag='nbnhhsh')
    result = await fetcher.post_json(url=API_URL, data=data)
    return result
