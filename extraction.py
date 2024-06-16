# Contains functions that deal with the extraction of documents from a text file (see PR01)

import json
import re
from typing import List
from document import Document


def extract_collection(source_file_path: str) -> List[Document]:
    """
    Loads a text file (aesopa10.txt) and extracts each of the listed fables/stories from the file.
    :param source_file_path: File name of the file that contains the fables
    :return: List of Document objects
    """
    catalog = []  # This dictionary will store the document raw_data.
    fables = ""
    current_document_id = 0
    title = "The Cock and the Pearl"
    # TODO: Implement this function. (PR02)
    # raise NotImplementedError('Not implemented yet!')

    with open(source_file_path, 'r') as file:
        lines = file.read()

    inside_fable = False  # parse flag
    for line in lines.split('\n'):
        line = line.strip()
        if line == title:
            inside_fable = True

        if inside_fable == True:
            fables += line

    fables_entries = lines.split('\n\n\n\n')

    for i,entry in enumerate(fables_entries):
        if i > 1:
            lines=entry.split('\n\n\n')
            document = Document()

            document.document_id = current_document_id
            document.title = lines[0]
            document.raw_text = lines[1]
            document.terms = re.findall(r'\b\w+\b', lines[1].lower())
            document.filtered_terms = []

            catalog.append(document)
            current_document_id += 1

    return catalog


def save_collection_as_json(collection: list[Document], file_path: str) -> None:
    """
    Saves the collection to a JSON file.
    :param collection: The collection to store (= a list of Document objects)
    :param file_path: Path of the JSON file
    """
    serializable_collection = []
    for doc in collection:
        serializable_collection.append({
            'document_id': doc.document_id,
            'title': doc.title,
            'raw_text': doc.raw_text,
            'terms': doc.terms,
            'filtered_terms': doc.filtered_terms,
            'stemmed_terms': doc.stemmed_terms
        })

    with open(file_path, "w") as json_file:
        json.dump(serializable_collection, json_file)


def load_collection_from_json(file_path: str) -> list[Document]:
    """
    Loads the collection from a JSON file.
    :param file_path: Path of the JSON file
    :return: list of Document objects
    """
    try:
        with open(file_path, "r") as json_file:
            json_data = json.load(json_file)

        collection = []
        for item in json_data:
            doc = Document()
            doc.document_id = item.get('document_id')
            doc.title = item.get('title')
            doc.raw_text = item.get('raw_text')
            doc.terms = item.get('terms')
            doc.filtered_terms = item.get('filtered_terms')
            doc.stemmed_terms = item.get('stemmed_terms')
            collection.append(doc)

        return collection
    except FileNotFoundError:
        print('No collection was found. Creating empty one.')
        return []
