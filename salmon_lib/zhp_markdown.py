import argparse
import mistletoe
from mistletoe.base_renderer import BaseRenderer
from mistletoe.ast_renderer import ASTRenderer
from mistletoe.block_token import Document
from mistletoe.span_token import RawText
from salmon_lib.zhp import ZHP, Page, Line, Image, Style, Link, TOCEntry
from functools import reduce

flatten = lambda t: [item for sublist in t for item in sublist]


def title_to_page_name(title):
    if type(title) == bytes:
        title = title.decode("cp1252")
    if ".html" in title:
        return title.encode("cp1252")
    return f"mapinfo.html#{title.replace(' ','')}".encode("cp1252")


class Gatherer(BaseRenderer):
    def render_image(self, token):
        assert token.src.lower().endswith(".gif"), "only GIF images supported"
        return set([token.src])

    def render_raw_text(self, token):
        return set()

    def render_inner(self, token):
        if not hasattr(token, "children"):
            return set()
        return set.union(*map(self.render, token.children))


class PageRenderer(BaseRenderer):
    def __init__(self, zhp, image_map, filename_map):
        super().__init__()
        self.zhp = zhp
        self.image_map = image_map
        self.filename_map = filename_map

    # span tokens: return a Line
    def render_raw_text(self, token):
        text = token.content.encode("cp1252")
        return Line(text=text)

    def render_style(self, token, type, extra_info=0):
        line = self.render_inner_line(token)
        line.styles.append(
            Style(start=0, end=len(line.text), type=type, extra_info=extra_info)
        )
        return line

    def render_strong(self, token):
        return self.render_style(token, type=Style.STYLE_BOLD)

    def render_emphasis(self, token):
        return self.render_style(token, type=Style.STYLE_ITALICS)

    def render_inline_code(self, token):
        return self.render_style(token, type=Style.STYLE_MONO)

    def render_image(self, token):
        image_id = self.image_map[token.src]
        line = Line(text=f" {image_id} ".encode("cp1252"))
        line.styles.append(
            Style(start=1, end=len(line.text) - 1, type=Style.STYLE_IMAGE)
        )
        return line

    def render_link(self, token):
        line = self.render_inner_line(token)
        if token.target in self.filename_map:
            target = self.filename_map[token.target]
        else:
            target = token.target.encode("cp1252")
        for i in self.zhp.links.links:
            if i.link == target:
                return self.render_style(token, type=Style.STYLE_LINK, extra_info=i.id)
        raise RuntimeError(f"Could not find link {token.target}")

    def render_auto_link(self, token):
        return self.render_inner_line(token)

    def render_escape_sequence(self, token):
        return self.render_inner_line(token)

    def render_strikethrough(self, token):
        raise RuntimeError("No strikethrough support")

    def render_table_row(self, token):
        raise RuntimeError("No table support")

    def render_table_cell(self, token):
        raise RuntimeError("No table support")

    # block tokens: return a list of Lines
    def render_block_code(self, token):
        lines = []
        for i in token.children[0].content.split("\n"):
            lines.append(
                Line(
                    text=i.encode("cp1252"),
                    styles=[Style(start=0, end=len(i), type=Style.STYLE_CODEBLOCK)],
                )
            )
        return lines

    def render_heading(self, token):
        lines = self.render_inner(token)
        type = [
            Style.STYLE_H1,
            Style.STYLE_H2,
            Style.STYLE_H3,
            Style.STYLE_H4,
            Style.STYLE_H5,
            Style.STYLE_H6,
        ]
        type = type[token.level - 1]
        for i in lines:
            i.styles.append(Style(start=0, end=len(i.text), type=type))
        return lines

    def render_thematic_break(self, token):
        return [Line(unknown_fields=Line.FIELDS_HRULE)]

    def render_list_item(self, token):
        return self.render_inner(token)

    def render_list(self, token):
        lines = self.render_inner(token)[0]  # ???
        if token.start is not None:
            first_line_fields = Line.FIELDS_OL_FIRST
            continuation_fields = Line.FIELDS_OL_CONT
            type = Style.STYLE_OL
        else:
            first_line_fields = Line.FIELDS_UL_FIRST
            continuation_fields = Line.FIELDS_UL_CONT
            type = Style.STYLE_UL
        for j in lines:
            for i, l in enumerate(j):
                if i == 0:
                    l.unknown_fields = first_line_fields
                else:
                    l.unknown_fields = continuation_fields
                l.styles.append(Style(start=0, end=len(l.text), type=Style.STYLE_OL))
        return flatten(lines)

    def render_paragraph(self, token):
        return self.render_inner(token)

    def reduce_line(self, line):
        if line == []:
            return Line()
        else:
            return reduce(lambda x, y: x + y, line)

    def render_inner_line(self, token):
        return self.reduce_line([self.render(i) for i in token.children])

    def render_inner(self, token):
        lines = []
        line = []
        for child in token.children:
            if child.__class__.__name__ == "LineBreak":
                if child.soft:
                    line.append(RawText(" "))
                else:
                    lines.append(line)
                    line = []
            else:
                line.append(child)
        lines.append(line)
        return [self.reduce_line([self.render(j) for j in i]) for i in lines]

    def render_document(self, token):
        return flatten([self.render(child) for child in token.children])

    def render_quote(self, token):
        raise RuntimeError("No quote support")

    def render_table(self, token):
        raise RuntimeError("No table support")

    # TODO: preprocess links and images
    def compile(self, markdown, title, page_name, page_id):
        lines = self.render(Document(markdown))
        page = Page(
            title=title,
            title_id=page_id,
            page_name=page_name,
            page_id=page_id,
            lines=lines,
        )
        self.zhp.pages[page_id] = page


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile and add markdown pages to a .zhp file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i", default="crisp2.zhp", metavar="INFILE", help="input zhp filename"
    )
    parser.add_argument(
        "-o", default="crisp2_new.zhp", metavar="OUTFILE", help="output zhp filename"
    )
    parser.add_argument(
        "toc",
        default=argparse.SUPPRESS,
        help="TOC of markdown files: `[title], [filename]` pairs, 1 per each line",
    )

    args = parser.parse_args()

    with open(args.i, "rb") as f:
        zhp = ZHP.parse(f.read())

    filename_map = {}

    pages = []
    page_id = max(zhp.pages) + 1
    for line in open(args.toc):
        title, filename = [i.strip() for i in line.split(",")]
        print(f"adding page {title} ({filename})")
        title = title.encode("cp1252")
        page_name = title_to_page_name(title)
        with open(filename) as f:
            m = f.read()
        filename_map[filename] = page_name
        pages.append((m, title, page_name, page_id))
        zhp.links.links.append(Link(link=page_name, id=page_id))
        zhp.toc.toc.append(TOCEntry(title=title, id=page_id))
        page_id += 1

    image_id = max(zhp.images) + 1
    image_map = {}
    images = set()

    for m, _, _, _ in pages:
        with Gatherer() as renderer:
            images |= renderer.render(Document(m))

    for i in images:
        print(f"adding image {i}")
        with open(i, "rb") as f:
            zhp.images[image_id] = Image(data=f.read())
        image_map[i] = image_id
        image_id += 1

    for m, title, page_name, page_id in pages:
        with PageRenderer(zhp, image_map, filename_map) as renderer:
            renderer.compile(m, title, page_name, page_id)

    with open(args.o, "wb") as f:
        f.write(zhp.serialize())
