"""Tests for content_generator image insertion logic"""
import pytest
from pathlib import Path
from app.core.content_generator import ContentGenerator


class TestInsertImageAtPosition:
    def test_first_image_after_first_paragraph_when_long(self):
        article = "A" * 120 + "\n\n" + "B" * 50 + "\n\n" + "C" * 50
        result = ContentGenerator._insert_image_at_position(article, "/img/header.png", position="first")
        parts = result.split("\n\n")
        assert "![配图](/img/header.png)" in result
        # 图片应插在第一段之后，即索引 1
        assert parts[1] == "\n![配图](/img/header.png)"
        assert parts[0] == "A" * 120

    def test_first_image_after_cumulative_100_chars(self):
        # 第一段不足100字，累计到第二段才超过100字
        article = "A" * 40 + "\n\n" + "B" * 70 + "\n\n" + "C" * 50
        result = ContentGenerator._insert_image_at_position(article, "/img/header.png", position="first")
        parts = result.split("\n\n")
        assert "![配图](/img/header.png)" in result
        # 累计字数：40 + 70 = 110 > 100，应插在第二段后（索引 2）
        assert parts[2] == "\n![配图](/img/header.png)"

    def test_last_image_in_latter_half(self):
        # 6 段，中线为 3，倒数第三段也是索引 3，假设足够长
        paragraphs = ["P" * 30 for _ in range(6)]
        paragraphs[3] = "P" * 120  # 倒数第三段够长
        article = "\n\n".join(paragraphs)
        result = ContentGenerator._insert_image_at_position(article, "/img/footer.png", position="last")
        parts = result.split("\n\n")
        assert "![配图](/img/footer.png)" in result
        # 应插在后半部分开始处（索引 3）之后
        assert parts[3] == "\n![配图](/img/footer.png)"

    def test_last_image_moves_forward_when_short(self):
        # 6 段，中线为 3，倒数第三段较短，从 3 往前累计不足 100 字
        paragraphs = ["P" * 30 for _ in range(6)]
        article = "\n\n".join(paragraphs)
        result = ContentGenerator._insert_image_at_position(article, "/img/footer.png", position="last")
        parts = result.split("\n\n")
        assert "![配图](/img/footer.png)" in result
        # 不应越过中线，插在中线之后（索引 4）
        assert parts[4] == "\n![配图](/img/footer.png)"

    def test_last_image_appends_when_few_paragraphs(self):
        article = "A" * 50 + "\n\n" + "B" * 50
        result = ContentGenerator._insert_image_at_position(article, "/img/footer.png", position="last")
        assert result.endswith("\n![配图](/img/footer.png)\n")

    def test_empty_article(self):
        result = ContentGenerator._insert_image_at_position("", "/img/header.png", position="first")
        assert "![配图](/img/header.png)" in result


class TestBuildImagePrompt:
    def test_header_prompt_contains_theme(self):
        prompt = ContentGenerator._build_image_prompt("数字化转型", position="header")
        assert "WeChat article" in prompt
        assert "数字化转型" in prompt
        assert "featured illustration" in prompt

    def test_footer_prompt_contains_theme(self):
        prompt = ContentGenerator._build_image_prompt("人工智能", position="footer")
        assert "WeChat article" in prompt
        assert "人工智能" in prompt
        assert "concluding illustration" in prompt
