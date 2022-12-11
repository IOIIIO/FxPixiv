import os
import sys
import threading
import ast
import asyncio
from string import Template

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pixivpy3 import AppPixivAPI
import pause
import dataset

sys.dont_write_bytecode = True

app = FastAPI()
DB = dataset.connect('sqlite:///fxpixiv.db')
_SETTINGS = DB['settings']

_REFRESH_TOKEN = _SETTINGS.find_one(name='refresh')["value"]
DOMAIN = _SETTINGS.find_one(name='domain')["value"]
DIRECTORY = _SETTINGS.find_one(name='img_dir')["value"]

API = AppPixivAPI()

TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" / >
    <title>FxPixiv</title>
    <meta property="og:title" content="$title" />
    <meta property="og:site_name" content="FxPixiv - Fix Pixiv Embeds" />
    <meta property="og:description" content="$desc" />
    <meta property="og:image" content="$url" />
    <meta name="theme-color" content="#55bbee" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta http-equiv="refresh" content="0; url=https://pixiv.net/en/artworks/$id" />
</head>
<body>
</body>
</html>""")

FAILURE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" / >
    <title>FxPixiv</title>
    <meta property="og:title" content="Unavailable" />
    <meta property="og:site_name" content="FxPixiv - Fix Pixiv Embeds" />
    <meta property="og:description" content="This post has been deleted or is restricted." />
    <meta name="theme-color" content="#55bbee" />
    <meta http-equiv="refresh" content="0; url=https://pixiv.net/en/artworks/$id" />
</head>
<body>
</body>
</html>""")

if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

def refresh_loop():
    global API
    while True:
        API.auth(refresh_token=_REFRESH_TOKEN)
        print("Token Refreshed")
        pause.minutes(45)

def cachepurge_loop():
    while True:
        
        print("Cache Purged")
        pause.days(3)

threading.Thread(target=refresh_loop).start()

async def appapi_illust(image_id):
    loop = asyncio.get_event_loop()
    if DB["posts"].find_one(id=image_id) != None:
        illust = DB["posts"].find_one(id=image_id)
        illust["tags"] = ast.literal_eval(illust["tags"])
        illust["meta_single_page"] = ast.literal_eval(illust["meta_single_page"])
        url = illust["image_urls"]
        illust["image_urls"] = {}
        illust["image_urls"]["large"] = url
    else:
        #json_result = API.illust_detail(image_id)
        json_result = await loop.run_in_executor(None, API.illust_detail, image_id)
        if "error" in json_result or json_result == None:
            return None
        else:
            illust = json_result.illust
            data = dict(
                id=illust["id"], 
                title=illust["title"], 
                tags=str(illust["tags"]), 
                meta_single_page=str(illust["meta_single_page"]),
                image_urls = str(illust["image_urls"]["large"])
                )
            DB["posts"].upsert(data, ["id"])
    return illust

async def download_image(image_id):
    # get image
    loop = asyncio.get_event_loop()
    illust = await appapi_illust(image_id)
    if illust != None:
        if not os.path.exists("./" + DIRECTORY + "/" + str(image_id) + ".jpg"):
            image_url = illust["meta_single_page"].get(
                "original_image_url", illust["image_urls"]["large"]
            )
            #API.download(image_url, path=DIRECTORY, fname="%s.jpg" % (image_id))
            loop.run_in_executor(None, API.download, image_url, '', DIRECTORY, None, False, "%s.jpg" % (image_id))
    return illust


@app.get("/en/artworks/{post_id}", response_class=HTMLResponse)
@app.get("/artworks/{post_id}", response_class=HTMLResponse)
async def show_post(post_id: int):
    print("Post ID:" + str(post_id))
    # show the post with the given id, the id is an integer
    tags = ""
    illust = await download_image(post_id)
    if illust != None:
        title = illust["title"]
        url = "https://" + DOMAIN + "/"+ DIRECTORY +"/" + str(post_id) + ".jpg"

        for tag in illust["tags"]:
            if tags != "":
                tags = tags + ", "

            if tag["translated_name"] != None:
                tags = tags + tag["translated_name"]
            else:
                tags = tags + tag["name"]

        return TEMPLATE.substitute(
            title=title, 
            desc=tags, 
            url=url,
            id=post_id
            )
    else:
        return FAILURE.substitute(
            id=post_id
            )

@app.get("/imgs/{post_id}.jpg", response_class=HTMLResponse)
async def show_img(post_id: int):
    return FileResponse("imgs/{}.jpg".format(post_id))