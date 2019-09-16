from PIL import Image
import os
import io
import requests
import tempfile
import json
import csv
from libs.colortagger import get_colors
from collections import Counter


_fields_ = "&fields=title,artistname,inventorynumber,uniqueid,objecttype,dimensions"
_url_ = f"https://api.collectorsystems.com/11184/objects?limit=100{_fields_}&pretty=1"
_objectsList_ = []
assetCounter = Counter({'attempted': 0, 'downloaded': 0})


def beginDataImport():
    jsonResponse = requests.get(_url_).json()
    while 'next' in dict.keys(jsonResponse['paging']):
        parseCollectorSystemsObjects(jsonResponse['data'])
        jsonResponse = requests.get(jsonResponse['paging']['next']).json()
        printAssetCounts()
    saveImports()


def parseCollectorSystemsObjects(objList):
    for obj in objList:
        assetCounter.update(attempted=1)
        try:
            csObj = {}
            # check if dimensions key exists and if object type is not a sculpture
            if 'dimensions' in dict.keys(obj) and obj['objecttype'] != 'Sculpture':
                dimensions = obj['dimensions'][0]
                csObj['width_inches'] = dimensions['widthimperial'] if 'widthimperial' in dict.keys(dimensions) else None
                csObj['height_inches'] = dimensions['heightimperial'] if 'heightimperial' in dict.keys(dimensions) else None
                initializeRemainingValues(csObj, obj)
                downloadImage(csObj['img_link'], csObj['object_id'])
                _objectsList_.append(csObj)
        except KeyError:
            pass


def printAssetCounts():
    print(f"\ndownloads attempted: {assetCounter['attempted']}")
    print(f"downloads succeeded: {assetCounter['downloaded']}\n")


def saveImports(objList=None, outPath=None):
    if objList is None: objList = _objectsList_
    if outPath is None: outPath = 'import.json'
    with open(outPath, 'w') as jsonFile:
        json.dump(objList, jsonFile)


def initializeRemainingValues(targetObject, responseObj):
    targetObject['inventory_number'] = responseObj['inventorynumber']
    targetObject['object_id'] = responseObj['objectid']
    targetObject['object_type'] = responseObj['objecttype']
    targetObject['title'] = responseObj['title']
    targetObject['unique_id'] = responseObj['uniqueid']
    targetObject['artist'] = responseObj['artistname']
    targetObject['img_link'] = getImgLink(targetObject['object_id'])


def getImgLink(objId):
    return f"https://api.collectorsystems.com/11184/objects/{objId}/mainimage"


def downloadImage(imgUrl, objId):
    buffer = tempfile.SpooledTemporaryFile(max_size=1e9)
    response = requests.get(f'{imgUrl}?size=detail', stream=True)
    if response.status_code == 200:
        downloaded = 0
        fileSize = int(response.headers['content-length'])
        for c in response.iter_content():
            downloaded += len(c)
            buffer.write(c)
            printProgress(objId, downloaded, fileSize)
        buffer.seek(0)
        i = Image.open(io.BytesIO(buffer.read()))
        savePath = os.path.join('./artwork_images', f'{objId}.png')
        i.save(savePath)
        assetCounter.update(downloaded=1)


def printProgress(objId, downloaded, filesize):
    progress = int((downloaded / filesize) * 100)
    isDone = progress == 100
    msg = f'downloading image: {objId}.png  {progress}%'
    print(f'\r{msg}', end=" \u2713\n" if isDone else "")


def updateColorTagsFromJson(jsonFile):
    print('Tagging colors from json...')
    with open(jsonFile, 'r') as file:
        artObjs = json.load(file)
    assetCounter['tagged'] = len(artObjs)
    for obj in artObjs:
        colors = list(tagColors(f"artwork_images/{obj['object_id']}.png"))
        obj['color_tags'] = {i: value for i, value in enumerate(colors)}
        assetCounter.update(tagged=-1)
        print(f"\rTagging image: {obj['object_id']}.png, {assetCounter['tagged']} images remaining", end='')
    saveImports(artObjs)
    print('\nImage color tagging from json completed.')


def tagColors(imgPath):
    return get_colors(imgPath, 3)


def makeCsvFromJsonImport(jsonFilePath, outPath=None):
    if outPath is None: outPath = 'imports.csv'
    importsDict = getJsonAsDict(jsonFilePath)
    importsData = open(outPath, 'w')
    csvWriter = csv.writer(importsData)
    assetCounter['csv_records'] = 0
    for record in importsDict:
        if assetCounter['csv_records'] == 0:
            header = record.keys()
            csvWriter.writerow(header)
            assetCounter.update(csv_records=1)
        csvWriter.writerow(record.values())


def getJsonAsDict(jsonFilePath):
    with open(jsonFilePath, 'r') as jsonFile:
        dictObj = json.load(jsonFile)
    return dictObj


def newExtract():
    newObjList = []
    importObjs = getJsonAsDict('import.json')
    artistSet = set()
    for obj in importObjs:
        newObj = {
            'artwork_id': obj['unique_id'],
            'object_id': obj['object_id'],
            'title': obj['title'],
            'artist': obj['artist'],
            'type': obj['object_type'],
            'width_inches': obj['width_inches'],
            'image_url': obj['img_link'],
            'thumbnail_url': f"{obj['img_link']}?size=detail"
        }
        newObjList.append(newObj)
        artistSet.add(newObj['artist'])
    saveImports(objList=newObjList, outPath='import2.json')


def determineWHImperial(o):
    image = getImgLink(o['object_id'])
    data = requests.get(image).content
    im = Image.open(io.BytesIO(data))
    return im.size





objList = [ {
    "width_inches": 69.0,
    "height_inches": 69.0,
    "inventory_number": "1220",
    "object_id": 379254,
    "object_type": "Painting",
    "title": "For the Mine (Tunnel)",
    "unique_id": "7285915299",
    "artist": "Hansell, Freya b. 1947",
    "img_link": "https://api.collectorsystems.com/11184/objects/379254/mainimage",
    "color_tags": {
      "0": "#1d242a",
      "1": "#686156",
      "2": "#c7bda3"
    }
  },
  {
    "width_inches": 41.75,
    "height_inches": 50.5,
    "inventory_number": "1222",
    "object_id": 379256,
    "object_type": "Painting",
    "title": "Untitled \u201cA\u201d",
    "unique_id": "6476387641",
    "artist": "Held, Al 1928-2005",
    "img_link": "https://api.collectorsystems.com/11184/objects/379256/mainimage",
    "color_tags": {
      "0": "#4d5760",
      "1": "#cec9bc",
      "2": "#1f0c06"
    }
  }]

def inchToPxScale(obj):
    widthInches = obj['width_inches']
    widthPx = widthInches * 96
    actualPxWidth = determineWHImperial(obj)[0]
    scale = widthPx / actualPxWidth
    return scale * actualPxWidth

if __name__ == '__main__':
    # newExtract()
    # beginDataImport()
    # updateColorTagsFromJson('import.json')
    # makeCsvFromJsonImport('import2.json', outPath='import2.csv')
    # o = {'object_id': 379254}
    # width = determineWHImperial(o)[0]
    # widthInches = 69.0
    for i in objList:
        correctSize = inchToPxScale(i)
        print(f'correct size: {correctSize}')
    print()

