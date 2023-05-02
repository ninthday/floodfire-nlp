#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from configparser import ConfigParser
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
        sentance += " " + post["description"].strip()
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
    # nolink_sentance = re.sub(r"http[s]?://\S+", "", sentance)
    nolink_sentance = re.sub(
        r"(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b",
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
    parser.add_argument("--pid", help="Post id", dest="pid")
    args = parser.parse_args()

    project_id = args.project_id
    pid = args.pid

    dir_path = Path(__file__).resolve().parent
    config = ConfigParser()
    config.read("{}/config.ini".format(dir_path))

    storage = FloodfireStorage(config)

    posts = storage.get_ct_posts(project_id, pid)
    print(posts)

    orig_sentance = concat_sentance(posts[0])
    print("orig_sentance:\n {}".format(orig_sentance))

    # 移除換行符號
    orig_sentance = orig_sentance.replace("\r", "").replace("\n", "")
    print("remove_changeline:\n {}".format(orig_sentance))

    # 移除全形空白
    orig_sentance = orig_sentance.replace("　", "")
    print("remove_space:\n {}".format(orig_sentance))

    # 移除 emojii
    demoji_sentence = remove_emojii(orig_sentance)
    print("remove_emojii:\n {}".format(demoji_sentence))

    # 移除 HTML Tag
    notag_sentance = remove_htmltag(demoji_sentence)
    print("remove_html:\n {}".format(notag_sentance))

    # 移除 http, https url 連結
    nolink_sentance = remove_link(notag_sentance)
    print("remove_url:\n {}".format(nolink_sentance))

    # 移除標點符號
    nopun_sentance = nolink_sentance.translate(
        str.maketrans("", "", punctuation)
    )
    print("remove_punctuation:\n {}".format(nopun_sentance))

    # 修改預設詞典
    jieba.set_dictionary("dict/dict.txt.big")
    # 載入自定義詞典
    jieba.load_userdict("dict/user_dict.txt")
    # 載入停用字字典
    stopwords = stopwords_list("dict/stop_words_zh.txt")

    seged_words = jieba.lcut(nopun_sentance, cut_all=False, HMM=True)
    print("segmented_words:\n {}".format(seged_words))

    # 逐字處理程序，移除停用字、文字型數字、半形空白
    proced_sentence = proc_words_list(stopwords, seged_words)
    print("proced_sentance:\n {}".format(proced_sentence))
