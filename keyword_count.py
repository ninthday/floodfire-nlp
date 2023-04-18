#!/usr/bin/env python3

import csv
import jieba
import demoji
import re
from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
from lxml.html import fromstring
from floodfire.storage.mariadb import FloodfireStorage


# 創建停用詞list
def stopwords_list(filepath: str) -> list:
    stopwords = [
        line.strip()
        for line in open(filepath, "r", encoding="utf-8").readlines()
    ]
    return stopwords


def concat_sentance(post: list) -> str:
    sentance = ""
    if post["message"] is not None:
        sentance += post["message"].strip()
    if post["description"] is not None:
        sentance += post["description"].strip()
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
    dir_path = Path(__file__).resolve().parent
    config = ConfigParser()
    config.read("{}/config.ini".format(dir_path))

    start_date = "2023-04-03"
    end_date = "2023-04-07"
    output_file = "outfile/p48_posts.csv"

    # 修改預設詞典
    jieba.set_dictionary("dict/dict.txt.big")
    # 載入自定義詞典
    jieba.load_userdict("dict/user_dict.txt")
    # 載入停用字
    stopwords = stopwords_list("dict/stop_words_zh.txt")

    storage = FloodfireStorage(config)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    proced_result = dict()

    while start_dt <= end_dt:
        print(start_dt.strftime("%Y-%m-%d"))

        posts = storage.get_crowdtangle_posts(48, start_dt.strftime("%Y-%m-%d"))

        cntr = Counter([])
        for post in posts:
            orig_sentance = concat_sentance(post)
            # 移除換行符號
            orig_sentance = orig_sentance.replace("\r", "").replace("\n", "")
            # 移除全形空白
            orig_sentance = orig_sentance.replace("　", "")
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
            cntr.update(proced_sentence)

        # proced_sentence_list.append(proced_sentence)

        # print("|".join(proced_sentence))
        proced_result[start_dt.strftime("%Y-%m-%d")] = cntr.most_common(50)
        start_dt = start_dt + timedelta(days=1)

    # print(proced_result)
    # 初始化空陣列
    rows = list()
    for i in range(50):
        rows.append(list())

    column_name = []

    for key, value in proced_result.items():
        column_name.append(key)
        column_name.append(" ")
        i = 0
        for word_cnt in value:
            rows[i].append(word_cnt[0])
            rows[i].append(word_cnt[1])
            i += 1

    with open(output_file, "w", newline="") as writefile:
        # 建立 CSV 檔寫入器
        writer = csv.writer(writefile)
        writer.writerow(column_name)
        for row in rows:
            writer.writerow(row)
    print(column_name)
    print(rows)
