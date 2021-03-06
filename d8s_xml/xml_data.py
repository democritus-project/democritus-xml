import functools
from typing import Dict, List, Optional, Union
from xml.etree.ElementTree import Element  # nosec

import defusedxml.ElementTree as ET
from d8s_html import html_text, html_to_json

StringOrXmlElement = Union[str, Element]


# @map_first_arg
def xml_read(xml_path: str) -> Element:
    """Read the XML from the given path (which can be a URL, file path, or string) and return an xml Element tree."""
    from d8s_utility import request_or_read

    xml_string = request_or_read(xml_path)
    return ET.fromstring(xml_string)


# @map_first_arg
def is_xml(possible_xml: str) -> bool:
    """Return whether or not possible_xml is valid XML."""
    try:
        xml_read(possible_xml)
    except Exception:  # pylint:disable=W0703
        return False
    else:
        return True


# @map_first_arg
def xml_as_string(xml_input: Element) -> str:
    """Convert the given xml_input to a string."""
    from d8s_strings import bytes_decode_as_string

    xml_string = ET.tostring(xml_input, method='xml')
    # decode bytes as string - todo: make sure the line below is necessary - I don't think I should have to do this
    xml_string = bytes_decode_as_string(xml_string)
    # mypy is failing here because: Incompatible return value type (got "bytes", expected "str")...
    # adding a type annotation to bytes_decode_as_string should fix this
    return xml_string  # type: ignore


def xml_read_first_arg_string(func):
    """Return an XML element for first argument (if it is a string)."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        first_arg = args[0]
        other_args = args[1:]

        if isinstance(first_arg, str):
            first_arg_xml_element = xml_read(first_arg)
            return func(first_arg_xml_element, *other_args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper


def stringify_first_arg_xml_element(func):
    """If the first arg is an XML element, send its string representation into the function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        first_arg = args[0]
        other_args = args[1:]

        if _is_xml_element(first_arg):
            first_arg_string = xml_as_string(first_arg)
            return func(first_arg_string, *other_args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper


def _is_xml_element(possible_element_tree: Element) -> bool:
    return isinstance(possible_element_tree, Element)


@xml_read_first_arg_string
def _xml_iterate(xml_input: StringOrXmlElement, structure: Optional[Dict] = None) -> Dict:
    new_structure: Dict
    if structure is not None:
        new_structure = structure
    else:
        new_structure = {}

    for child in xml_input:
        # mypy fails here: Unsupported target for indexed assignment ("Optional[Dict[Any, Any]]") and...
        # Item "str" of "Union[str, Element]" has no attribute "tag"
        new_structure[child.tag] = _xml_iterate(child, {})  # type: ignore
    return new_structure


# @map_first_arg
@xml_read_first_arg_string
def xml_structure(xml_input: StringOrXmlElement) -> Dict[str, dict]:
    """Return the high-level structure of xml_input."""
    result = _xml_iterate(xml_input, {})
    return result


# @map_first_arg
@stringify_first_arg_xml_element
def xml_to_json(xml_input: StringOrXmlElement) -> Dict[str, List[Dict[str, List[Dict[str, str]]]]]:
    """Convert the xml to json using https://gitlab.com/fhightower/html-to-json."""
    return html_to_json(xml_input)


# @map_first_arg
@stringify_first_arg_xml_element
def xml_text(xml_input: StringOrXmlElement) -> str:
    """Convert the given xml_input to a string."""
    return html_text(xml_input)


# @map_first_arg
def xml_file_names(path: str) -> List[str]:
    """Find all xml files in the given directory."""
    from d8s_file_system import directory_file_names_matching

    files = directory_file_names_matching(path, '*.xml')
    return files
