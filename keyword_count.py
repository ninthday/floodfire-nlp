#!/usr/bin/env python3

import csv
from argparse import ArgumentParser
from collections import Counter
from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path

import demoji
import jieba
from lxml.html import fromstring

from floodfire.process.preprocessing import DataPreProcessing
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

    output_file = "outfile/p{}_keywords.csv".format(project_id)

    # 修改預設詞典
    jieba.set_dictionary("dict/dict.txt.big")
    # 載入自定義詞典
    jieba.load_userdict("dict/user_dict.txt")
    # 載入停用字字典
    stopwords = stopwords_list("dict/stop_words_zh.txt")

    storage = FloodfireStorage(config)
    pre_proc = DataPreProcessing()

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    proced_result = dict()

    while start_dt <= end_dt:
        print(start_dt.strftime("%Y-%m-%d"))

        posts = storage.get_ct_singleday_posts(
            project_id, start_dt.strftime("%Y-%m-%d")
        )

        cntr = Counter([])
        for post in posts:
            orig_sentance = concat_sentance(post)
            # 移除換行符號
            orig_sentance = pre_proc.remove_eol(orig_sentance)
            # 移除全形空白
            orig_sentance = pre_proc.remove_fullwidth_space(orig_sentance)
            # 移除 emojii
            demoji_sentence = pre_proc.remove_emojii(orig_sentance)
            # 如果上述程序處理完已經變成空字串則直接跳過
            if len(demoji_sentence.strip()) == 0:
                continue
            # 移除 HTML Tag
            notag_sentance = pre_proc.remove_htmltag(demoji_sentence)
            # 移除 http, https url 連結
            nolink_sentance = pre_proc.remove_link(notag_sentance)
            # 移除標點符號
            nopun_sentance = pre_proc.remove_punctuation(nolink_sentance)
            # 如果上述程序處理完已經變成空字串則直接跳過
            if len(nopun_sentance.strip()) == 0:
                continue
            seged_words = jieba.lcut(nopun_sentance, cut_all=False, HMM=True)

            # 逐字處理程序，移除停用字、文字型數字、半形空白
            proced_sentence = proc_words_list(stopwords, seged_words)
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
