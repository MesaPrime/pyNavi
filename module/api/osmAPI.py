import httpx


async def version() -> str:
    """
    返回API版本
    :return: API 版本
    """
    async with httpx.AsyncClient() as client:
        req = await client.get('https://api.openstreetmap.org/api/versions.json')
        try:
            APIversion = req.json()['version']
        except KeyError:
            return 'unable to get from server'
        return APIversion


async def capabilities() -> dict:
    """
    'version': API 版本,
    'generator': 生成者,
    'copyright': 版权信息,
    'attribution': 归属,
    'license': 许可,
    'api'：
        'version':
            'minium': 最小版本,
            'maximum': 最大版本
        'area':
            'maximum': 通过API调用查询的最大面积(平方米度)
        'tracepoints':
            'per_page': 单个 GPS 轨迹中的最大点数(不一定准确)
        'waynodes':
            'maximum': 一条路径可以包含的最大节点数
        'relationmembers':
            'maximum': 关系可以包含的最大成员数
        'changesets':
            'maximum_elements': 变更集中可以包含的组合节点、方式和关系的最大数量
        'changesets':
            'default_query_limit': 变更集查询默认限制
            'maximum_query_limit'：变更集查询最大限制
        'notes':
            'default_query_limit': 边界框查询和搜索的限制参数的默认值和最大值
            'maximum_query_limit': 边界框查询和搜索的限制参数的最大值
        'status': api/gpx 字段指示客户端是否应该期望读取和写入请求工作（online）、仅读取请求工作（readonly）或没有请求工作（offline）。
            'database':
            'api':
            'gpx':
    'policy': 编辑者不得将这些资源显示为背景层
    :return:
    """
    async with httpx.AsyncClient() as client:
        req = await client.get('https://api.openstreetmap.org/api/0.6/capabilities.json')
        return req.json()


async def getMap(left, bottom, right, top):
    async with httpx.AsyncClient() as client:
        req = await client.get('https://api.openstreetmap.org/api/0.6', bbox=(left, bottom, right, top))
        match req.status_code:
            case 200:
                return req.json()
            case 400:
                return {'error': '超出任何节点/路径/关系限制，特别是如果调用将返回超过 50000 个节点'}
            case 509:
                return {'error': '您下载的数据过多。请稍后再试'}

