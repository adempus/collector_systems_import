from pprint import pprint
from PIL import Image
import os
import io
import csv
import requests
import tempfile
import json
from collections import Counter

_fields_ = "&fields=title,artistname,inventorynumber,uniqueid,objecttype,dimensions"
_url_ = f"https://api.collectorsystems.com/11184/objects?limit=100{_fields_}&pretty=1"
_objectsList_ = []
assetCounter = Counter({'attempted': 0, 'downloaded': 0})


def getImgLink(objId):
    return f"https://api.collectorsystems.com/11184/objects/{objId}/mainimage"


def parseCollectorSystemsObjects(objList):
    for obj in objList:
        assetCounter.update(attempted=1)
        csObj = {}
        try:
            # check if dimensions key exists and if object type is not a sculpture
            if 'dimensions' in dict.keys(obj) and obj['objecttype'] != 'Sculpture':
                dimensions = obj['dimensions'][0]
                csObj['width_inches'] = dimensions['widthimperial'] if 'widthimperial' in dict.keys(dimensions) else None
                csObj['height_inches'] = dimensions['heightimperial'] if 'heightimperial' in dict.keys(dimensions) else None
                initializeRemainingValues(csObj, obj)
                downloadImage(csObj['img_link'], csObj['object_id'])
        except KeyError:
            pass
        _objectsList_.append(csObj)


def downloadImage(imgUrl, objId):
    buffer = tempfile.SpooledTemporaryFile(max_size=1e9)
    response = requests.get(f'{imgUrl}?size=detail', stream=True)
    if response.status_code == 200:
        downloaded = 0
        filesize = int(response.headers['content-length'])
        for c in response.iter_content():
            downloaded += len(c)
            buffer.write(c)
            printProgress(objId, downloaded, filesize)
        print()
        buffer.seek(0)
        i = Image.open(io.BytesIO(buffer.read()))
        savePath = os.path.join('./artwork_images', f'{objId}.png')
        i.save(savePath)
        assetCounter.update(downloaded=1)


def getDominantImageColors(objId):
    url = "https://apicloud-colortag.p.rapidapi.com/tag-url.json"
    link = getImgLink(objId)
    querystring = {"palette": "simple", "sort": "weight", "url": link}
    headers = {
        'x-rapidapi-host': "apicloud-colortag.p.rapidapi.com",
        'x-rapidapi-key': "5RSRfxBxOMmshPiD70U5zHT91QNep1FDbywjsnPeF31sPOtTFg"
    }
    try:
        return requests.request("GET", url, headers=headers, params=querystring).json()['tags'][:3]
    except json.decoder.JSONDecodeError:
        return None


def initializeRemainingValues(targetObject, responseObj):
    targetObject['inventory_number'] = responseObj['inventorynumber']
    targetObject['object_id'] = responseObj['objectid']
    targetObject['object_type'] = responseObj['objecttype']
    targetObject['title'] = responseObj['title']
    targetObject['unique_id'] = responseObj['uniqueid']
    targetObject['artist'] = responseObj['artistname']
    targetObject['img_link'] = getImgLink(targetObject['object_id'])
    targetObject['color_tags'] = getDominantImageColors(targetObject['object_id'])


def beginDataImport():
    jsonResponse = requests.get(_url_).json()
    while 'next' in dict.keys(jsonResponse['paging']):
        parseCollectorSystemsObjects(jsonResponse['data'])
        jsonResponse = requests.get(jsonResponse['paging']['next']).json()
        printAssetCounts()


def printAssetCounts():
    print(f"\ndownloads attempted: {assetCounter['attempted']}")
    print(f"downloads succeeded: {assetCounter['downloaded']}\n")


def printProgress(objId, downloaded, filesize):
    progress = int((downloaded / filesize) * 100)
    isDone = progress == 100
    msg = f'downloading image: {objId}.png  {progress}%'
    print(f'\r{msg}', end=" \u2713" if isDone else "")


#TODO: fix
def saveImports():
    with open('./import.json', 'w') as jsonFile:
        json.dump(_objectsList_, jsonFile)


if __name__ == '__main__':
    beginDataImport()
    saveImports()
