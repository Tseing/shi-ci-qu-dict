from lxml import etree

if __name__ == "__main__":
    with open("../data/dumped_dict.html", "r", encoding="utf-8") as f:
        text = f.read()

    entries = text.split("</>")
    entries.pop(entries.index(""))

    search_map = {}
    unique_entry_map = {}
    list_entries = {}

    for i, entry in enumerate(entries):
        split_items = entry.strip().split("\n")
        search_key = split_items[0]
        html_content = "\n".join(split_items[1:])

        tree = etree.HTML(html_content)

        e_title = tree.find(".//div[@class='title']")
        if e_title is None:
            e_title = tree.find(".//font[@size='6']")

        if not e_title is None:
            primary_key = e_title.text
            assert not primary_key is None, f"{html_content}"
            unique_entry_map.update({primary_key: html_content})
            search_map.update({primary_key: primary_key})
        else:
            list_entries.update({search_key: html_content})

        e_subtitle = tree.find(".//div[@class='subtitle']")

        if not e_subtitle is None:
            variant_keys = e_subtitle.text.split("\u3000")
            search_map.update({vk: primary_key for vk in variant_keys})

    unique_entry_s = "\n".join(
        [
            "\n".join([pk, unique_entry_map[pk], "</>"])
            for pk in sorted(unique_entry_map.keys())
        ]
    )

    search_key_s = "\n".join(
        [
            "\t".join([search_key, search_map[search_key]])
            for search_key in sorted(search_map.keys())
        ]
    )

    skipped_entry_s = "\n".join(
        [
            "\n".join([pk, list_entries[pk], "</>"])
            for pk in sorted(list_entries.keys())
        ]
    )

    with open("../data/unique_entries.html", "w+", encoding="utf-8") as f:
        f.write(unique_entry_s)

    with open("../data/search_keys.tsv", "w+", encoding="utf-8") as f:
        f.write(search_key_s)

    with open("../data/list_entries.html", "w+", encoding="utf-8") as f:
        f.write(skipped_entry_s)