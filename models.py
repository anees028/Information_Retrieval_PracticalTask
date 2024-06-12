# Contains all retrieval models.

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Set

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
    def __init__(self, collection: List[Document]):
        self.collection = collection

    def __str__(self):
        return 'Boolean Model (Linear)'

    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        if stopword_filtering:
            return document.filtered_terms
        else:
            return document.terms

    def query_to_representation(self, query: str):
        return query.lower()

    def match(self, document_representation, query_representation) -> float:
        return 1.0 if query_representation in document_representation else 0.0

    def search(self, term: str) -> List[Document]:
        term = self.query_to_representation(term)
        matching_documents = []
        for doc in self.collection:
            document_rep = self.document_to_representation(doc)
            if self.match(document_rep, term):
                matching_documents.append(doc)
        return matching_documents


class InvertedListBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods and __init__() in this class. (PR03)
    def __init__(self):
        self.inverted_list = {}
        self.documents = []

    def __str__(self):
        return 'Boolean Model (Inverted List)'

    def document_to_representation(self, document: Document) -> list[str]:
        # Represent a document as a list of terms
        return document.terms

    def query_to_representation(self, query: str) -> list[str]:
        # Represent a query as a list of terms
        return query.split()

    def match(self, document_representation: list[str], query_representation: list[str]) -> bool:
        # Check if the document representation matches the query representation
        return all(term in document_representation for term in query_representation)

    def add_document(self, document: Document):
        self.documents.append(document)
        doc_id = len(self.documents) - 1
        for term in self.document_to_representation(document):
            if term not in self.inverted_list:
                self.inverted_list[term] = set()
            self.inverted_list[term].add(doc_id)

    def parse_query(self, query: str) -> list[str]:
        return self.query_to_representation(query)

    def evaluate_query(self, query_terms: list[str]) -> set:
        if not query_terms:
            return set()

        # Start with the set of documents containing the first term
        result_set = self.inverted_list.get(query_terms[0], set()).copy()

        # Intersect with the sets of documents containing the other terms
        for term in query_terms[1:]:
            result_set &= self.inverted_list.get(term, set())

        return result_set


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
