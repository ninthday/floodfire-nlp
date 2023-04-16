#!/usr/bin/env python3

import csv
import jieba
import demoji
import re
from lxml.html import fromstring


# 創建停用詞list
def stopwords_list(filepath: str) -> list:
    stopwords = [
        line.strip()
        for line in open(filepath, "r", encoding="utf-8").readlines()
    ]
    return stopwords


def concat_sentance(row: list) -> str:
    sentance = ""
    for i in range(0, 2):
        if row[i] != "NULL":
            sentance += row[i].strip()
    return sentance


def remove_emojii(sentance: str) -> str:
    # 去除 emojii
    demoji_sentence = demoji.replace(sentance, "")
    return demoji_sentence


def remove_htmltag(sentance: str) -> str:
    # 移除 HTML tag
    notag_sentance = fromstring(sentance).text_content()
    # print(notag_sentance)
    return notag_sentance


def remove_link(sentance: str) -> str:
    # 移除 http, https url 連結
    nolink_sentance = re.sub(r"http[s]?://\S+", "", sentance)
    # print(nolink_sentance)
    return nolink_sentance


def remove_stopword(stopword_list: list, seged_list: list) -> list:
    proced_sentence = []
    for seged_word in seged_list:
        if seged_word not in stopword_list and seged_word != " ":
            proced_sentence.append(seged_word)
    return proced_sentence


if __name__ == "__main__":
    # my_string = """【節目快訊】週五美食單元：姚舜時間 快跟著帥哥美食達人姚舜一起吃喝玩樂吧！！ 今天當然要來聊聊《臺北、臺中、臺南& 高雄米其林指南2022》 按讚追蹤 姚舜 & 姚舜美食中央社 Facebook，掌握最新最快的美食資訊！ 📻聽重播按這裡！https://youtu.be/VzYUIPo-BiE ▶飛碟聯播網Youtube《飛碟早餐》頻道 http://bit.ly/2QVQsFh ▶網路線上收聽 http://www.uforadio.com.tw/stream/stream.html ▶ 飛碟APP，讓你收聽零距離 IOS：https://reurl.cc/3jYQMV Android：https://reurl.cc/5GpNbR ▶ 飛碟Podcast SoundOn : https://bit.ly/30Ia8Ti Apple Podcasts : https://apple.co/3jFpP6x Spotify : https://spoti.fi/2CPzneD Google 播客：https://bit.ly/3gCTb3G KKBOX：https://reurl.cc/MZR0K4"""
    data_proc_file = "data/p48_posts.csv"
    output_file = "outfile/p48_posts.csv"

    # 修改預設詞典
    jieba.set_dictionary("dict/dict.txt.big")
    # 載入自定義詞典
    jieba.load_userdict("dict/user_dict.txt")
    # 載入停用字
    stopwords = stopwords_list("dict/stop_words_zh.txt")
    # 準備寫入檔案的 list
    proced_sentence_list = list()

    # 開啟 CSV 檔案
    with open(data_proc_file, newline="") as csvfile:
        # 讀取 CSV 檔案內容
        rows = csv.reader(csvfile)

        # 以迴圈輸出每一列
        # i = 1
        for row in rows:
            # if i > 10:
            #     break
            orig_sentance = concat_sentance(row)
            # 移除 emojii
            demoji_sentence = remove_emojii(orig_sentance)
            # 如果程序處理完變成空字串則直接跳過
            if len(demoji_sentence) == 0:
                continue
            # 移除 HTML Tag
            notag_sentance = remove_htmltag(demoji_sentence)
            # 移除 http, https url 連結
            nolink_sentance = remove_link(notag_sentance)
            seged_sentence = jieba.lcut(
                nolink_sentance, cut_all=False, HMM=True
            )
            proced_sentence = remove_stopword(stopwords, seged_sentence)

            proced_sentence_list.append(proced_sentence)

            print("|".join(proced_sentence))

            # i += 1

    with open(output_file, "w", newline="") as writefile:
        # 建立 CSV 檔寫入器
        writer = csv.writer(writefile)
        for write_sentance in proced_sentence_list:
            writer.writerow([" ".join(write_sentance)])
