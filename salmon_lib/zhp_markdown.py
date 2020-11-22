import argparse
import mistletoe
from mistletoe.base_renderer import BaseRenderer
from mistletoe.ast_renderer import ASTRenderer
from mistletoe.block_token import Document
from mistletoe.span_token import RawText
from salmon_lib.zhp import ZHP, Page, Line, Style
from functools import reduce

flatten = lambda t: [item for sublist in t for item in sublist]

# lol mutability, hopefully there isn't too much reuse of objects
class PageRenderer(BaseRenderer):
    # span tokens: return a Line
    def render_raw_text(self, token):
        text = token.content.encode('utf8')
        return Line(text=text)

    def render_style(self, token, type, extra_info=0):
        line = self.render_inner_line(token)
        start = 0
        end = len(line.text)
        line.styles.append(Style(start=start, end=end, type=type, extra_info=extra_info))
        return line

    def render_strong(self, token):
        return self.render_style(token, type=Style.STYLE_BOLD)

    def render_emphasis(self, token):
        return self.render_style(token, type=Style.STYLE_ITALICS)

    def render_inline_code(self, token):
        return self.render_style(token, type=Style.STYLE_MONO)

    def render_strikethrough(self, token):
        raise NotImplementedError

    def render_image(self, token):
        raise NotImplementedError

    def render_link(self, token):
        raise NotImplementedError

    def render_auto_link(self, token):
        raise self.render_inner_line(token)

    def render_escape_sequence(self, token):
        raise self.render_inner_line(token)

    def render_list_item(self, token):
        raise NotImplementedError

    def render_table_row(self, token):
        raise NotImplementedError

    def render_table_cell(self, token):
        raise NotImplementedError

    # block tokens: return a list of Lines
    def render_block_code(self, token):
        lines = []
        for i in token.children[0].content.split('\n'):
            lines.append(Line(text=i.encode('utf8'), styles=[Style(start=0, end=len(i), type=Style.STYLE_CODEBLOCK)]))
        return lines

    def render_heading(self, token):
        lines = self.render_inner(token)
        type = [Style.STYLE_H1, Style.STYLE_H2, Style.STYLE_H3, Style.STYLE_H4, Style.STYLE_H5, Style.STYLE_H6]
        type = type[token.level-1]
        for i in lines:
            i.styles.append(Style(start=0, end=len(i.text), type=type))
        return lines

    def render_quote(self, token):
        raise NotImplementedError

    def render_thematic_break(self, token):
        return [Line.make_hrule()]

    def render_list(self, token):
        raise NotImplementedError

    def render_table(self, token):
        raise NotImplementedError

    def render_paragraph(self, token):
        return self.render_inner(token)

    def reduce_line(self, line):
        if line == []:
            return Line()
        else:
            return reduce(lambda x,y: x+y, line)

    def render_inner_line(self, token):
        return self.reduce_line([self.render(i) for i in token.children])

    def render_inner(self, token):
        lines = []
        line = []
        for child in token.children:
            if child.__class__.__name__ == "LineBreak":
                if child.soft:
                    line.append(RawText(' '))
                else:
                    lines.append(line)
                    line = []
            else:
                line.append(child)
        lines.append(line)
        return [self.reduce_line([self.render(j) for j in i]) for i in lines]

    def render_document(self, token):
        return flatten([self.render(child) for child in token.children])

    # set stuff up?
    # TODO: this should take a list of markdown files instead of 1
    # TODO: preprocess links and images
    def compile(self, markdown, zhp):
        lines = self.render(Document(markdown))
        print(lines)
        page = Page(title=b'title', title_id=1337, page_name=b'page_name', page_id=1337, lines=lines)
        zhp.pages[1337] = page

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compile and add markdown pages to a .zhp file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", default="crisp2.zhp",
                        metavar='INFILE', help="input zhp filename")
    parser.add_argument("-o", default="crisp2_new.zhp",
                        metavar='OUTFILE', help="output zhp filename")
    parser.add_argument("markdown", default=argparse.SUPPRESS, help="Markdown file to add to zhp")

    args = parser.parse_args()
    print(args)

    with open(args.i, "rb") as f:
        zhp = ZHP.parse(f.read())

    print(zhp.pages[1])

    with open(args.markdown) as f:
        m = f.read()

    print(mistletoe.markdown(m, ASTRenderer))
    with PageRenderer() as renderer:
        renderer.compile(m, zhp=zhp)

    with open(args.o, "wb") as f:
        f.write(zhp.serialize())
