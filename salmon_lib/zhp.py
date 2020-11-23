# i have no idea what i'm doing

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace, field
from typing import List
import struct


def u32(b):
    return struct.unpack("<I", b)[0]


def p32(x):
    return struct.pack("<I", x)


def prefix_length(b):
    return p32(len(b)) + b


class Buffer:
    def __init__(self, b):
        self.raw = b
        self.fp = 0

    def seek(self, n):
        self.fp = n

    def read(self, n):
        ret = self.raw[self.fp : self.fp + n]
        self.fp += n
        return ret

    def read_int(self):
        return u32(self.read(4))

    def read_str(self):
        length = self.read_int()
        return self.read(length)


class Serializable(ABC):
    @classmethod
    @abstractmethod
    def parse(cls, b: Buffer):  # parse from the current b.fp and advance b.fp
        pass

    @abstractmethod
    def serialize(self):
        pass


@dataclass
class Style(Serializable):
    start: int
    end: int
    type: int
    extra_info: int = 0

    STYLE_LINK = 0x01
    STYLE_BOLD = 0x03
    STYLE_ITALICS = 0x04
    STYLE_MONO = 0x06
    STYLE_H1 = 0x08
    STYLE_H2 = 0x09
    STYLE_H3 = 0x0A
    STYLE_H4 = 0x0B
    STYLE_H5 = 0x0C
    STYLE_H6 = 0x0D
    STYLE_IMAGE = 0x0F
    STYLE_OL = 0x11
    STYLE_UL = 0x15
    STYLE_CODEBLOCK = 0x20

    @classmethod
    def parse(cls, b):
        start = b.read_int()
        end = b.read_int()
        type = b.read_int()
        extra_info = b.read_int()
        return cls(start=start, end=end, type=type, extra_info=extra_info)

    def serialize(self):
        return p32(self.start) + p32(self.end) + p32(self.type) + p32(self.extra_info)


@dataclass
class Line(Serializable):
    text: bytes = b""
    unknown_fields: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0])
    styles: List[Style] = field(default_factory=list)

    @classmethod
    def make_hrule(cls):
        return cls(unknown_fields=[1, 0, 0, 0, 0, 1, 0, 0])

    @classmethod
    def parse(cls, b):
        text_length = b.read_int()
        unknown_fields = []
        for j in range(8):
            unknown_fields.append(b.read_int())
        text = b.read(text_length)
        styles = []
        while True:
            style = Style.parse(b)
            if style.start == 0xFFFF:
                break
            styles.append(style)
        return cls(text=text, unknown_fields=unknown_fields, styles=styles)

    def serialize(self):
        b = b""
        b += p32(len(self.text))
        for i in self.unknown_fields:
            b += p32(i)
        b += self.text
        for i in self.styles:
            b += i.serialize()
        b += b"\xff\xff\x00\x00" * 4
        return b

    # takes the unknown_fields of the left argument
    # mutability is hard
    def __add__(self, other):
        text = self.text + other.text
        unknown_fields = self.unknown_fields
        styles = []
        for i in self.styles:
            styles.append(replace(i))  # copy?
        for i in other.styles:
            start = i.start + len(self.text)
            end = i.end + len(self.text)
            styles.append(replace(i, start=start, end=end))
        return Line(text=text, unknown_fields=unknown_fields, styles=styles)


@dataclass
class Page(Serializable):
    title: bytes
    title_id: int  # ???
    page_name: bytes
    page_id: int  # ???
    lines: List[Line]

    @classmethod
    def parse(cls, b):
        b.read(4)  # length (ignored)
        num_lines = b.read_int()
        title = b.read_str()
        title_id = b.read_int()
        page_name = b.read_str()
        page_id = b.read_int()
        lines = []
        for i in range(num_lines):
            lines.append(Line.parse(b))
        return cls(
            title=title,
            title_id=title_id,
            page_name=page_name,
            page_id=page_id,
            lines=lines,
        )

    def serialize(self):
        b = b""
        b += p32(len(self.lines))
        b += prefix_length(self.title)
        b += p32(self.title_id)
        b += prefix_length(self.page_name)
        b += p32(self.page_id)
        for i in self.lines:
            b += i.serialize()
        return prefix_length(b)


@dataclass
class Image(Serializable):
    data: bytes

    @classmethod
    def parse(cls, b):
        l = b.read_int()
        assert b.read_int() == 0  # ???
        data = b.read(l - 4)
        return cls(data=data)

    def serialize(self):
        return prefix_length(p32(0) + self.data)


@dataclass
class TOCEntry(Serializable):
    title: bytes
    id: int

    @classmethod
    def parse(cls, b):
        title = b.read_str()
        title_id = b.read_int()
        return cls(title=title, id=title_id)

    def serialize(self):
        return prefix_length(self.title) + p32(self.id)


@dataclass
class TOC(Serializable):
    toc: List[TOCEntry]

    @classmethod
    def parse(cls, b):
        toc = []
        b.read(4)  # length (ignored)
        num_toc = b.read_int()
        for i in range(num_toc):
            toc.append(TOCEntry.parse(b))
        return cls(toc=toc)

    def serialize(self):
        b = b""
        for i in self.toc:
            b += i.serialize()
        b = p32(len(self.toc)) + b
        return prefix_length(b)


@dataclass
class Link(Serializable):
    link: bytes
    id: int

    @classmethod
    def parse(cls, b):
        link = b.read_str()
        link_id = b.read_int()
        return cls(link=link, id=link_id)

    def serialize(self):
        return prefix_length(self.link) + p32(self.id)


@dataclass
class Links(Serializable):
    links: List[Link]

    @classmethod
    def parse(cls, b):
        links = []
        b.read(4)  # length (ignored)
        num_links = b.read_int()
        for i in range(num_links):
            links.append(Link.parse(b))
        return cls(links=links)

    def serialize(self):
        b = b""
        for i in self.links:
            b += i.serialize()
        b = p32(len(self.links)) + b
        return prefix_length(b)


@dataclass
class DirectoryEntry(Serializable):
    id: int
    offset: int
    type: int

    @classmethod
    def parse(cls, b):
        id = b.read_int()
        offset = b.read_int()
        type = b.read_int()
        return cls(id=id, offset=offset, type=type)

    def serialize(self):
        return p32(self.id) + p32(self.offset) + p32(self.type)


@dataclass
class Directory(Serializable):
    directory: List[DirectoryEntry]

    @classmethod
    def parse(cls, b):
        directory = []
        num_dir = b.read_int()
        for i in range(num_dir):
            directory.append(DirectoryEntry.parse(b))
        return cls(directory=directory)

    def serialize(self):
        b = b""
        for i in self.directory:
            b += i.serialize()
        b += b"\xff\xff\x00\x00" * 4
        return p32(len(self.directory)) + b


@dataclass
class ZHP(Serializable):
    pages: dict
    images: dict
    toc: TOC
    links: Links

    @classmethod
    def parse(cls, b):
        if type(b) == bytes:
            b = Buffer(b)
        assert b.read(12) == b"ZHELP10000\x01\x00"
        l = b.read_int()
        b.seek(l)

        directory = Directory.parse(b)

        pages = {}
        images = {}
        toc = None
        links = None

        for d in directory.directory:
            b.seek(d.offset)
            if d.type == 1:
                pages[d.id] = Page.parse(b)
            if d.type == 2:
                images[d.id] = Image.parse(b)
            if d.type == 3:
                toc = TOC.parse(b)
            if d.type == 4:
                links = Links.parse(b)
        return cls(pages=pages, images=images, toc=toc, links=links)

    def serialize(self):
        header = b"ZHELP10000\x01\x00"
        entries = b""
        directory = []
        header_offset = len(header) + 4
        # pages
        for d_id, page in self.pages.items():
            d_offset = header_offset + len(entries)
            entries += page.serialize()
            directory.append(DirectoryEntry(id=d_id, offset=d_offset, type=1))
        # images
        for d_id, image in self.images.items():
            d_offset = header_offset + len(entries)
            entries += image.serialize()
            directory.append(DirectoryEntry(id=d_id, offset=d_offset, type=2))
        # toc
        d_offset = header_offset + len(entries)
        entries += self.toc.serialize()
        directory.append(DirectoryEntry(id=0, offset=d_offset, type=3))
        # links
        d_offset = header_offset + len(entries)
        entries += self.links.serialize()
        directory.append(DirectoryEntry(id=0, offset=d_offset, type=4))

        directory = Directory(directory=directory).serialize()

        header += p32(len(header) + 4 + len(entries))  # directory offset
        return header + entries + directory
