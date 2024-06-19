# Contains all retrieval models.

from abc import ABC, abstractmethod
from collections import defaultdict
import re
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
    def __init__(self):
        raise NotImplementedError()  # TODO: Remove this line and implement the function.

    def __str__(self):
        return 'Boolean Model (Signatures)'


class VectorSpaceModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        raise NotImplementedError()  # TODO: Remove this line and implement the function.

    def __str__(self):
        return 'Vector Space Model'


class FuzzySetModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        raise NotImplementedError()  # TODO: Remove this line and implement the function.

    def __str__(self):
        return 'Fuzzy Set Model'
