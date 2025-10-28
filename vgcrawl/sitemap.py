import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def build_structure(root, discovered, max_depth=None):
    return {
        "root": root,
        "depth": max_depth,
        "discovered_urls": sorted(list(discovered))
    }

def write_output(structure, path):
    path = path.lower()
    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2)
    elif path.endswith(".xml"):
        urlset = Element("urlset")
        root = SubElement(urlset, "root")
        root.text = structure.get("root", "")
        for u in structure.get("discovered_urls", []):
            url = SubElement(urlset, "url")
            loc = SubElement(url, "loc")
            loc.text = u
        raw = tostring(urlset, "utf-8")
        reparsed = minidom.parseString(raw)
        pretty = reparsed.toprettyxml(indent="  ")
        with open(path, "w", encoding="utf-8") as f:
            f.write(pretty)
    else:
        raise ValueError("Output extension must be .json or .xml")
