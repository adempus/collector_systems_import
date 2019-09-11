import requests
from pprint import pprint


_url_ = "https://api.collectorsystems.com/11184/objects?limit=2000&fields=title,artistname,inventorynumber,uniqueid,objecttype,dimensions&pretty=1"


def getImgLink(objId):
    return f"https://api.collectorsystems.com/11184/objects/{objId}/mainimage"


def getCollectorSystemsObjects():
    jsonResponse = requests.get(_url_).json()
    pprint(jsonResponse)


if __name__ == '__main__':
    getCollectorSystemsObjects()

