# Contains functions that deal with the extraction of documents from a text file (see PR01)

import json

from document import Document

def extract_collection(source_file_path: str) -> list[Document]:
    """
    Loads a text file (aesopa10.txt) and extracts each of the listed fables/stories from the file.
    :param source_file_name: File name of the file that contains the fables
    :return: List of Document objects
    """
    catalog = []  # This dictionary will store the document raw_data.

    # TODO: Implement this function. (PR02)
    raise NotImplementedError('Not implemented yet!')

    return catalog


def save_collection_as_json(collection: list[Document], file_path: str) -> None:
    """
    Saves the collection to a JSON file.
    :param collection: The collection to store (= a list of Document objects)
    :param file_path: Path of the JSON file
    """
    with open(file_path, "w") as json_file:
        json.dump(collection, json_file)


def load_collection_from_json(file_path: str) -> list[Document]:
    """
    Loads the collection from a JSON file.
    :param file_path: Path of the JSON file
    :return: list of Document objects
    """
    try:
        with open(file_path, "r") as json_file:
            collection = json.load(json_file)
        return collection
    except FileNotFoundError:
        print('No collection was found. Creating empty one.')
        return []
