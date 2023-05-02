#!/usr/bin/env python3

import csv
from argparse import ArgumentParser
from pathlib import Path

import pyLDAvis.gensim_models
from gensim.corpora import Dictionary
from gensim.models import LdaModel


def read_csv_data(file_path: str):
    data = []
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data


def save_lda_visualization(lda_model, corpus, dictionary, output_file):
    vis_data = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
    pyLDAvis.save_html(vis_data, output_file)


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
    args = parser.parse_args()

    project_id = args.project_id

    dir_path = Path(__file__).resolve().parent
    segmented_file = "outfile/p{}_segmented.csv".format(project_id)

    segmented_texts = read_csv_data(segmented_file)
    print(len(segmented_texts))
    print(segmented_texts[:5])

    # Genism 建立詞典以及語料庫
    dictionary = Dictionary(segmented_texts)
    corpus = [dictionary.doc2bow(text) for text in segmented_texts]

    # dictionary 的目的是將文字對應到一個唯一的ID
    print("字典中的單詞數量：", len(dictionary))
    print("字典中的前10個單詞：")
    for i in range(10):
        print(f"ID {i}: {dictionary[i]}")

    # corpus 是將每一篇文章對應成唯一ID
    print("語料庫中的文檔數量：", len(corpus))
    print("語料庫中的第一篇文檔：")
    print(segmented_texts[0])
    for word_id, freq in corpus[0]:
        print(f"{dictionary[word_id]} (ID: {word_id}): {freq} 次")

    # 訓練 LDA 模型
    optimal_num_topics = 15
    model = LdaModel(
        corpus,
        num_topics=optimal_num_topics,
        id2word=dictionary,
        passes=20,
        iterations=100,
        random_state=297,
    )

    topics = model.print_topics(num_words=10)
    for topic in topics:
        print(topic)

    model.save("trained-model/lda_model.model")

    save_lda_visualization(
        model, corpus, dictionary, "outfile/lda_p{}.html".format(project_id)
    )
