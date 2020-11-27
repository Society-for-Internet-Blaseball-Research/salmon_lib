import argparse
import mistletoe
from mistletoe.base_renderer import BaseRenderer
from mistletoe.ast_renderer import ASTRenderer
from mistletoe.block_token import Document
from mistletoe.span_token import RawText
from salmon_lib.zhp import ZHP, Page, Line, Style
from functools import reduce

flatten = lambda t: [item for sublist in t for item in sublist]


class PageRenderer(BaseRenderer):
    def __init__(self, zhp):
        super().__init__()
        self.zhp = zhp

    # span tokens: return a Line
    def render_raw_text(self, token):
        text = token.content.encode("cp1252")
        return Line(text=text)

    def render_style(self, token, type, extra_info=0):
        line = self.render_inner_line(token)
        start = 0
        end = len(line.text)
        line.styles.append(
            Style(start=start, end=end, type=type, extra_info=extra_info)
        )
        return line

    def render_strong(self, token):
        return self.render_style(token, type=Style.STYLE_BOLD)

    def render_emphasis(self, token):
        return self.render_style(token, type=Style.STYLE_ITALICS)

    def render_inline_code(self, token):
        return self.render_style(token, type=Style.STYLE_MONO)

    def render_image(self, token):
        raise NotImplementedError

    def render_link(self, token):
        raise NotImplementedError  # TODO

    def render_auto_link(self, token):
        return self.render_inner_line(token)

    def render_escape_sequence(self, token):
        return self.render_inner_line(token)

    def render_strikethrough(self, token):
        raise NotImplementedError("No strikethrough support")

    def render_table_row(self, token):
        raise NotImplementedError("No table support")

    def render_table_cell(self, token):
        raise NotImplementedError("No table support")

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
        return [Line.make_hrule()]

    def render_list_item(self, token):
        return self.render_inner(token)

    def render_list(self, token):
        lines = self.render_inner(token)[0]  # ???
        if token.start is not None:
            first_line_fields = [0, 1, 1, 0, 1, 0, 0, 1]
            continuation_fields = [0, 1, 1, 0, 1, 0, 0, 0]
            type = Style.STYLE_OL
        else:
            first_line_fields = [0, 1, 1, 1, 0, 0, 0, 1]
            continuation_fields = [0, 1, 1, 1, 0, 0, 0, 0]
            type = Style.STYLE_UL
        print(lines)
        for j in lines:
            for i, l in enumerate(j):
                print(l)
                if i == 0:
                    l.unknown_fields = first_line_fields
                else:
                    l.unknown_fields = continuation_fields
                l.styles.append(Style(start=0, end=len(l.text), type=Style.STYLE_OL))
        print(lines)
        return flatten(lines)

    def render_paragraph(self, token):
        return self.render_inner(token)

    def reduce_line(self, line):
        if line == []:
            return Line()
        else:
            return reduce(lambda x, y: x + y, line)

    def render_inner_line(self, token):
        print([self.render(i) for i in token.children])
        print(token.children)
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
        raise NotImplementedError("No quote support")

    def render_table(self, token):
        raise NotImplementedError("No table support")

    # TODO: preprocess links and images
    def compile(self, markdown, title, page_id):
        page_name = f"mapinfo.html#{title.replace(' ','')}".encode("cp1252")
        title = title.encode("cp1252")
        lines = self.render(Document(markdown))
        print(lines)
        page = Page(
            title=title,
            title_id=page_id,
            page_name=b"page_name",
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
        "markdown", default=argparse.SUPPRESS, help="Markdown file to add to zhp"
    )

    args = parser.parse_args()
    print(args)

    with open(args.i, "rb") as f:
        zhp = ZHP.parse(f.read())

    print(zhp.pages[1])

    with open(args.markdown) as f:
        m = f.read()

    print(mistletoe.markdown(m, ASTRenderer))
    with PageRenderer(zhp) as renderer:
        renderer.compile(m, "title", 1337)

    with open(args.o, "wb") as f:
        f.write(zhp.serialize())
