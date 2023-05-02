#!/usr/bin/env python3

import csv
import re
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path
from string import punctuation

import demoji
import jieba
from lxml.html import fromstring

from floodfire.storage.mariadb import FloodfireStorage


# 創建停用詞 list
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
    nolink_sentance = re.sub(
        r"(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)",
        "",
        sentance,
    )
    # print(nolink_sentance)
    return nolink_sentance


def remove_stopword(stopword_list: list, seged_list: list) -> list:
    proced_sentence = []
    for seged_word in seged_list:
        if seged_word not in stopword_list and seged_word != " ":
            proced_sentence.append(seged_word)
    return proced_sentence


def proc_words_list(stopword_list: list, seged_list: list) -> list:
    rtn_words_list = []

    for seged_word in seged_list:
        # 去除停用字
        if seged_word in stopword_list:
            continue
        # 去除空白
        if seged_word == " ":
            continue
        # 去除數字
        if seged_word.isdigit():
            continue
        rtn_words_list.append(seged_word)

    return rtn_words_list


if __name__ == "__main__":
    parser = ArgumentParser(
        description="CrowdTangle Project Posts Daily Keyword"
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Project Id",
        type=int,
        dest="project_id",
        required=True,
    )
    parser.add_argument(
        "--start-date", help="Search start date", dest="start_date"
    )
    parser.add_argument("--end-date", help="Search end date", dest="end_date")
    args = parser.parse_args()

    project_id = args.project_id
    start_date = args.start_date
    end_date = args.end_date

    dir_path = Path(__file__).resolve().parent
    config = ConfigParser()
    config.read("{}/config.ini".format(dir_path))

    # 修改預設詞典
    jieba.set_dictionary("dict/dict.txt.big")
    # 載入自定義詞典
    jieba.load_userdict("dict/user_dict.txt")
    # 載入停用字字典
    stopwords = stopwords_list("dict/stop_words_zh.txt")

    storage = FloodfireStorage(config)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    posts = storage.get_ct_period_posts(project_id, start_date, end_date)

    segmented_posts = []

    i = 1
    for post in posts:
        orig_sentance = concat_sentance(post)
        # 移除換行符號
        orig_sentance = orig_sentance.replace("\r", "").replace("\n", "")
        # 移除全形空白
        orig_sentance = orig_sentance.replace("　", "")
        # 移除 emojii
        demoji_sentence = remove_emojii(orig_sentance)
        # 如果上述程序處理完已經變成空字串則直接跳過
        if len(demoji_sentence) == 0:
            continue
        # 移除 HTML Tag
        notag_sentance = remove_htmltag(demoji_sentence)
        # 移除 http, https url 連結
        nolink_sentance = remove_link(notag_sentance)
        # 移除標點符號
        nopun_sentance = nolink_sentance.translate(
            str.maketrans("", "", punctuation)
        )
        # 如果上述程序處理完已經變成空字串則直接跳過
        if len(nopun_sentance) == 0:
            continue
        seged_words = jieba.lcut(nopun_sentance, cut_all=False, HMM=True)

        # 逐字處理程序，移除停用字、文字型數字、半形空白
        proced_sentence = proc_words_list(stopwords, seged_words)

        segmented_posts.append(proced_sentence)

        print("Segmented Post: {}".format(i))
        i += 1

    output_file = "outfile/p{}_segmented.csv".format(project_id)
    with open(output_file, "w", newline="") as writefile:
        writer = csv.writer(writefile)
        for segmented_post in segmented_posts:
            writer.writerow(segmented_post)
