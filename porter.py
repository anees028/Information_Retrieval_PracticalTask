# Contains all functions related to the porter stemming algorithm.
import re
from document import Document


def get_measure(term: str) -> int:
    """
    Returns the measure m of a given term [C](VC){m}[V].
    :param term: Given term/word
    :return: Measure value m
    """
    # TODO: Implement this function. (PR03)
    m = 0
    vowel_found = False

    for i in range(len(term)):
        if is_vowel(term[i]):
            vowel_found = True
        else:
            if vowel_found:
                m += 1
                vowel_found = False

    return m


def is_vowel(letter: str) -> bool:
    """
    Check if a letter is a vowel.
    """
    return letter in 'aeiou' or (letter == 'y' and len(letter) > 1 and not is_vowel(letter[-2]))


def condition_v(stem: str) -> bool:
    """
    Returns whether condition *v* is true for a given stem (= the stem contains a vowel).
    :param stem: Word stem to check
    :return: True if the condition *v* holds
    """
    # TODO: Implement this function. (PR03)
    return any(is_vowel(char) for char in stem)


def condition_d(stem: str) -> bool:
    """
    Returns whether condition *d is true for a given stem (= the stem ends with a double consonant (e.g. -TT, -SS)).
    :param stem: Word stem to check
    :return: True if the condition *d holds
    """
    # TODO: Implement this function. (PR03)
    return len(stem) > 1 and stem[-1] == stem[-2] and not is_vowel(stem[-1])


def cond_o(stem: str) -> bool:
    """
    Returns whether condition *o is true for a given stem (= the stem ends cvc, where the second c is not W, X or Y
    (e.g. -WIL, -HOP)).
    :param stem: Word stem to check
    :return: True if the condition *o holds
    """
    # TODO: Implement this function. (PR03)
    if len(stem) < 3:
        return False
    return (
            not is_vowel(stem[-1]) and
            is_vowel(stem[-2]) and
            not is_vowel(stem[-3]) and
            stem[-1] not in 'wxy'
    )


def stem_term(term: str) -> str:
    """
    Stems a given term of the English language using the Porter stemming algorithm.
    :param term:
    :return:
    """
    # TODO: Implement this function. (PR03)
    # Note: See the provided file "porter.txt" for information on how to implement it!
    term = term.lower()
    if len(term) <= 2:
        return term

    # Step 1a
    if term.endswith('sses'):
        term = term[:-2]
    elif term.endswith('ies'):
        term = term[:-2]
    elif term.endswith('ss'):
        term = term
    elif term.endswith('s'):
        term = term[:-1]

    # Step 1b
    if term.endswith('eed'):
        if get_measure(term[:-3]) > 0:
            term = term[:-1]
    elif term.endswith('ed'):
        stem = term[:-2]
        if condition_v(stem):
            term = step1b_helper(stem)
    elif term.endswith('ing'):
        stem = term[:-3]
        if condition_v(stem):
            term = step1b_helper(stem)

    # Step 1c
    if term.endswith('y'):
        stem = term[:-1]
        if condition_v(stem):
            term = stem + 'i'

    # Step 2
    suffixes = {
        'ational': 'ate', 'tional': 'tion', 'enci': 'ence', 'anci': 'ance',
        'izer': 'ize', 'abli': 'able', 'alli': 'al', 'entli': 'ent',
        'eli': 'e', 'ousli': 'ous', 'ization': 'ize', 'ation': 'ate',
        'ator': 'ate', 'alism': 'al', 'iveness': 'ive', 'fulness': 'ful',
        'ousness': 'ous', 'aliti': 'al', 'iviti': 'ive', 'biliti': 'ble',
    }
    for suffix, replacement in sorted(suffixes.items(), key=lambda x: -len(x[0])):
        if term.endswith(suffix):
            stem = term[:-len(suffix)]
            if get_measure(stem) > 0:
                term = stem + replacement
                break

    # Step 3
    suffixes = {
        'icate': 'ic', 'ative': '', 'alize': 'al', 'iciti': 'ic',
        'ical': 'ic', 'ful': '', 'ness': ''
    }
    for suffix, replacement in sorted(suffixes.items(), key=lambda x: -len(x[0])):
        if term.endswith(suffix):
            stem = term[:-len(suffix)]
            if get_measure(stem) > 0:
                term = stem + replacement
                break

    # Step 4
    suffixes = [
        'al', 'ance', 'ence', 'er', 'ic', 'able', 'ible', 'ant', 'ement', 'ment', 'ent',
        'ou', 'ism', 'ate', 'iti', 'ous', 'ive', 'ize'
    ]
    for suffix in sorted(suffixes, key=lambda x: -len(x)):
        if term.endswith(suffix):
            stem = term[:-len(suffix)]
            if get_measure(stem) > 1:
                term = stem
                break
    if term.endswith('ion'):
        stem = term[:-3]
        if get_measure(stem) > 1 and (stem.endswith('s') or stem.endswith('t')):
            term = stem

    # Step 5a
    if term.endswith('e'):
        stem = term[:-1]
        if get_measure(stem) > 1 or (get_measure(stem) == 1 and not cond_o(stem)):
            term = stem

    # Step 5b
    if get_measure(term) > 1 and condition_d(term) and term.endswith('l'):
        term = term[:-1]

    return term

def step1b_helper(term: str) -> str:
    if term.endswith(('at', 'bl', 'iz')):
        return term + 'e'
    if condition_d(term) and not term.endswith(('l', 's', 'z')):
        return term[:-1]
    if get_measure(term) == 1 and cond_o(term):
        return term + 'e'
    return term


def stem_all_documents(collection: list[Document]):
    """
    For each document in the given collection, this method uses the stem_term() function on all terms in its term list.
    Warning: The result is NOT saved in the document's term list, but in the extra field stemmed_terms!
    :param collection: Document collection to process
    """
    # TODO: Implement this function. (PR03)
    for doc in collection:
        doc.stemmed_terms = [stem_term(term) for term in doc.terms]


def stem_query_terms(query: str) -> str:
    """
    Stems all terms in the provided query string.
    :param query: User query, may contain Boolean operators and spaces.
    :return: Query with stemmed terms
    """
    # TODO: Implement this function. (PR03)
    terms = query.split()
    stemmed_terms = [stem_term(term) for term in terms]
    return ' '.join(stemmed_terms)
