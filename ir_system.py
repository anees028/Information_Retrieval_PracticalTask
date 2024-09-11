# --------------------------------------------------------------------------------
# Information Retrieval SS2024 - Practical Assignment Template
# --------------------------------------------------------------------------------
# This Python template is provided as a starting point for your assignments PR02-04.
# It serves as a base for a very rudimentary text-based information retrieval system.
#
# Please keep all instructions from the task description in mind.
# Especially, avoid changing the base structure, function or class names or the
# underlying program logic. This is necessary to run automated tests on your code.
#
# Instructions:
# 1. Read through the whole template to understand the expected workflow and outputs.
# 2. Implement the required functions and classes, filling in your code where indicated.
# 3. Test your code to ensure functionality and correct handling of edge cases.
#
# Good luck!


import json
import os
import time

import cleanup
import extraction
import models
import porter
from document import Document

# Important paths:
RAW_DATA_PATH = 'raw_data'
DATA_PATH = 'data'
COLLECTION_PATH = os.path.join(DATA_PATH, 'my_collection.json')
STOPWORD_FILE_PATH = os.path.join(DATA_PATH, 'stopwords.json')
GROUND_TRUTH_PATH = os.path.join(RAW_DATA_PATH, 'ground_truth.txt')

# Menu choices:
(CHOICE_LIST, CHOICE_SEARCH, CHOICE_EXTRACT, CHOICE_UPDATE_STOP_WORDS, CHOICE_SET_MODEL, CHOICE_SHOW_DOCUMENT,
 CHOICE_EXIT) = 1, 2, 3, 4, 5, 6, 9
MODEL_BOOL_LIN, MODEL_BOOL_INV, MODEL_BOOL_SIG, MODEL_FUZZY, MODEL_VECTOR = 1, 2, 3, 4, 5
SW_METHOD_LIST, SW_METHOD_CROUCH = 1, 2


class InformationRetrievalSystem(object):
    def __init__(self):
        if not os.path.isdir(DATA_PATH):
            os.makedirs(DATA_PATH)

        # Collection of documents, initially empty.
        try:
            self.collection = extraction.load_collection_from_json(COLLECTION_PATH)
        except FileNotFoundError:
            print('No previous collection was found. Creating empty one.')
            self.collection = []

        # Stopword list, initially empty.
        try:
            with open(STOPWORD_FILE_PATH, 'r') as f:
                self.stop_word_list = json.load(f)
        except FileNotFoundError:
            print('No stopword list was found.')
            self.stop_word_list = []

        self.model = None  # Saves the current IR model in use.
        self.output_k = 5  # Controls how many results should be shown for a query.
        self.ground_truth = self.load_ground_truth(GROUND_TRUTH_PATH)  # Load ground truth data

    def main_menu(self):
        """
        Provides the main loop of the CLI menu that the user interacts with.
        """
        while True:
            print(f'Current retrieval model: {self.model}')
            print(f'Current collection: {len(self.collection)} documents')
            print()
            print('Please choose an option:')
            print(f'{CHOICE_LIST} - List documents')
            print(f'{CHOICE_SEARCH} - Search for term')
            print(f'{CHOICE_EXTRACT} - Build collection')
            print(f'{CHOICE_UPDATE_STOP_WORDS} - Rebuild stopword list')
            print(f'{CHOICE_SET_MODEL} - Set model')
            print(f'{CHOICE_SHOW_DOCUMENT} - Show a specific document')
            print(f'{CHOICE_EXIT} - Exit')
            action_choice = int(input('Enter choice: '))

            if action_choice == CHOICE_LIST:
                # List documents in CLI.
                if self.collection:
                    for document in self.collection:
                        print(document)
                else:
                    print('No documents.')

            elif action_choice == CHOICE_SEARCH:
                # Read a query string from the CLI and search for it.

                # Determine desired search parameters:
                SEARCH_NORMAL, SEARCH_SW, SEARCH_STEM, SEARCH_SW_STEM = 1, 2, 3, 4
                print('Search options:')
                print(f'{SEARCH_NORMAL} - Standard search (default)')
                print(f'{SEARCH_SW} - Search documents with removed stopwords')
                print(f'{SEARCH_STEM} - Search documents with stemmed terms')
                print(f'{SEARCH_SW_STEM} - Search documents with removed stopwords AND stemmed terms')
                search_mode = int(input('Enter choice: '))
                stop_word_filtering = (search_mode == SEARCH_SW) or (search_mode == SEARCH_SW_STEM)
                stemming = (search_mode == SEARCH_STEM) or (search_mode == SEARCH_SW_STEM)

                # Actual query processing begins here:
                query = input('Query: ')
                if stemming:
                    query = porter.stem_query_terms(query)

                start_time = time.time()  # Start timing

                if isinstance(self.model, models.InvertedListBooleanModel):
                    results = self.inverted_list_search(query, stemming, stop_word_filtering)
                elif isinstance(self.model, models.VectorSpaceModel):
                    results = self.buckley_lewit_search(query, stemming, stop_word_filtering)
                elif isinstance(self.model, models.SignatureBasedBooleanModel):
                    results = self.signature_search(query, stemming, stop_word_filtering)
                else:
                    results = self.basic_query_search(query, stemming, stop_word_filtering)

                end_time = time.time()  # End timing
                processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

                # Output of results:
                for (score, document) in results:
                    print(f'{score}: {document}')

                # Output of quality metrics:
                precision = self.calculate_precision(query, results)
                recall = self.calculate_recall(query, results)
                print()
                print(f'precision: {precision}')
                print(f'recall: {recall}')
                print(f'Time taken for query processing: {processing_time:.2f} ms')

            elif action_choice == CHOICE_EXTRACT:
                # Extract document collection from text file.

                raw_collection_file = os.path.join(RAW_DATA_PATH, 'aesopa10.txt')
                self.collection = extraction.extract_collection(raw_collection_file)
                assert isinstance(self.collection, list)
                assert all(isinstance(d, Document) for d in self.collection)

                if input('Should stopwords be filtered? [y/N]: ') == 'y':
                    cleanup.filter_collection(self.collection)

                if input('Should stemming be performed? [y/N]: ') == 'y':
                    porter.stem_all_documents(self.collection)

                extraction.save_collection_as_json(self.collection, COLLECTION_PATH)
                print('Done.\n')

            elif action_choice == CHOICE_UPDATE_STOP_WORDS:
                # Rebuild the stop word list, using one out of two methods.

                print('Available options:')
                print(f'{SW_METHOD_LIST} - Load stopword list from file')
                print(f"{SW_METHOD_CROUCH} - Generate stopword list using Crouch's method")

                method_choice = int(input('Enter choice: '))
                if method_choice in (SW_METHOD_LIST, SW_METHOD_CROUCH):
                    # Load stop words using the desired method:
                    if method_choice == SW_METHOD_LIST:
                        self.stop_word_list = cleanup.load_stop_word_list(os.path.join(RAW_DATA_PATH, 'englishST.txt'))
                        print('Done.\n')
                    elif method_choice == SW_METHOD_CROUCH:
                        self.stop_word_list = cleanup.create_stop_word_list_by_frequency(self.collection)
                        print('Done.\n')

                    # Save new stopword list into file:
                    with open(STOPWORD_FILE_PATH, 'w') as f:
                        json.dump(self.stop_word_list, f)
                else:
                    print('Invalid choice.')

            elif action_choice == CHOICE_SET_MODEL:
                # Choose and set the retrieval model to use for searches.

                print()
                print('Available models:')
                print(f'{MODEL_BOOL_LIN} - Boolean model with linear search')
                print(f'{MODEL_BOOL_INV} - Boolean model with inverted lists')
                print(f'{MODEL_BOOL_SIG} - Boolean model with signature-based search')
                print(f'{MODEL_FUZZY} - Fuzzy set model')
                print(f'{MODEL_VECTOR} - Vector space model')
                model_choice = int(input('Enter choice: '))
                if model_choice == MODEL_BOOL_LIN:
                    self.model = models.LinearBooleanModel()  # Passing the collection.
                elif model_choice == MODEL_BOOL_INV:
                    self.model = models.InvertedListBooleanModel()
                elif model_choice == MODEL_BOOL_SIG:
                    self.model = models.SignatureBasedBooleanModel()
                elif model_choice == MODEL_FUZZY:
                    self.model = models.FuzzySetModel()
                elif model_choice == MODEL_VECTOR:
                    self.model = models.VectorSpaceModel()
                else:
                    print('Invalid choice.')

            elif action_choice == CHOICE_SHOW_DOCUMENT:
                target_id = int(input('ID of the desired document:'))
                found = False
                for document in self.collection:
                    if document.document_id == target_id:
                        print(document.title)
                        print('-' * len(document.title))
                        print(document.raw_text)
                        found = True

                if not found:
                    print(f'Document #{target_id} not found!')

            elif action_choice == CHOICE_EXIT:
                break
            else:
                print('Invalid choice.')

            print()
            input('Press ENTER to continue...')
            print()

    def basic_query_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Searches the collection for a query string. This method is "basic" in that it does not use any special algorithm
        to accelerate the search. It simply calculates all representations and matches them, returning a sorted list of
        the k most relevant documents and their scores.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        query_representation = self.model.query_to_representation(query)
        document_representations = [self.model.document_to_representation(d, stop_word_filtering, stemming)
                                    for d in self.collection]
        scores = [self.model.match(dr, query_representation) for dr in document_representations]
        ranked_collection = sorted(zip(scores, self.collection), key=lambda x: x[0], reverse=True)
        results = ranked_collection[:self.output_k]
        return results

    def inverted_list_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Fast Boolean query search for inverted lists.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        # TODO: Implement this function (PR03)
        for doc in self.collection:
            self.model.add_document(doc, stop_word_filtering, stemming)
        query_representation = self.model.query_to_representation(query)
        document_representations = [self.model.document_to_representation(d, stop_word_filtering, stemming) for
                                    d in self.collection]
        scores = [self.model.match(dr, query_representation) for dr in document_representations]
        ranked_collection = sorted(zip(scores, self.collection), key=lambda x: x[0], reverse=True)
        return ranked_collection[:5]

    def buckley_lewit_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Fast query search for the Vector Space Model using the algorithm by Buckley & Lewit.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        # TODO: Implement this function (PR04)
        for doc in self.collection:
            self.model.add_document(doc, stop_word_filtering, stemming)

        query_representation = self.model.query_to_representation(query)
        document_representations = [self.model.document_to_representation(d, stop_word_filtering, stemming)
                                    for d in self.collection]

        # Calculate scores
        scores = [self.model.match(dr, query_representation) for dr in document_representations]
        ranked_collection = sorted(zip(scores, self.collection), key=lambda x: x[0], reverse=True)
        return ranked_collection[:5]

    def signature_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Fast Boolean query search using signatures for quicker processing.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        # TODO: Implement this function (PR04)
        for doc in self.collection:
            self.model.add_document(doc, stop_word_filtering, stemming)

            # Get query representation
        query_representation = self.model.query_to_representation(query)

        # Calculate scores
        scores = []
        for doc in self.collection:
            doc_representation = self.model.document_to_representation(doc, stop_word_filtering, stemming)
            score = self.model.match(doc_representation, query_representation)
            scores.append((score, doc))

        # Sort and return top results
        ranked_collection = sorted(scores, key=lambda x: x[0], reverse=True)
        return ranked_collection[:self.output_k]

    def load_ground_truth(self, ground_truth_path: str) -> dict:
        """
        Load the ground truth data from a file.
        :param ground_truth_path: Path to the ground truth file
        :return: Dictionary with query terms as keys and sets of relevant document IDs as values
        """
        ground_truth = {}
        with open(ground_truth_path, 'r') as file:
            for line in file:
                if (line == '\n'):
                    break
                parts = line.strip().split(' - ')
                if len(parts) == 2:
                    query_term, doc_ids_str = parts
                    doc_ids = set(map(int, doc_ids_str.split(', ')))
                    ground_truth[query_term] = doc_ids
        return ground_truth

    def calculate_precision(self, query: str, result_list: list[tuple]) -> float:
        # Split and normalize the query
        query_terms = query.lower().split()

        # Collect relevant document IDs based on the query terms
        relevant_doc_ids = set()
        for term in query_terms:
            relevant_doc_ids.update(self.ground_truth.get(term, set()))

        # Print relevant_doc_ids for debugging
        print("Relevant Document IDs:", relevant_doc_ids)

        if not relevant_doc_ids:
            return -1

        retrieved_doc_ids = {doc.document_id for score, doc in result_list}

        # Print retrieved_doc_ids for debugging
        print("Retrieved Document IDs:", retrieved_doc_ids)
        
        if not retrieved_doc_ids:
            return 0.0

        # Calculate precision
        true_positive = len(relevant_doc_ids & retrieved_doc_ids)
        precision = true_positive / len(retrieved_doc_ids)
        
        return precision



    def calculate_recall(self, query: str, result_list: list[tuple]) -> float:
        query_terms = query.split()

        # Collect relevant document IDs based on the query terms
        relevant_doc_ids = set()
        for term in query_terms:
            relevant_doc_ids.update(self.ground_truth.get(term, set()))

        if not relevant_doc_ids:
            return -1

        retrieved_doc_ids = {doc.document_id for score, doc in result_list}

        if not retrieved_doc_ids:
            return 0.0
        
        # Calculate recall
        true_positive = len(retrieved_doc_ids & relevant_doc_ids)
        recall = true_positive / len(relevant_doc_ids)
        return recall


if __name__ == '__main__':
    irs = InformationRetrievalSystem()
    irs.main_menu()
    exit(0)
