import httpx

headers = {'Authorization': 'Basic q25289577@outlook.com:869613109'}


def test_asyncHttp():
    with httpx.AsyncClient() as client:
        req = client.post()
