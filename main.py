from pprint import pprint
from PIL import Image
import os
import io
import base64
import requests
import tempfile
from collections import Counter

_fields_ = "&fields=title,artistname,inventorynumber,uniqueid,objecttype,dimensions"
_url_ = f"https://api.collectorsystems.com/11184/objects?limit=100{_fields_}&pretty=1"
_objectsList_ = []
objCounter = Counter(numObj=0)


def getImgLink(objId):
    return f"https://api.collectorsystems.com/11184/objects/{objId}/mainimage"

def parseCollectorSystemsObjects(objList):
    for obj in objList:
        objCounter['numObj'] += 1
        csObj = {}
        # check if dimensions key exists and if object type is not a sculpture
        try:
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
        dwnld = 0
        filesize = int(response.headers['content-length'])
        for c in response.iter_content():
            dwnld += len(c)
            buffer.write(c)
            print(f'{int((dwnld/filesize)*100)}%')
        buffer.seek(0)
        i = Image.open(io.BytesIO(buffer.read()))
        savePath = os.path.join('./image', f'{objId}.png')
        i.save(savePath)
        getDominantImageColors(savePath)


def getDominantImageColors(imgPath):
    url = "https://apicloud-colortag.p.rapidapi.com/tag-file.json"
    apiKey = open('./apikey.txt', 'r').readlines()[0]
    image = getImageByteString(imgPath).decode('utf-8')
    print(image)
    payload = f'palette=simple&sort=relevance&image="{image}"'
    headers = {
        'x-rapidapi-host': "apicloud-colortag.p.rapidapi.com",
        'x-rapidapi-key': apiKey,
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8"
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code != 200:
        print(f"an error happened. status code: {response.status_code}")
    else:
        print("Successful request")
    print(response.text)


def initializeRemainingValues(targetObject, responseObj):
    targetObject['inventory_number'] = responseObj['inventorynumber']
    targetObject['object_id'] = responseObj['objectid']
    targetObject['object_type'] = responseObj['objecttype']
    targetObject['title'] = responseObj['title']
    targetObject['unique_id'] = responseObj['uniqueid']
    targetObject['artist'] = responseObj['artistname']
    targetObject['img_link'] = getImgLink(targetObject['object_id'])


def getImageByteString(imgPath):
    # with open(imgPath, 'rb') as image:
    #     return base64.b64encode(image.read()).decode('utf-8')
    with open(imgPath, "rb") as image_file:
        return base64.b64encode(image_file.read())


def beginDataImport():
    jsonResponse = requests.get(_url_).json()
    while 'next' in dict.keys(jsonResponse['paging']):
        parseCollectorSystemsObjects(jsonResponse['data'])
        jsonResponse = requests.get(jsonResponse['paging']['next']).json()
        pprint(jsonResponse)
        print(f"num objects: {objCounter['numObject']}")


if __name__ == '__main__':
    getDominantImageColors('./image/379298.png')
    # beginDataImport()
    print(objCounter)
