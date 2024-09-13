# Contains all retrieval models.

from abc import ABC, abstractmethod
from collections import defaultdict, Counter
import re
import math
import hashlib
import random
import bitarray
import porter
from document import Document
from collections.abc import Iterable
from cleanup import remove_stop_words_from_term_list

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
    def __init__(self, signature_length=64, num_hash_functions=4,m=20):
        self.signature_length = signature_length
        self.num_hash_functions = num_hash_functions
        self.docs = []
        self.term_hash = {}
        
        self.m=m

    def _compute_hash(self, term):
        
        h= hashlib.md5(term.encode())
        return int(h.hexdigest(), 16) % self.signature_length

    def _generate_signature(self, terms):
        signature = []
        for i in range(0,len(terms),self.num_hash_functions):
            four_terms = terms[i:i+self.num_hash_functions]
            block = [0] * self.signature_length
            
            for term in four_terms:

                single_block = [0] * self.signature_length

                hash_value = self._compute_hash(term)
                random.seed(hash_value)
                active_bits_indices = random.sample(range(self.signature_length), self.m)
                
                for index in active_bits_indices:
                    single_block[index] = 1

                self.term_hash[term]= single_block

                block = [a | b for a, b in zip(block, single_block)]
           
            signature.append(block)
     
        return signature
      

    def document_to_representation(self, document, stopword_filtering=False, stemming=False):
        
        signatures = {}
        if stopword_filtering:
            if isinstance(document, Iterable):
                for d in document:
                    d.terms = remove_stop_words_from_term_list(d.terms)       
  

        if stemming:
            document = porter.stem_all_documents(document)

        for d in document:
            d.terms = [term.lower() for term in d.terms]
     
        
        for d in document:
            signature = self._generate_signature(d.terms)
            signatures[d.document_id] = signature

        return signatures
    
    
    def match(self, document_representation, query_representation) -> float:
        
        tokens = re.split(r'(\(|\)|&|-|\|)', query_representation)
        tokens = [token.strip() for token in tokens if token.strip()]
        operators = []
        stack = []

        doc_ids = []

        query_bits = {}

        bitwise_and = []
        
        for token in tokens:
            if token in ['&','|']:
                operators.append(token)
                
            else:
                query_signature = self.query_to_representation(token)
                query_bits[token] = query_signature
            
                stack.append(query_bits[token])
                while len(stack)>1 and operators:
                    if  '&' in  operators:
                       
                        op1 = stack.pop()
                        op2 = stack.pop()
                        stack.append([bit1 & bit2 for bit1, bit2 in zip(op1, op2)])
                     
                        doc_ids =  self.search(stack[0],document_representation)
        
                    if '|' in operators:
                        op1 = stack.pop()
                        op2 =stack.pop()
                        doc_ids1 =  self.search(op1,document_representation)
                        doc_ids2 =  self.search(op2,document_representation)
                        doc_ids  = list(set(doc_ids1)|set(doc_ids2))
        
        if len(operators) == 0:
            op = stack.pop()
            doc_ids = self.search(op,document_representation)

        
        return doc_ids

    def search(self,query_bits,doc_signature):
   
        resultant_docid = []
        for key, value in doc_signature.items():
               doc_id = key
               docs_sig = value
               for single_block in docs_sig:
                   
                   bitwise_and = [query_bits[i] & single_block[i] for i in range(len(query_bits))]
                   if bitwise_and  == query_bits:
                      
                       resultant_docid.append(doc_id)
                    
                       break
        return resultant_docid

    def query_to_representation(self, query):
        query_hash = []
       
        if query in self.term_hash.keys():
            query_hash= self.term_hash[query]

        return query_hash

    def __str__(self):
        return 'Signature-Based Boolean Model'


class VectorSpaceModel(RetrievalModel):
    def __init__(self):
        self.total_docs = 82
        self.term_frequence = {}
        self.doc_term_count = {}
        self.index = {}
    
    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        
        if stopword_filtering:
            if isinstance(document, Iterable):
                for d in document:
                    d.terms = remove_stop_words_from_term_list(d.terms)          

        if stemming:
            document = porter.stem_all_documents(document)


        self.doc_term_count = {}

        for i in document:
            doc_id = i.document_id
            i.terms = [term.lower() for term in i.terms]
            terms = i.terms
            term_counts = Counter(terms)
            for terms, count in term_counts.items():
                if terms not in self.index.keys():
                    self.index[terms] = []
                self.index[terms].append((doc_id,count))
        
        return document

    def query_to_representation(self, query: str):

        query_terms = query.split(' ')
        query_terms = [term.lower() for term in query_terms]
        term_counts = Counter(query_terms)
        query_length = len(query_terms)
        vector = {term: (count / query_length) * self.calculated_idf(term) for term, count in term_counts.items()}
     
        return vector

    def get_term_frequencey(self,term,doc_id):

        doc_term = self.index[term]
        tf = 0
        for i in doc_term:
            if i[0] == doc_id:
                tf = i[1]

        return tf 


    def get_overall_term_freq(self,term):
        
        tf_overall = 0
        if term in self.index.keys():
            tf_overall = len(self.index[term])
           
        
        return tf_overall

    def calculated_idf(self,term):

        idf = 0
        ni = self.get_overall_term_freq(term)
        
        N = self.total_docs
        if ni != 0:
            idf = math.log(N/ni)
        
        return idf
    
    def calculate_tfidf(self,term,doc_id):

        idf = self.calculated_idf(term)
        tf = self.get_term_frequencey(term,doc_id)

        tf_idf = tf*idf     

        return tf_idf
    
    def vector_calculation(self, doc_id):

        terms = self.index.keys()
        vector = {term: self.calculate_tfidf(term, doc_id) for term in terms}
        return vector
    

    def cosine_similarity(self, vec1, vec2):

        dot_product = sum(vec1[term] * vec2.get(term, 0) for term in vec1)
        norm1 = math.sqrt(sum(v**2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v**2 for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def match(self, document_representation, query_representation) -> float:        
        # For finding the match of the documents selected.
        document_scores = {}
        for i in document_representation:
            
            doc_id = i.document_id
            doc_vector = self.vector_calculation(doc_id)
           
            similarity = self.cosine_similarity(query_representation, doc_vector)

            if similarity >0:
                document_scores[doc_id] = round(similarity,3)
       
        ranked_docs = sorted(document_scores.items(), key=lambda item: item[1], reverse=True)
 
        
        return ranked_docs

    def __str__(self):
        return 'Vector Space Model'


class FuzzySetModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        raise NotImplementedError() # TODO: Remove this line and implement the function.
    
    def __str__(self):
        return 'Fuzzy Set Model'
