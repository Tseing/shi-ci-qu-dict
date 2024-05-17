from typing import Literal, Optional, Tuple, Union, List

from lxml import etree
from tqdm import tqdm


def format_element(
    e: etree._Element, tag: str, cls_name: Optional[str] = None
) -> etree._Element:
    e.tag = tag
    e.attrib.clear()
    if cls_name:
        e.set("class", cls_name)
    return e


def remove_element(e: etree._Element) -> None:
    e.getparent().remove(e)


def find_def(s: str) -> Union[Tuple[str, Optional[str]], Literal[-1]]:
    if s.endswith("。"):
        return s, None
    else:
        pass

    idx = s.find("。《")
    if -1 != idx:
        return s[: idx + 1], s[idx + 1 :]
    else:
        pass

    idx = s.find("」《")
    if -1 != idx:
        return s[: idx + 1], s[idx + 1 :]
    else:
        pass

    idx = s.find("。又")
    if -1 != idx:
        return s[: idx + 1], s[idx + 1 :]
    else:
        pass

    idx = s.find("」又")
    if -1 != idx:
        return s[: idx + 1], s[idx + 1 :]
    else:
        pass

    idx = s.find("。")
    if -1 != idx:
        return s[:idx + 1], s[idx + 1:]
    else:
        return -1


def _string(e: etree._Element) -> str:
    return etree.tostring(e, pretty_print=True, encoding="utf-8").decode("utf-8")


# def find_definition(s: str) -> Tuple[str, str]:
#     idx = s.find("。《")
#     return s[: idx + 1], s[idx + 1 :]


class EntryParser:
    def __init__(self, content: etree._Element) -> None:
        self.entry_content = content
        self.entry = etree.Element("div", attrib={"class": "entry"})
        self.title = etree.Element("div", attrib={"class": "title"})
        self.subtitle = etree.Element("div", attrib={"class": "subtitle"})
        self.content = etree.Element("div", attrib={"class": "content"})
        self.p = etree.SubElement(self.content, "p")

        self.definition = None
        self._prev_e = None
        self._residual_text: Optional[str] = None
        self._new_li: bool
        self._has_subtitle: bool
        self._done_starter: bool = False

    def parse(self) -> etree._Element:
        links = tree.findall(".//a[@href]")
        if links:
            return self.parse_href(links)
        else:
            return self.parse_entry()

    def parse_href(self, links: List[etree._Element]) -> etree._Element:
        ul = etree.SubElement(self.content, "ul")
        for link in links:
            li = etree.Element("li")
            li.append(link)
            ul.append(li)

        return ul

    def parse_entry(self) -> etree._Element:
        self.parse_title(self.entry_content)

        for e in self.entry_content:
            # print(
            #     etree.tostring(e, pretty_print=True, encoding="utf-8").decode("utf-8")
            # )
            if not self._done_starter:
                self.parse_def(e)
            elif "font" == e.tag:
                if {"color": "black"} == e.attrib:
                    self.parse_span(e, "emph")
                elif {"color": "red"} == e.attrib:
                    self.parse_span(e, "proper-noun")
                else:
                    assert (
                        False
                    ), f"Unknown tag: {e.tag}, {e.attrib}, {e.text}, {e.tail}."
            else:
                assert False, f"Unknown tag: {e.tag}, {e.attrib}, {e.text}, {e.tail}."

        if self._residual_text:
            self._prev_e.tail = self._residual_text

        ul = etree.SubElement(self.content, "ul")
        for li in self.content.findall(".//li"):
            ul.append(li)

        return self.gen_html()

    def parse_title(self, tree: etree._Element):
        e_title = tree.find(".//font[@size='6']")
        assert not e_title is None, f"Entry has no title:\n'''\n{_string(tree)}'''"
        self.title.text = e_title.text

        e_subtitle = tree.find(".//font[@color='green']")
        if e_subtitle is None:
            self._has_subtitle = False
            self.subtitle = None
            try:
                self.p.text, self._residual_text = find_def(e_title.tail)
            except Exception as e:
                print(f"Invalid Entry:\n'''\n{_string(e_title)}'''")
                raise e
            self._prev_e = self.p
            self._done_starter = True
            self._new_li = True

        else:
            self.subtitle.text = e_subtitle.text

        remove_element(e_title)
        remove_element(self.entry_content[0])

    def parse_def(self, e: etree._Element) -> None:
        # if self._residual_text is None:
        #     self.p.text = e.tail

        if e.tail:
            splits = find_def(e.tail)
            if -1 != splits:
                self.p.text, self._residual_text = find_def(e.tail)
                self._new_li = True
            else:
                self.p.text = e.tail
                self._new_li = False

            self._done_starter = True
            self._prev_e = self.p
        else:
            raise RuntimeError(f"Unexpected format: '{e.text}'.")

    def parse_span(self, e: etree._Element, cls_name: str):
        assert not self._prev_e is None, f"Missing <br> tag, '{e.tag}: {e.text}'."
        span = etree.Element("span", attrib={"class": cls_name})
        span.text = e.text

        if self._new_li:
            li = etree.Element("li")
            li.text = self._residual_text
            li.append(span)
            self.content.append(li)

        else:
            if self._residual_text:
                self._prev_e.tail = self._residual_text
                self._residual_text = None

            self._prev_e.getparent().append(span)

        self._prev_e = span

        if e.tail:
            splits = find_def(e.tail)
            if -1 != splits:
                span.tail, self._residual_text = splits
                self._new_li = True
            else:
                self._residual_text = e.tail
                self._new_li = False

    def gen_html(self) -> etree._Element:

        for element in [self.title, self.subtitle, self.content]:
            if not element is None:
                self.entry.append(element)
        return self.entry


if __name__ == "__main__":
    with open("../data/shi_ci_qu_dict.txt", "r", encoding="utf-8") as f:
        text = f.read()

    entries = text.split("</>")
    entries.pop(entries.index(""))

    f = open("../data/dumped_dict.html", "a+", encoding="utf-8")
    skip_items = [
        "凝",
        "凝佇",
        "凝竚",
        "唱",
        "唱道",
        "常",
        "常好是",
        "常好道",
        "把似",
        "把如",
        "-敍言",
        "是事",
        "是人",
        "是物",
        "是處",
        "是（四）",
        "暢",
        "暢好是",
        "暢好道",
        "暢道",
        "朅來（一）",
        "消凝",
        "竚凝",
        "-跋",
        "銷凝",
        "雲陽"
    ]

    for i, entry in enumerate(entries):
        split_itmes = entry.strip().split("\n")
        key = split_itmes[0]

        if key in skip_items:
            print(f"{i}: {key} is skipped.")
            continue
        else:
            print(f"{i}: {key}")
        html_content = "\n".join(split_itmes[1:])

        tree = etree.HTML(html_content)

        entry_content = tree[0][0]
        parser = EntryParser(entry_content)

        # print(
        #     etree.tostring(parser.parse(), pretty_print=True, encoding="utf-8").decode(
        #         "utf-8"
        #     )
        # )
        # break

        html = (
            etree.tostring(parser.parse(), pretty_print=True, encoding="utf-8")
            .decode("utf-8")
            .replace("<br/>", "")
        )

        entry_s = "\n".join([key, html, "</>\n"]).replace("\n\n", "\n")
        f.write(entry_s)

    f.close()
