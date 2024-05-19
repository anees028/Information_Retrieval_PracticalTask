# Contains functions that deal with the extraction of documents from a text file (see PR01)

import json
from typing import List
from document import Document


def extract_collection(source_file_path: str) -> List[Document]:
    """
    Loads a text file (aesopa10.txt) and extracts each of the listed fables/stories from the file.
    :param source_file_name: File name of the file that contains the fables
    :return: List of Document objects
    """
    catalog = []  # This dictionary will store the document raw_data.

    # TODO: Implement this function. (PR02)
    # raise NotImplementedError('Not implemented yet!')
    catalog = []

    with open(source_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    current_document_id = 0
    current_title = None
    current_text = []
    inside_fable = False

    for i in range(len(lines)):
        if not inside_fable and lines[i].strip() and i > 2 and lines[i - 3].strip() == '':
            inside_fable = True
            current_title = lines[i].strip()
            current_text = []
            continue

        if inside_fable:
            if lines[i].strip() == '' and (i + 1 < len(lines) and lines[i + 1].strip() == ''):
                raw_text = ' '.join(current_text)
                terms = raw_text.split()
                document = Document()
                document.document_id = current_document_id
                document.title = current_title
                document.raw_text = raw_text
                document.terms = terms
                catalog.append(document)
                current_document_id += 1
                inside_fable = False
            else:
                current_text.append(lines[i].strip())

    return catalog


def save_collection_as_json(collection: list[Document], file_path: str) -> None:
    """
    Saves the collection to a JSON file.
    :param collection: The collection to store (= a list of Document objects)
    :param file_path: Path of the JSON file
    """
    with open(file_path, "w", encoding='utf-8') as json_file:
        json.dump([doc.__dict__ for doc in collection], json_file, ensure_ascii=False, indent=4)


def load_collection_from_json(file_path: str) -> list[Document]:
    """
    Loads the collection from a JSON file.
    :param file_path: Path of the JSON file
    :return: list of Document objects
    """
    try:
        with open(file_path, "r", encoding='utf-8') as json_file:
            collection_dicts = json.load(json_file)
        return [Document(**doc) for doc in collection_dicts]
    except FileNotFoundError:
        print('No collection was found. Creating empty one.')
        return []
