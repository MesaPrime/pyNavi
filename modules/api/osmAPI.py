import asyncio
import json
import httpx
import aiofiles
from typing import Optional, Union, Literal, List, Dict, Iterable
import xmltodict
from enum import Enum
from arrow import Arrow
from modules.server import Message


async def loadAccessToken(path: str = r'../osmAccessToken.json') -> dict:
    async with aiofiles.open(path) as file:
        osmAccessTokenData = json.loads(await file.read())
        authHeader = {'Authorization': f"{osmAccessTokenData['token_type']} {osmAccessTokenData['access_token']}"}
        return authHeader


async def version() -> str:
    """
    返回API版本
    :return: API 版本
    """
    authHeader = await loadAccessToken()
    async with httpx.AsyncClient(headers=authHeader) as client:
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
    authHeader = await loadAccessToken()
    async with httpx.AsyncClient(headers=authHeader) as client:
        req = await client.get('https://api.openstreetmap.org/api/0.6/capabilities.json')
        return req.json()


async def getMap(left, bottom, right, top):
    authHeader = await loadAccessToken()
    async with httpx.AsyncClient(headers=authHeader) as client:
        req = await client.get('https://api.openstreetmap.org/api/0.6/map.json',
                               params={'left': left, 'bottom': bottom, 'right': right, 'top': top})
        match req.status_code:
            case 200:
                return req.json()
            case 400:
                return {'error': '超出任何节点/路径/关系限制，特别是如果调用将返回超过 50000 个节点'}
            case 509:
                return {'error': '您下载的数据过多。请稍后再试'}


async def permissions():
    authHeader = await loadAccessToken()
    async with httpx.AsyncClient(headers=authHeader) as client:
        req = await client.get('https://api.openstreetmap.org/api/0.6/permissions.json')
        print(req.json())
    return req.json()


class STATUS(Enum):
    open = 1
    close = 0
    unknown = -1


class CHANGESET:

    def __init__(self, changeSetID: Optional[str] = None):
        if changeSetID:
            self.changeSetID = changeSetID
        self.status = STATUS.unknown
        self.lastActivateTime = Arrow.now()

    def __str__(self):
        return f'changeSet:{self.changeSetID}'

    async def createChangeSet(self, xml: Union[Optional[str], dict] = None) -> str:
        if xml is None:
            xml = r'<?xml version="1.0" encoding="utf-8"?>\n<osm><changeset><tag k="created_by" v="MesaPrime via api"></tag><tag k="comment" v="add data"></tag>...</changeset>...</osm>'
        elif isinstance(xml, dict):
            xml = xmltodict.unparse(xml)

        authHeader = await loadAccessToken()
        async with httpx.AsyncClient(headers=authHeader, proxy='http://127.0.0.1:7890') as client:
            req = await client.put('https://api.openstreetmap.org/api/0.6/changeset/create.json',
                                   content=xml.encode())
            changeSetID = req.text
            self.changeSetID = changeSetID
            return changeSetID

    async def closeChangeSet(self, changeSetID: Optional[str] = None) -> dict:
        authHeader = await loadAccessToken()
        if changeSetID is None:
            changeSetID = self.changeSetID

        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.put(f'https://api.openstreetmap.org/api/0.6/changeset/{changeSetID}/close')
        match req.status_code:
            case 200:
                return {'message': f'changeSet {changeSetID} has closed', 'status': 'ok'}
            case 404:
                return {'message': f'cannot find changeSet {changeSetID}', 'status': 'fail'}
            case 409:
                return {'message': req.text, 'status': 'fail'}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def downloadChangeSet(self, changeSetID: Optional[str]) -> dict:
        authHeader = await loadAccessToken()
        if changeSetID is None:
            changeSetID = self.changeSetID
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.get(f'https://api.openstreetmap.org/api/0.6/changeset/{changeSetID}/download')
        match req.status_code:
            case 200:
                data = xmltodict.unparse(req.text)
                return {'message': 'success', 'status': 'ok', 'data': data}
            case 404:
                return {'message': f'cannot find changeSet {changeSetID}', 'status': 'fail'}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def getChangeSetQuery(self, **kwargs):
        pass  # todo:complete it

    async def diffUploadChangeSet(self, changeSetID, osmFormatFile):
        pass  # todo:complete

    async def commentChangeSet(self, text: str, changeSetID: Optional[str] = None):  # todo:need test
        authHeader = await loadAccessToken()
        if changeSetID is None:
            changeSetID = self.changeSetID
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.post(f'https://api.openstreetmap.org/api/0.6//api/0.6/{changeSetID}/comment',
                                    params=text)
        match req.status_code:
            case 200:
                data = xmltodict.unparse(req.text)
                return {'message': 'success', 'status': 'ok', 'data': data}
            case 400:
                return {'message': f'cannot find changeSet {changeSetID}', 'status': 'fail'}
            case 409:
                return {'message': f'changeSet {changeSetID} closed', 'status': 'fail'}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def subscribeChangeSet(self, changeSetID: Optional[str] = None):  # todo:need test
        authHeader = await loadAccessToken()
        if changeSetID is None:
            changeSetID = self.changeSetID
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.post(f'https://api.openstreetmap.org/api/0.6/{changeSetID}/subscribe')
        match req.status_code:
            case 200:
                data = xmltodict.unparse(req.text)
                return {'message': 'success', 'status': 'ok', 'data': data}
            case 409:
                return {'message': f'changeSet {changeSetID} have been subscribed'}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def unsubscribeChangeSet(self, changeSetID: Optional[str] = None):  # todo:need test
        authHeader = await loadAccessToken()
        if changeSetID is None:
            changeSetID = self.changeSetID
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.post(f'https://api.openstreetmap.org/api/0.6/{changeSetID}/unsubscribe')
        match req.status_code:
            case 200:
                data = xmltodict.unparse(req.text)
                return {'message': 'success', 'status': 'ok', 'data': data}
            case 404:
                return {'message': f'cannot find changeSet {changeSetID}', 'status': 'fail'}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}


class ELEMENT:
    def __init__(self, elementType: Literal['node', 'way', 'relation', None] = None):
        self.data = None
        self.elementType = elementType
        self.ref = None

    def __str__(self):
        fullXml = xmltodict.unparse(self.data, pretty=True)  # todo: check if available
        xmlWithoutVersion = fullXml[39:]
        return xmlWithoutVersion

    async def upload(self, changeSet: str | CHANGESET) -> Message:
        uploadData: Dict[str:dict] = dict(self.data)
        uploadData[self.elementType].update({'@changeset': changeSet})
        nodeData = xmltodict.unparse(uploadData, root='osm')
        authHeader = await loadAccessToken()
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.put(f'https://api.openstreetmap.org/api/0.6/{self.elementType}/create',
                                   content=nodeData.encode())
        match req.status_code:
            case 200:
                # todo: check statusCode
                self.ref = req.text
                return Message.model_validate(
                    {'msg': f'create {self.elementType} success', 'code': 200, 'data': self.ref})
            case 400:
                return Message.model_validate(
                    {'msg': f'cannot create {self.elementType}', 'code': 400, 'data': req.text})
            case 409:
                return Message.model_validate(
                    {'msg': f'changeset {changeSet} has closed or this changeset is not owned by you',
                     'code': 409})
            case 412:
                return Message.model_validate(
                    {'msg': f'the {self.elementType} has element that do not exist or are nor visible',
                     'code': 412})
            case _:
                return Message.model_validate(
                    {'msg': f'unknown status code {req.status_code}: {req.text}', 'code': 404})

    async def read(self, elementID: str) -> dict:
        authHeader = await loadAccessToken()
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.get(f'https://api.openstreetmap.org/api/0.6/{self.elementType}/create/{elementID}')
            match req.status_code:
                case 200:
                    return {'message': 'read element successful', 'status': 'ok', 'data': xmltodict.parse(req.text)}
                case 404:
                    return {'message': f'cannot find element:{elementID}', 'status': 'fail'}
                case 410:
                    return {'message': f'element:{elementID} has been deleted', 'status': 'fail'}
                case _:
                    return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def update(self, elementID: str, xmlData: str) -> dict:
        authHeader = await loadAccessToken()
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.put(f'https://api.openstreetmap.org/api/0.6/{self.elementType}/{elementID}',
                                   content=xmlData.encode())
        match req.status_code:
            case 200:
                # todo: check statusCode
                self.ref = req.text
                return {'message': f'update {self.elementType} success', 'status': 'ok', 'data': req.text}
            case 400:
                return {'message': f'cannot update {self.elementType}', 'status': 'fail', 'data': req.text}
            case 409:
                return {'message': 'conflict', 'status': 'fail', 'data': req.text}
            case 404:
                return {'message': 'no element with the given id could be found', 'status': 'fail', 'data': req.text}
            case 412:
                return {'message': f'the {self.elementType} has element that do not exist or are nor visible',
                        'status': 'fail', 'data': req.text}
            case _:
                return {'message': f'unknown status code {req.status_code}: {req.text}', 'status': 'fail'}

    async def delete(self, elementID: str):
        elementData = await self.read(elementID)
        xmlData = xmltodict.unparse(elementData)
        authHeader = await loadAccessToken()
        async with httpx.AsyncClient(headers=authHeader) as client:
            req = await client.put(f'https://api.openstreetmap.org/api/0.6/{self.elementType}/{elementID}',
                                   content=xmlData.encode())


class NODE(ELEMENT):
    def __init__(self, lat: float, lon: float, tags: Optional[dict] = None, text: Optional[str] = None):
        super().__init__(elementType='node')
        self.lat = lat
        self.lon = lon
        if tags is not None:
            self.tags = [{'@k': key, '@v': value} for key, value in tags.items()]
        else:
            self.tags = [{'@k': 'created_by', '@v': 'MesaPrime via api'}]

        self.data: Dict[str, dict] = {'node': {'@lat': self.lat,
                                               '@lon': self.lon,
                                               'tag': self.tags}}


class WAY(ELEMENT):
    def __init__(self, nodes: Iterable[NODE | str] | None = None, tags: Optional[dict] = None):
        super().__init__(elementType='way')
        if tags is not None:
            self.tags = [{'@k': key, '@v': value} for key, value in tags.items()]
        else:
            self.tags = [{'@k': 'created_by', '@v': 'MesaPrime via api'}]

        self.nodesData = list()
        if isinstance(nodes, Iterable):
            for node in nodes:
                self.addNode(node)

    def addNode(self, newNode: NODE | str):
        if isinstance(newNode, NODE):
            try:
                self.nodesData.append([{'@ref': newNode.ref}])
            except AttributeError:
                pass
            pass  # todo: complete it
        elif isinstance(newNode, str):
            self.nodesData.append([{'@ref': newNode}])

    @property
    def data(self):
        return {'way': {'nd': self.nodesData,
                        'tag': self.tags}}


class Relation(ELEMENT):
    def __init__(self, ways: Iterable[WAY | str] | None = None,
                 nodes: Iterable[NODE | str] | None = None,
                 tags: Optional[dict] = None):
        super().__init__(elementType='relation')
        self.members = list()
        if tags is not None:
            self.tags = [{'@k': key, '@v': value} for key, value in tags.items()]
        else:
            self.tags = [{'@k': 'created_by', '@v': 'MesaPrime via api'}]

        if ways:
            for way in ways:
                self.addNode(way)

        if nodes:
            for node in nodes:
                self.addNode(node)

    def addNode(self, newNode: NODE | str):
        if isinstance(newNode, NODE):
            newNodeData = {f'@{key}': getattr(newNode, key)
                           for key in dir(newNode)
                           if not callable(getattr(newNode, key))}
            self.members.append(
                {'@ref': newNode.ref, '@type': 'node'}.update(newNodeData)
            )
        else:
            self.members.append({'@ref': newNode})

    def addWay(self, newWay: WAY | str):
        if isinstance(newWay, WAY):
            newNodeData = {f'@{key}': getattr(newWay, key)
                           for key in dir(newWay)
                           if not callable(getattr(newWay, key))}
            self.members.append(
                {'@ref': newWay.ref, '@type': 'way'}.update(newNodeData)
            )
        else:
            self.members.append({'@ref': newWay})

    @property
    def data(self):
        return {'relation': {
            'tag': self.tags,
            'member': self.members}
        }


class COMMITMENT:
    def __init__(self, changeSet: CHANGESET | str, element: ELEMENT):
        if isinstance(changeSet, str):
            self.changeSet = CHANGESET(changeSetID=changeSet)
        else:
            self.changeSet = changeSet

        self.data = element  # todo: fix!


if __name__ == '__main__':
    pass
