#!/bin/bash
mkdir -p ~/.nltk_data
python -m nltk.downloader -d ~/.nltk_data punkt
python -m nltk.downloader -d ~/.nltk_data averaged_perceptron_tagger
python -m nltk.downloader -d ~/.nltk_data maxent_ne_chunker
python -m nltk.downloader -d ~/.nltk_data words
python -m nltk.downloader -d ~/.nltk_data stopwords
