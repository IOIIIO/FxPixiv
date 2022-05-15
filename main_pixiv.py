import os
import sys
import threading

from flask import Flask, render_template
from pixivpy3 import AppPixivAPI

sys.dont_write_bytecode = True

# get your refresh_token, and replace _REFRESH_TOKEN
#  https://github.com/upbit/pixivpy/issues/158#issuecomment-778919084
_REFRESH_TOKEN = "***REMOVED***"
API = None
app = Flask(__name__)

def init_api():
    global API
    api = AppPixivAPI()
    api.auth(refresh_token=_REFRESH_TOKEN)
    API = api

def appapi_illust(image_id):
    aapi = API
    json_result = aapi.illust_detail(image_id)
    print(json_result)
    illust = json_result.illust
    print(">>> {}, origin url: {}".format(illust.title, illust.image_urls["large"]))
    return illust

def download_image(image_id):
    aapi = API
    # get image
    illust = appapi_illust(image_id)

    directory = "illusts"
    if not os.path.exists(directory):
        os.makedirs(directory)

    image_url = illust.meta_single_page.get(
        "original_image_url", illust.image_urls.large
    )
    print("{}: {}".format(illust.title, image_url))
    aapi.download(image_url, path=directory, fname="%s.jpg" % (illust.id))
    return illust

def webserver(): 
    """Initialises Flask"""
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port="5123")

@app.route('/en/artworks/<int:post_id>')
@app.route('/artworks/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    tags = ""
    illust = download_image(post_id)
    title = illust["illust"]["title"]
    for tag in illust["illust"]["tags"]:
        if tags != "":
            tags = tags + ", "

        if tag["translated_name"] != None:
            tags = tags + tag["translated_name"]
        else:
            tags = tags + tag["name"]
        
    return render_template('meta.html', title=title, desc=tags, url=url)

if __name__ == "__main__":
    init_api()
    threads = [webserver]
    for x in threads:
        threading.Thread(target=x).start()