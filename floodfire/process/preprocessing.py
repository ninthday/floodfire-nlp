#!/usr/bin/env python3

import re
from string import punctuation

import demoji
from lxml.html import fromstring


class DataPreProcessing:
    def remove_eol(self, sentance: str) -> str:
        """
        移除換行符號

        Args:
            sentance (str): 句子

        Returns:
            str: 處理過句子
        """
        return sentance.replace("\r", "").replace("\n", "")

    def remove_fullwidth_space(self, sentance: str) -> str:
        """
        去除全形空白

        Args:
            sentance (str): 句子

        Returns:
            str: 處理過句子
        """
        return sentance.replace("　", "")

    def remove_emojii(self, sentance: str) -> str:
        """
        移除文字中的 emojii

        Args:
            sentance (str): 句子

        Returns:
            str: 移除 emojii 的句子
        """
        # 去除 emojii
        demoji_sentence = demoji.replace(sentance, "")
        return demoji_sentence

    def remove_htmltag(self, sentance: str) -> str:
        """
        移除句子中的 HTML

        Args:
            sentance (str): 句子

        Returns:
            str: 去除 HTML 的句子
        """
        # 移除 HTML tag
        notag_sentance = fromstring(sentance).text_content()
        # print(notag_sentance)
        return notag_sentance

    def remove_link(self, sentance: str) -> str:
        """
        移除句子裡的 URL 連結內容

        Args:
            sentance (str): 句子

        Returns:
            str: 去除 URL 的句子
        """
        # 移除 http, https url 連結
        nolink_sentance = re.sub(
            r"(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b",
            "",
            sentance,
        )
        # print(nolink_sentance)
        return nolink_sentance

    def remove_punctuation(self, sentance: str) -> str:
        """
        移除句子裡的半形標點符號

        Args:
            sentance (str): 輸入的句子

        Returns:
            str: 移除標點半形符號的句子
        """
        without_punctuation = sentance.translate(
            str.maketrans("", "", punctuation)
        )
        return without_punctuation
