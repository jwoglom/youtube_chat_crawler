# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import ast
import requests
import re
import sys

if len(sys.argv) == 1:
    print("Usage : YoutubeChatReplayCrawler.py {Target Youtube URL} to crawl chat replays of Target Youtube URL.");
    sys.exit(0);

target_url = sys.argv[1]
dict_str = ""
next_url = ""
comment_data = []
session = requests.Session()
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

# まず動画ページにrequestsを実行しhtmlソースを手に入れてlive_chat_replayの先頭のurlを入手
html = session.get(target_url)
soup = BeautifulSoup(html.text, "html.parser")
title = soup.find_all("title")
title = "".join(title[0].text.split("-")[:-1])
INVALID_FILENAME = "\\/:*?\"<>|"
for frag in INVALID_FILENAME:
    title = title.replace(frag,"")
RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
for iframe in soup.find_all("iframe"):
    if("live_chat_replay" in iframe["src"]):
        next_url= iframe["src"]

print(next_url)
while(1):

    try:
        html = session.get(next_url, headers=headers)
        soup = BeautifulSoup(html.text,"lxml")
        

        # 次に飛ぶurlのデータがある部分をfind_allで探してsplitで整形
        for scrp in soup.find_all("script"):
            if "window[\"ytInitialData\"]" in scrp.text:
                dict_str = ''.join(scrp.text.split(" = ")[1:])

        # javascript表記なので更に整形. falseとtrueの表記を直す
        dict_str = dict_str.replace("false","False")
        dict_str = dict_str.replace("true","True")

        # 辞書形式と認識すると簡単にデータを取得できるが, 末尾に邪魔なのがあるので消しておく（「空白2つ + \n + ;」を消す）
        dict_str = dict_str.rstrip("  \n;")
        dict_str = RE_EMOJI.sub(r'', dict_str)
        # 辞書形式に変換
        dics = ast.literal_eval(dict_str)

        # "https://www.youtube.com/live_chat_replay?continuation=" + continue_url が次のlive_chat_replayのurl
        print('dics', dics)
        print('continuations', dics["continuationContents"]["liveChatContinuation"]["continuations"])
        if "liveChatReplayContinuationData" not in dics["continuationContents"]["liveChatContinuation"]["continuations"][0]:
            break
        continue_url = dics["continuationContents"]["liveChatContinuation"]["continuations"][0]["liveChatReplayContinuationData"]["continuation"]
        print(continue_url)
        next_url = "https://www.youtube.com/live_chat_replay?continuation=" + continue_url
        # dics["continuationContents"]["liveChatContinuation"]["actions"]がコメントデータのリスト。先頭はノイズデータなので[1:]で保存
        for samp in dics["continuationContents"]["liveChatContinuation"]["actions"][1:]:
            comment_data.append(str(samp)+"\n")

    # next_urlが入手できなくなったら終わり
    except requests.ConnectionError as e:
        print("Connection Error")
        continue
    except requests.HTTPError as e:
        print("HTTPError")
        break
    except requests.Timeout as e:
        print("Timeout")
        continue
    except requests.exceptions.RequestException as e:
        print(e)
        break
    except KeyError as e:
        print("KeyError")
        print(e)
        break
    except SyntaxError as e:
        print("SyntaxError")
        print(e)
        continue
    except KeyboardInterrupt as e:
        break
    #except :
    #    print("Unexpected error:" + str(sys.exc_info()[0]))

# comment_data.txt にコメントデータを書き込む
with open(title+".json", mode='w', encoding="utf-8") as f:
    f.writelines(comment_data)
