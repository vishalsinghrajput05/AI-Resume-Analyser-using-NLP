#!/bin/bash
mkdir -p ~/.nltk_data
python -m nltk.downloader -d ~/.nltk_data punkt averaged_perceptron_tagger maxent_ne_chunker words stopwords
