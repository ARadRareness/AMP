# -*- coding: cp1252 -*-
from zipfile import ZipFile
from find_lib import *
import os, sys
import urllib.parse

CONTAINER_PATH = "META-INF/container.xml"


def load_epub(fname, split_mode=False):
    with ZipFile(fname) as inzip:
        all_files = inzip.namelist()
        if not CONTAINER_PATH in all_files:
            print(f"ERROR: {CONTAINER_PATH} not found in file {fname}.")
        else:
            files = get_html_files(inzip)

            if split_mode:
                return get_epub_text_split(inzip, files)
            else:
                return get_epub_text(inzip, files)


def get_html_files(epub):
    with epub.open(CONTAINER_PATH) as container:
        data = container.read().decode(errors="ignore")
        content_filename, _ = find_between(data, ["<rootfile", 'full-path="', '"'])

        with epub.open(content_filename[1]) as content:
            base_path = os.path.dirname(content_filename[1])
            data = content.read().decode()

            result_list = []
            for fname in find_all(data, ("<item", 'href="', '"')):
                fname_lower = fname.lower()
                if (
                    fname_lower.endswith(".htm")
                    or fname_lower.endswith(".html")
                    or fname_lower.endswith(".xhtml")
                    or fname_lower.endswith(".xhtm")
                ):
                    if base_path:
                        fname = base_path + "/" + fname
                    result_list.append(fname)

            return result_list


def get_epub_text(epub, files):
    text = ""
    for file in files:
        try:
            text += parse_html(epub, file)
        except:
            print("Warning: Failed to parse a file...")
    return text


def get_epub_text_split(epub, files):
    text = []
    for file in files:
        try:
            h = parse_html(epub, file)
        except:
            print("Warning: Failed to parse a file...")
    return text


def parse_html(epub, file_handle):
    text = ""
    # print(file_handle)
    file_handle = urllib.parse.unquote(file_handle)

    with epub.open(file_handle) as file:
        content = file.read().decode(errors="ignore")

        content = content[content.find("<body") :]

    content = content.replace("\xad", "")
    new_content = ""

    if "<p>" in content:
        content = content.replace("\r", "")

        for line in content.split("\n"):
            new_content += line.strip()

        content = new_content

        content = content.replace("<p>", "\n").replace("</p>", "")

    index = 0

    while index < len(content):
        # print(index)
        r, index = parse_tags(content, index)
        if r:
            text += r
        else:
            cont = True
            while index < len(content) and content[index] != "<":
                text += content[index]
                index += 1
    return text


def parse_tags(content, index):
    if not content[index] == "<":
        return "", index
    else:
        tag_name, index = parse_tag_name(content, index)
        if tag_name == "ruby":
            return parse_ruby_content(content, index)
        else:
            return "", index


def parse_ruby_content(content, index):
    ruby_string = "</ruby>"
    end_index = content.find(ruby_string, index)

    if end_index == -1:
        return "", index

    new_content = content[index:end_index]

    i = 0

    while i != -1:
        for variant in [("<rt>", "</rt>")]:
            i = new_content.find(variant[0])
            i2 = new_content.find(variant[1])

            if i != -1 and i2 != -1:
                new_content = new_content[:i] + new_content[i2 + 5 :]
                break

    new_content = new_content.replace("<rb>", "").replace("</rb>", "")

    return new_content, end_index + len(ruby_string)


def parse_tag_name(content, index):
    if content[index] == "<":
        name = ""
        while index < len(content):
            index += 1
            if content[index] == ">":
                break
            else:
                name += content[index]
        return name, index + 1
    else:
        return "", index


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: EpubLib.py FILE")
    else:
        content = load_epub(sys.argv[1]).replace("\r", "")
        print((content[:1000],))
        with open(sys.argv[1] + ".txt", "w", encoding="utf8") as file:
            file.write(content)
