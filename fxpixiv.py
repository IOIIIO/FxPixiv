import os
import sys
import threading
import dataset
import ast

from flask import Flask, render_template
from pixivpy3 import AppPixivAPI

sys.dont_write_bytecode = True

# get your refresh_token, and replac _REFRESH_TOKEN
#  https://github.com/upbit/pixivpy/issues/158#issuecomment-778919084
#_REFRESH_TOKEN = ""

app = Flask(__name__)
DB = dataset.connect('sqlite:///fxpixiv.db')
_SETTINGS = DB['settings']

_REFRESH_TOKEN = _SETTINGS.find_one(name='refresh')["value"]
DOMAIN = _SETTINGS.find_one(name='domain')["value"]
DIRECTORY = _SETTINGS.find_one(name='img_dir')["value"]
API = AppPixivAPI()
API.auth(refresh_token=_REFRESH_TOKEN)

def appapi_illust(image_id):
    aapi = API
    if DB["posts"].find_one(id=image_id) != None:
        illust = DB["posts"].find_one(id=image_id)
        illust["tags"] = ast.literal_eval(illust["tags"])
        illust["meta_single_page"] = ast.literal_eval(illust["meta_single_page"])
        url = illust["image_urls"]
        illust["image_urls"] = {}
        illust["image_urls"]["large"] = url
    else:
        json_result = aapi.illust_detail(image_id)
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

def download_image(image_id):
    directory = DIRECTORY
    aapi = API
    # get image
    illust = appapi_illust(image_id)

    if not os.path.exists(directory):
        os.makedirs(directory)

    image_url = illust["meta_single_page"].get(
        "original_image_url", illust["image_urls"]["large"]
    )
    #print("{}: {}".format(illust.title, image_url))
    if not os.path.exists("./" + directory + "/" + str(image_id) + ".jpg"):
        aapi.download(image_url, path=directory, fname="%s.jpg" % (image_id))
    return illust

def webserver(): 
    """Initialises Flask"""
    app.run(host="0.0.0.0", port=5123)

@app.route('/en/artworks/<int:post_id>')
@app.route('/artworks/<int:post_id>')
def show_post(post_id):
    print("Post ID:" + str(post_id))
    # show the post with the given id, the id is an integer
    tags = ""
    illust = download_image(post_id)
    title = illust["title"]
    url = "https://" + DOMAIN + "/"+ DIRECTORY +"/" + str(post_id) + ".jpg"

    for tag in illust["tags"]:
        if tags != "":
            tags = tags + ", "

        if tag["translated_name"] != None:
            tags = tags + tag["translated_name"]
        else:
            tags = tags + tag["name"]
        
    return render_template('meta.html', title=title, desc=tags, url=url)

if __name__ == "__main__":
    threads = [webserver]
    for x in threads:
        threading.Thread(target=x).start()