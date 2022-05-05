#!/usr/bin/env python3
from collections import defaultdict
import random


FINAL_STATE = 'FINAL_STATE'
FINAL_STATE_SPACED = ' {} '.format(FINAL_STATE)


def get_corpus():
    # file generated with
    # $ awk -F'\t' '/^[0-9]+\s+admiralbulldog/ {print $3}' < bulldog_chat > only_bulldog_says
    with open("only_bulldog_says") as sbs:
        return sbs.read()


def build_words(text):
    """Return all words (sans punctuation, with FINAL_STATE)"""
    for char in '\n;,!?':
        text = text.replace(char, FINAL_STATE_SPACED)
    # there may be consecutive FINAL_STATE tokens but idc
    return text.split()


def build_transitions(words):
    transitions = defaultdict(list)
    for word, next_word in zip(words, words[1:]):
        if word != FINAL_STATE:
            transitions[word].append(next_word)
    return transitions


def generate_sentence(transitions):
    word = random.choice(list(transitions.keys()))
    while True:
        print(word, end=" ")
        word = random.choice(transitions[word])
        if word == FINAL_STATE:
            print()
            return


def main(count):
    text = get_corpus()
    words = build_words(text)
    transitions = build_transitions(words)
    for _ in range(count):
        generate_sentence(transitions)


if __name__ == '__main__':
    try:
        import sys
        count = int(sys.argv[1])
    except Exception:
        count = 10
    main(count)
