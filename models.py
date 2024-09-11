# Contains all retrieval models.

from abc import ABC, abstractmethod
from collections import defaultdict
import re
import math
import hashlib
import random
import bitarray
from document import Document


class RetrievalModel(ABC):
    @abstractmethod
    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        """
        Converts a document into its model-specific representation.
        This is an abstract method and not meant to be edited. Implement it in the subclasses!
        :param document: Document object to be represented
        :param stopword_filtering: Controls, whether the document should first be freed of stopwords
        :param stemming: Controls, whether stemming is used on the document's terms
        :return: A representation of the document. Data type and content depend on the implemented model.
        """
        raise NotImplementedError()

    @abstractmethod
    def query_to_representation(self, query: str):
        """
        Determines the representation of a query according to the model's concept.
        :param query: Search query of the user
        :return: Query representation in whatever data type or format is required by the model.
        """
        raise NotImplementedError()

    @abstractmethod
    def match(self, document_representation, query_representation) -> float:
        """
        Matches the query and document presentation according to the model's concept.
        :param document_representation: Data that describes one document
        :param query_representation:  Data that describes a query
        :return: Numerical approximation of the similarity between the query and document representation. Higher is
        "more relevant", lower is "less relevant".
        """
        raise NotImplementedError()


class LinearBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods and __init__() in this class. (PR02)
    def __init__(self):
        pass

    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        return set(document.terms)

    def query_to_representation(self, query: str):
        return query.lower()

    def match(self, document_representation, query_representation) -> float:
        return 1.0 if query_representation in document_representation else 0.0

    def __str__(self):
        return 'Boolean Model (Linear)'


class InvertedListBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods and __init__() in this class. (PR03)
    def __init__(self):
        self.inverted_index = defaultdict(set)
        self.documents = []

    def document_to_representation(self, document: Document, stop_word_filtering=False, stemming=False):
        words = document.terms
        if stemming:
            words = document.stemmed_terms
        if stop_word_filtering:
            words = document.filtered_terms
        return set(words)

    def query_to_representation(self, query):
        terms = re.findall(r'\(|\)|\w+|&|\||-', query.lower())
        return terms

    def match(self, doc_representation, query_tokens) -> float:
        complete_docs = set(range(len(self.documents)))
        idx = self.inverted_index
        relevant_docs = self.evaluate_expression(query_tokens[:], idx, complete_docs)
        doc_idx = self.documents.index(doc_representation)
        return 1.0 if doc_idx in relevant_docs else 0.0

    def add_document(self, doc: Document, filter_stopwords=False, apply_stemming=False):
        doc_rep = self.document_to_representation(doc, filter_stopwords, apply_stemming)
        self.documents.append(doc_rep)
        doc_idx = len(self.documents) - 1
        for term in doc_rep:
            self.inverted_index[term].add(doc_idx)

    def evaluate_expression(self, token_list, idx, complete_docs):
        evaluation_stack = []
        while token_list:
            current_token = token_list.pop(0)
            if current_token == '(':
                evaluation_stack.append(self.evaluate_expression(token_list, idx, complete_docs))
            elif current_token == ')':
                break
            elif current_token == '&':
                evaluation_stack.append('AND')
            elif current_token == '|':
                evaluation_stack.append('OR')
            elif current_token == '-':
                next_term = token_list.pop(0)
                evaluation_stack.append(complete_docs - idx.get(next_term, set()))
            else:
                evaluation_stack.append(idx.get(current_token, set()))

        expression_result = evaluation_stack.pop(0)
        while evaluation_stack:
            operator = evaluation_stack.pop(0)
            if operator == 'AND':
                expression_result &= evaluation_stack.pop(0)
            elif operator == 'OR':
                expression_result |= evaluation_stack.pop(0)

        return expression_result

    def __str__(self):
        return 'Boolean Model (Inverted List)'


class SignatureBasedBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self, F=64, D=4):
        self.F = F
        self.D = D
        self.m = 1000  # Optimal size of the signature vector (you might need to optimize this)
        self.documents = []
        self.signatures = []
        self.hash_functions = [self._create_hash_function() for _ in range(F)]

    def _create_hash_function(self):
        """Create a hash function."""
        return lambda x, seed=random.randint(0, 2 ** 32): int(hashlib.md5((str(seed) + x).encode()).hexdigest(),
                                                              16) % self.m

    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        if stopword_filtering:
            words = document.filtered_terms
        else:
            words = document.terms

        if stemming:
            words = document.stemmed_terms

        signature = bitarray.bitarray(self.m)
        signature.setall(1)

        for term in words:
            for i, hash_function in enumerate(self.hash_functions):
                signature[hash_function(term)] = 0

        return signature

    def query_to_representation(self, query: str):
        terms = query.lower().split()
        signature = bitarray.bitarray(self.m)
        signature.setall(1)
        for term in terms:
            for i, hash_function in enumerate(self.hash_functions):
                signature[hash_function(term)] = 0

        return signature

    def match(self, document_representation, query_representation) -> float:
        return (document_representation & query_representation).count(0) / self.m

    def __str__(self):
        return 'Boolean Model (Signatures)'

    def add_document(self, doc: Document, filter_stopwords=False, apply_stemming=False):
        doc_rep = self.document_to_representation(doc, filter_stopwords, apply_stemming)
        self.documents.append(doc_rep)


class VectorSpaceModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        self.inverted_index = defaultdict(lambda: defaultdict(float))
        self.doc_lengths = defaultdict(float)
        self.documents = []

    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        terms = document.terms
        if stemming:
            terms = document.stemmed_terms
        if stopword_filtering:
            terms = document.filtered_terms

        term_freq = defaultdict(int)
        for term in terms:
            term_freq[term] += 1

        doc_length = 0
        for term, freq in term_freq.items():
            tf_idf = self._tf_idf(term, freq, document)
            self.inverted_index[term][document.document_id] = tf_idf
            doc_length += tf_idf ** 2

        self.doc_lengths[document.document_id] = math.sqrt(doc_length)
        return term_freq

    def query_to_representation(self, query: str):
        term_freq = defaultdict(int)
        terms = query.lower().split()
        for term in terms:
            term_freq[term] += 1
        return term_freq

    def match(self, document_representation, query_representation) -> float:
        score = 0
        query_length = 0
        doc_id = list(document_representation.keys())[0] if document_representation else None
        if doc_id is None:
            return 0.0

        for term, qtf in query_representation.items():
            doc_tf_idf = self.inverted_index[term].get(doc_id, 0)
            score += doc_tf_idf * qtf
            query_length += qtf ** 2

        query_length = math.sqrt(query_length)
        doc_length = self.doc_lengths.get(doc_id, 1)

        return score / (query_length * doc_length)

    def _tf_idf(self, term, term_freq, document):
        # Compute TF-IDF for a term in a document
        doc_count = len(self.documents)
        df = len(self.inverted_index[term])
        idf = math.log((doc_count + 1) / (1 + df)) + 1
        tf = term_freq
        return tf * idf

    def __str__(self):
        return 'Vector Space Model'

    def add_document(self, doc: Document, filter_stopwords=False, apply_stemming=False):
        self.documents.append(doc)
        self.document_to_representation(doc, filter_stopwords, apply_stemming)


class FuzzySetModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        raise NotImplementedError() # TODO: Remove this line and implement the function.
    
    def __str__(self):
        return 'Fuzzy Set Model'
