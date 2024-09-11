# Contains all functions related to the porter stemming algorithm.
import re
from document import Document

def get_measure(term: str) -> int:
    """
    Returns the measure m of a given term [C](VC){m}[V].
    :param term: Given term/word
    :return: Measure value m
    """
    # Replacing consonant sequences with 'C' and vowel sequences with 'V'
    form = re.sub(r'[^aeiou]+', 'C', term)
    form = re.sub(r'[aeiouy]+', 'V', form)
    # Count the number of VC sequences
    return form.count('VC')


def condition_v(stem: str) -> bool:
    """
    Returns whether condition *v* is true for a given stem (= the stem contains a vowel).
    :param stem: Word stem to check
    :return: True if the condition *v* holds
    """
    return bool(re.search(r'[aeiouy]', stem))


def condition_d(stem: str) -> bool:
    """
    Returns whether condition *d is true for a given stem (= the stem ends with a double consonant (e.g. -TT, -SS)).
    :param stem: Word stem to check
    :return: True if the condition *d holds
    """
    return bool(re.search(r'([^aeiou])\1$', stem))


def cond_o(stem: str) -> bool:
    """
    Returns whether condition *o is true for a given stem (= the stem ends cvc, where the second c is not W, X or Y
    (e.g. -WIL, -HOP)).
    :param stem: Word stem to check
    :return: True if the condition *o holds
    """
    return bool(re.search(r'[^aeiou][aeiouy][^aeiouwxy]$', stem))


def stem_term(term: str) -> str:
    """
    Stems a given term of the English language using the Porter stemming algorithm.
    :param term: The term to be stemmed
    :return: Stemmed term
    """
    term = term.lower()

    def replace_suffix(word, suffix, replacement):
        if word.endswith(suffix):
            return word[:-len(suffix)] + replacement
        return word

    def step_1a(word):
        if word.endswith('sses'):
            return replace_suffix(word, 'sses', 'ss')
        elif word.endswith('ies'):
            return replace_suffix(word, 'ies', 'i')
        elif word.endswith('ss'):
            return word
        elif word.endswith('s'):
            return replace_suffix(word, 's', '')
        return word

    def step_1b(word):
        if word.endswith('eed'):
            stem = replace_suffix(word, 'eed', '')
            if get_measure(stem) > 0:
                word = stem + 'ee'
        elif word.endswith('ed'):
            stem = replace_suffix(word, 'ed', '')
            if condition_v(stem):
                word = stem
                word = step_1b_2(word)
        elif word.endswith('ing'):
            stem = replace_suffix(word, 'ing', '')
            if condition_v(stem):
                word = stem
                word = step_1b_2(word)
        return word

    def step_1b_2(word):
        if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
            return word + 'e'
        elif condition_d(word) and not re.search(r'(ll|ss|zz)$', word):
            return word[:-1]
        elif get_measure(word) == 1 and cond_o(word):
            return word + 'e'
        return word

    def step_1c(word):
        if word.endswith('y'):
            stem = replace_suffix(word, 'y', '')
            if condition_v(stem):
                return stem + 'i'
        return word

    def step_2(word):
        suffixes = {
            'ational': 'ate',
            'tional': 'tion',
            'enci': 'ence',
            'anci': 'ance',
            'izer': 'ize',
            'abli': 'able',
            'alli': 'al',
            'entli': 'ent',
            'eli': 'e',
            'ousli': 'ous',
            'ization': 'ize',
            'ation': 'ate',
            'ator': 'ate',
            'alism': 'al',
            'iveness': 'ive',
            'fulness': 'ful',
            'ousness': 'ous',
            'aliti': 'al',
            'iviti': 'ive',
            'biliti': 'ble'
        }
        for suffix, replacement in suffixes.items():
            if word.endswith(suffix):
                stem = replace_suffix(word, suffix, '')
                if get_measure(stem) > 0:
                    return stem + replacement
        return word

    def step_3(word):
        suffixes = {
            'icate': 'ic',
            'ative': '',
            'alize': 'al',
            'iciti': 'ic',
            'ical': 'ic',
            'ful': '',
            'ness': ''
        }
        for suffix, replacement in suffixes.items():
            if word.endswith(suffix):
                stem = replace_suffix(word, suffix, '')
                if get_measure(stem) > 0:
                    return stem + replacement
        return word

    def step_4(word):
        suffixes = [
            'al', 'ance', 'ence', 'er', 'ic', 'able', 'ible', 'ant', 'ement', 'ment',
            'ent', 'ion', 'ou', 'ism', 'ate', 'iti', 'ous', 'ive', 'ize'
        ]
        for suffix in suffixes:
            if word.endswith(suffix):
                stem = replace_suffix(word, suffix, '')
                if get_measure(stem) > 1:
                    return stem
        return word

    def step_5a(word):
        if word.endswith('e'):
            stem = replace_suffix(word, 'e', '')
            if get_measure(stem) > 1 or (get_measure(stem) == 1 and not cond_o(stem)):
                return stem
        return word

    def step_5b(word):
        if word.endswith('l') and get_measure(word) > 1 and condition_d(word):
            return word[:-1]
        return word

    # Apply the stemming steps in sequence
    term = step_1a(term)
    term = step_1b(term)
    term = step_1c(term)
    term = step_2(term)
    term = step_3(term)
    term = step_4(term)
    term = step_5a(term)
    term = step_5b(term)
    
    return term


def stem_all_documents(collection: list[Document]):
    """
    For each document in the given collection, this method uses the stem_term() function on all terms in its term list.
    Warning: The result is NOT saved in the document's term list, but in the extra field stemmed_terms!
    :param collection: Document collection to process
    """
    for document in collection:
        document.stemmed_terms = [stem_term(term) for term in document.terms]


def stem_query_terms(query: str) -> str:
    """
    Stems all terms in the provided query string.
    :param query: User query, may contain Boolean operators and spaces.
    :return: Query with stemmed terms
    """
    query_terms = query.split()
    stemmed_query_terms = [stem_term(term) for term in query_terms]
    return ' '.join(stemmed_query_terms)
