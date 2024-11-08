# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 21:34:20 2021
python 3.11.2

@author: yuki
@emendator: Rusty

"""

#どこまで取得したかをjsonで保持しフォロー新着のみを取得


from pixivpy3 import *
import json
import os
import shutil
from PIL import Image
import glob
from time import sleep
import zipfile
import cv2
import numpy as np
import re
import datetime

def writeFile(filename,msg,mode) :
    f = open(filename,mode)
    f.write(msg)
    f.close()


#client.jsonの読み込み処理
f = open("/home/pi/pixiv/client.json", "r")
client_info = json.load(f)
f.close()

#pixiv_complate.jsonの読み込み処理
f = open(client_info["complate_json_path"], "r")
illust_eof = json.load(f)
f.close()

#2021/2/21ログイン方法変更
#2021/11/9　api(PixivAPI())削除
aapi = AppPixivAPI()
aapi.auth(refresh_token = client_info["refresh_token"])


debug = False

#設定
#ダウンロードする作品数
max_download_works=10000
#ブックマーク数の最小値を設定
min_bookmarks=0
#閲覧数の最小値を設定
min_view=0
#コメント数
min_comments=0
#保存先
#画像を保存するディレクトリ
main_saving_direcory_path = client_info["download_path"]

#うごイラのダウンロード形式設定
#画質悪、ファイルサイズ大、ループ、保存場所は直下
ugoira_gif  = True
#画質良、ファイルサイズ小、ループしない（再生ソフト次第）、保存場所は直下
ugoira_mp4  = True
#画質最高（劣化なし）、ファイルサイズ小、ループ、ファイル移動できない（元の画像を参照しているため）、保存場所はugoiraフォルダ内
ugoira_html = True
#画質最高（劣化なし）、ループ、ファイルサイズ大、移動可、保存場所はugoiraフォルダ内
html_onefile = True

#Filter by tag　e.g. target_tag = ["Fate/GrandOrder","FGO","FateGO","Fate/staynight"]
select_tags = [] #同じtag内に複数書くと少なくとも一つあればダウンロード
select_tags2 = []#異なるタグ間のタグはすべて含まれていないとダウンロードされない
exclude_tags = ["R-18"]#一つでもかぶっていればダウンロードしない


#新着イラストID取得
json_result = aapi.illust_follow(req_auth=True)

endid = illust_eof["endid"]
illust_ids = []
while True:
    try:
        for i in range(30):
            #print("result_id : {}".format(json_result.illusts[i].id))
            if endid >= int(json_result.illusts[i].id):
                break
            illust_ids.append(json_result.illusts[i])
            #print("{:<10}".format(json_result.illusts[i].id) + json_result.illusts[i].title)
        next_qs = aapi.parse_qs(json_result.next_url)
        sleep(1)
        json_result = aapi.json_result(**next_qs)
        sleep(1)
    except:
        #print("\nたぶん終わり\n")
        break

#古いもの順序へ変更
illust_ids.reverse()
process_illust_id = 0

#print("Download Target : {}".format(len(illust_ids)))
#ここから各イラストごとの処理
loop = len(illust_ids)
download_count = 0
compdata = []

if loop > 1:
    for x in range(loop):
        sleep(10)
        user_detail = illust_ids[x]
        user_name = user_detail.user.name
        user_id = user_detail.user.id
        total_works = user_detail.page_count
        #将来的に関数にするときのためにbreakを使わない
        if not total_works == 0:

            #フォルダパス作成
            directory_user_name = user_name
            #エスケープシーケンスを削除
            #https://pg-chain.com/python-escape
            directory_user_name = directory_user_name.translate((str.maketrans({'\n': '','\0': '','\t': '','\r': '',"\'": "'",'\"': '"', '\\':''})))
            #windowsで使えるフォルダ名に変更
            #https://www.itc.u-toyama.ac.jp/el/win7/restricted.html
            directory_user_name = directory_user_name.translate((str.maketrans({'/': '／' , ':': '：', '*': '＊', '?': '？', '"': "”", '>': '＞', '<': '＜', '|': '｜'})))
            #https://all.undo.jp/asr/1st/document/01_03.html
            #先頭ドット、末尾ドット
            directory_user_name = directory_user_name.strip(".")
            #半角スペース
            directory_user_name = directory_user_name.strip(" ")
            #全角スペース
            directory_user_name = directory_user_name.strip("　")
            saving_direcory_path = main_saving_direcory_path + directory_user_name + ("(") +str(user_id) + (")") + "/"

            #フォルダ名アップデート
            local_folders_list = glob.glob(main_saving_direcory_path + "*")
            for local_dir in local_folders_list:
                local_user_id = local_dir.rsplit("(", 1)[-1][:-1]
                local_user_name = os.path.basename(local_dir).rsplit("(", 1)[0]
                if local_user_id == str(user_id):
                    if user_name != local_user_name:
                        print(local_dir + " を次に変更 " + saving_direcory_path)
                        os.rename(local_dir, saving_direcory_path)
                        sleep(3)
                    break
            #フォルダ作成
            if not os.path.exists(saving_direcory_path):
                os.mkdir(saving_direcory_path)



            #ダウンロード開始
            #Display information of illustrator and the number of illustrations
            print("------------------------------------------------------------")
            print("start downloading " + str(total_works) + " "+ user_detail.type +" (" + str(user_detail.id)  + ") of {:<10}".format(user_id) + user_name)

            next_qs=None
            download_work_no=0
            finish_flag=False

            try:

                illust = user_detail
                process_illust_id = int(illust.id)

                #ダウンロード済みか
                #https://www.pixiv.help/hc/ja/articles/235584428-pixiv%E3%81%AB%E6%8A%95%E7%A8%BF%E3%81%A7%E3%81%8D%E3%82%8B%E7%94%BB%E5%83%8F%E3%81%AE%E7%A8%AE%E9%A1%9E%E3%82%92%E7%9F%A5%E3%82%8A%E3%81%9F%E3%81%84   
                
                title_name = illust.title
                #エスケープシーケンスを削除
                title_name = title_name.translate((str.maketrans({'\n': '','\0': '','\t': '','\r': '',"\'": "'",'\"': '"', '\\':''})))
                #windowsで使えるフォルダ名に変更
                title_name = title_name.translate((str.maketrans({'/': '／' , ':': '：', '*': '＊', '?': '？', '"': "”", '>': '＞', '<': '＜', '|': '｜'})))
                #先頭ドット、末尾ドット
                title_name = title_name.strip(".")
                #半角スペース
                title_name = title_name.strip(" ")
                #全角スペース
                title_name = title_name.strip("　")

                file_name_head = saving_direcory_path + str(illust.id)+ "_" + title_name + "_p" + str(illust.page_count-1) 
                file_name_head2 = saving_direcory_path + str(illust.id)+ "_" + title_name 

                if os.path.exists(file_name_head+".png") or os.path.exists(file_name_head+".jpg") or os.path.exists(file_name_head+".jpeg") or os.path.exists(file_name_head2+".gif") or os.path.exists(file_name_head2+".mp4") or os.path.exists(saving_direcory_path+str(illust.id)+'_ugoira'):
                    print("--------------------------------")
                    print("Title:"+title_name+" has already downloaded.")
                    continue
                
                #ダウンロード開始
                sleep(1)
                download_work_no += 1
                #print("download    :" + illust.title)
                #print("download id :" + str(illust.id))
                #print("caption")
                #print(illust.caption.replace("<br />", "\n"))

                if illust.type == "illust":
                    if illust.page_count == 1:
                        aapi.download(illust.meta_single_page.original_image_url, saving_direcory_path)

                        frames = glob.glob(f'{saving_direcory_path}/{illust.id}_p*.jpg')
                        frames += glob.glob(f'{saving_direcory_path}/{illust.id}_p*.jpeg')
                        frames += glob.glob(f'{saving_direcory_path}/{illust.id}_p*.png')
                        for frame in frames:
                            if debug:
                                print("process 1")
                                print("frame        : " + frame)
                            file_name = os.path.basename(frame)
                            if debug:
                                print("file_name    : " + file_name)
                                print("illust.id    : " + str(illust.id))
                                print("title_name : " + title_name)
                            #00000.jpgへの対策
                            file_name = file_name.replace(str(illust.id)+"_p",'{}_{}_p'.format(str(illust.id),title_name))

                            new_file = os.path.join(saving_direcory_path, file_name)
                            os.rename(frame, new_file)

                    else:
                        for page in illust.meta_pages:
                            aapi.download(page.image_urls.original, saving_direcory_path)

                        frames = glob.glob(f'{saving_direcory_path}/{illust.id}_p*.jpg')
                        frames += glob.glob(f'{saving_direcory_path}/{illust.id}_p*.jpeg')
                        frames += glob.glob(f'{saving_direcory_path}/{illust.id}_p*.png')
                        for frame in frames:
                            if debug:
                                print("process 2")
                                print("frame        : " + frame)
                            file_name = os.path.basename(frame)
                            if debug:
                                print("file_name    : " + file_name)
                                print("illust.id    : " + str(illust.id))
                                print("title_name : " + title_name)
                            #00000.jpgへの対策
                            file_name = file_name.replace(str(illust.id)+"_p",'{}_{}_p'.format(str(illust.id),title_name))

                            if debug:
                                print("save_file_name: " + file_name)

                            new_file = os.path.join(saving_direcory_path, file_name)
                            os.rename(frame, new_file)

                            sleep(1)
                    
                #うごイラ
                #ページごとdelayが違ううごイラが作れない。今は1枚目のディレイを全体に適用
                if illust.type == "ugoira":
                #イラストIDの入力待機
                    illust_id = illust.id
                    ugoira_url = illust.meta_single_page.original_image_url.rsplit('0', 1)
                    ugoira = aapi.ugoira_metadata(illust_id)
                    ugoira_frames = len(ugoira.ugoira_metadata.frames)
                    ugoira_delay = ugoira.ugoira_metadata.frames[0].delay
                    fps = 1000 / ugoira_delay
                    height = illust.height
                    width = illust.width
                    dir_name = saving_direcory_path + str(illust_id)+'_'+ title_name +'_ugoira'
                    
                    
                    #うごイラを保存するフォルダの作成
                    if not os.path.isdir(dir_name):
                        os.mkdir(dir_name)
                    
                    
                    #うごイラに使われているすべての画像のダウンロード(オリジナル) 
                    #高画質低速
                    for frame in range(ugoira_frames):
                        frame_url = ugoira_url[0] + str(frame) + ugoira_url[1]
                        aapi.download(frame_url, path=dir_name)
                        sleep(1)
                        
                    """                                               
                    #zipでダウンローのほうが速いが、低画質、動画がうまく作れない  
                    aapi.download(ugoira.ugoira_metadata.zip_urls.medium, path=dir_name)
                    print(os.path.join(dir_name, os.path.basename(ugoira.ugoira_metadata.zip_urls.medium)))
                    with zipfile.ZipFile(os.path.join(dir_name, os.path.basename(ugoira.ugoira_metadata.zip_urls.medium))) as existing_zip:
                        existing_zip.extractall(dir_name)
                    """                        
                    
                    #ファイル名が数字のみなのでリネームする  jpg以外の画像あるのかわからない
                    frames = glob.glob(f'{dir_name}/*.jpg')
                    for frame in frames:
                        file_name = os.path.basename(frame)
                        #00000.jpgへの対策
                        file_name =file_name[:-5].lstrip("0") + file_name[-5:]
                        new_file = os.path.join(dir_name, file_name)
                        os.rename(frame, new_file)

                        
                    #jpg以外の画像あるのかわからない
                    frames = glob.glob(f'{dir_name}/*.jpg')
                    frames += glob.glob(f'{dir_name}/*.jpeg')
                    frames += glob.glob(f'{dir_name}/*.png')
                    #https://note.nkmk.me/python-sort-num-str/
                    frames.sort(key=lambda s: int(re.findall(r'\d+', s)[-1]))
                    #frames.sort(key=os.path.getmtime, reverse=False)

                    #保存した画像をもとにgifを作成
                    if ugoira_gif  == True:
                        ims = []
                        for frame in frames:
                            ims.append(Image.open(frame))
                        ims[0].save(f'{saving_direcory_path}/{illust_id}_{title_name}.gif', save_all=True, append_images=ims[1:], optimize=False, duration=ugoira_delay, loop=0)
                           
                    #動画の作成　opencv全角文字問題？ 
                    #なぜか作れる動画と作れない動画があると思ったら、zipの画像が元より小さい縦横の画像があることが判明
                    if ugoira_mp4  == True:
                        # encoder(for mp4)
                        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                        # 65535 エラー対応
                        if fps*1000 > 65535:
                            fps = round(fps)
                        # output file name, encoder, fps, size(fit to image size)
                        video = cv2.VideoWriter(f'{saving_direcory_path}/{illust_id}_{title_name}.mp4',fourcc, fps, (width, height))
                        
                        for frame in frames:
                            #https://imagingsolution.net/program/python/opencv-python/read_save_image_files_in_japanese/
                            #numpyで開いてopencvに渡すことで全角文字のパスでも動く
                            buf = np.fromfile(frame, np.uint8)
                            img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
                            if img.shape[2] == 4:
                                img = np.delete(img, 3, axis=2)
                            #img = cv2.imread(frame)
                            video.write(img)
                        
                        video.release()
                        #print('written')
                        
                    #ローカルを参照するhtml
                    #https://qiita.com/choshicure/items/8795bf929e34af6622fc
                    if ugoira_html == True:

                        paths_json = json.dumps(frames)

                        html = """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Document</title>
                        </head>
                        <body>
                            <canvas id="ugoira" width="{width}" height="{height}"></canvas>
                            <script>

                                const paths = {paths_json};
                                const images = paths.map(path => {{
                                    const image = new Image();
                                    image.src = path;
                                    return image;
                                    }});

                                const canvas = document.querySelector('#ugoira');
                                const context = canvas.getContext('2d');
                                let count = 0;
                                window.addEventListener('load', function(){{
                                    setInterval(function(){{
                                        context.clearRect(0, 0, canvas.width, canvas.height);
                                        context.drawImage(images[count], 0, 0);
                                        count++;
                                        if(count>={frames}) count=0;
                                    }}, {delay});
                                }});
                            </script>
                        </body>
                        </html>
                        """.format(width=width, height=height, frames=ugoira_frames, illust_id=illust_id, delay=ugoira_delay, paths_json=paths_json)
                        with open(f'{dir_name}/ugoira.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                            
                            
                    #一つのファイルにまとめたhtml
                    if html_onefile == True:
                        import base64
                        illust_b64 = []
                        img_ext = frames[0].split('.')[-1]
                        for frame in frames:
                            with open(frame, 'rb') as f:
                                illust_b64.append(f'data:image/{img_ext};base64,{base64.b64encode(f.read()).decode()}')
                        html = """
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Document</title>
                        </head>
                        <body>
                            <canvas id="ugoira" width="{width}" height="{height}"></canvas>
                            <script>
                                const illust_b64 = {illust_b64};
                                const images = [];
                                for(let i=0; i<{frames}; i++){{
                                    const img = new Image();
                                    img.src = illust_b64[i];
                                    images.push(img);
                                }}
                                const canvas = document.querySelector('#ugoira');
                                const context = canvas.getContext('2d');
                                let count = 0;
                                window.addEventListener('load', function(){{
                                    setInterval(function(){{
                                        context.clearRect(0, 0, canvas.width, canvas.height);
                                        context.drawImage(images[count], 0, 0);
                                        count++;
                                        if(count>={frames}) count=0;
                                    }}, {delay});
                                }});
                            </script>
                        </body>
                        </html>
                        """.format(width=width, height=height, frames=ugoira_frames, illust_id=illust_id, delay=ugoira_delay, illust_b64=str(illust_b64))
                        with open(f'{dir_name}/ugoira_onefile.html', 'w', encoding='utf-8') as f:
                            f.write(html)

                    #うごイラフォルダ削除
                    if html_onefile == False and ugoira_html == False:
                      shutil.rmtree(dir_name)


                #max_download_worksに達したら2重ループをやめる
                #https://note.nkmk.me/python-break-nested-loops/
                if download_work_no >= max_download_works:
                    finish_flag=True
                    break
                
                if finish_flag == True:
                   break
               
                sleep(1)

            except:
                print("error")
                import traceback
                traceback.print_exc()

                now = datetime.datetime.now()
                dayTime = str("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}".format(now.year,now.month,now.day,now.hour,now.minute))

                #error.logの読み込み処理
                f = open(client_info["error_json_path"], "r")
                error_all_ids_old = json.load(f)
                f.close()

                errorarray = {}
                errorarray["user_id"] = user_id
                errorarray["user_name"] = user_name
                errorarray["illust_id"] = illust.id
                errorarray["title_name"] = title_name
                errorarray["dayTime"] = dayTime
                
                error_ids_old = error_all_ids_old["error-data"]
                error_ids_old.append(errorarray)

                error_ids_array = {}
                error_ids_array["count"] = len(error_ids_old)
                error_ids_array["error-data"] = error_ids_old

                with open(client_info["error_json_path"], 'w', encoding="utf-8") as f:
                    json.dump(error_ids_array, f, ensure_ascii=False, indent=4)

                sleep(30)

                break
                #continueだとuser_illustsを新たにとってこれずエラーて回るのでbreakで次のユーザーにまわしちゃう
                
            print("Download complete! to {:<10}".format(illust.id) + illust.title)

        onestr = "illust id : {:>9} / user name : {} / illust title {}".format(illust.id, user_name, illust.title)
        compdata.append(onestr)

        download_count += 1

#pixiv_complate.jsonの書き込み処理
now = datetime.datetime.now()
dayTime = str("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}".format(now.year,now.month,now.day,now.hour,now.minute))

if process_illust_id == 0:
    process_illust_id = endid
jsonStr = {}
jsonStr["endid"] = process_illust_id
jsonStr["dayTime"] = dayTime
jsonStr["download_count"] = download_count
jsonStr["download-compleate"] = compdata
with open(client_info["complate_json_path"], 'w') as f:
    json.dump(jsonStr, f, ensure_ascii=True, indent=4)
