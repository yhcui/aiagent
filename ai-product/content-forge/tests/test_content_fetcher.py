"""ContentFetcher 测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.content_fetcher import ContentFetcher


class TestContentFetcher:
    """ContentFetcher 测试"""

    def test_is_valid_url(self):
        """URL 有效性验证"""
        fetcher = ContentFetcher()

        # 有效 URL
        assert fetcher.is_valid_url("https://example.com")
        assert fetcher.is_valid_url("http://example.com")
        assert fetcher.is_valid_url("https://example.com/path?query=1")

        # 无效 URL
        assert not fetcher.is_valid_url("")
        assert not fetcher.is_valid_url("not-a-url")
        assert not fetcher.is_valid_url("example.com")  # 缺少协议
        assert not fetcher.is_valid_url("ftp://example.com")  # 非 HTTP

    def test_is_valid_url_edge_cases(self):
        """边界情况"""
        fetcher = ContentFetcher()
        assert not fetcher.is_valid_url(None)
        assert not fetcher.is_valid_url("   ")
        assert fetcher.is_valid_url("https://a.co")  # 最短有效 URL


class TestExtractText:
    """正文提取测试"""

    def test_extract_from_wechat(self):
        """微信公众号格式"""
        fetcher = ContentFetcher()
        html = """
        <html>
        <body>
            <div id="js_content">
                这是微信公众号的正文内容，包含多段文字。
                第二段文字内容。
            </div>
        </body>
        </html>
        """
        text = fetcher._extract_text(html, "https://mp.weixin.qq.com/s/test")
        assert "微信公众号" in text
        assert "正文内容" in text

    def test_extract_from_article(self):
        """标准 article 标签"""
        fetcher = ContentFetcher()
        html = """
        <html>
        <body>
            <article>
                <p>文章段落一</p>
                <p>文章段落二</p>
            </article>
        </body>
        </html>
        """
        text = fetcher._extract_text(html, "https://example.com/article")
        assert "文章段落一" in text
        assert "文章段落二" in text

    def test_remove_script_style(self):
        """移除脚本和样式标签"""
        fetcher = ContentFetcher()
        html = """
        <html>
        <script>
            var secret = "不应该出现的脚本内容";
            alert("test");
        </script>
        <style>
            .hidden { display: none; }
        </style>
        <body>
            <p>这是正文内容</p>
        </body>
        </html>
        """
        text = fetcher._extract_text(html, "https://example.com")
        assert "secret" not in text
        assert "alert" not in text
        assert "display: none" not in text
        assert "正文内容" in text

    def test_normalize_whitespace(self):
        """空白字符规范化"""
        fetcher = ContentFetcher()
        html = """
        <html>
        <body>
            <p>第一行


            多个空行</p>
            <p>第二段</p>
        </body>
        </html>
        """
        text = fetcher._extract_text(html, "https://example.com")
        # 不应有超过两个连续换行
        assert "\n\n\n" not in text

    def test_extract_from_main_tag(self):
        """标准 main 标签"""
        fetcher = ContentFetcher()
        html = """
        <html>
        <body>
            <main>
                <h1>标题</h1>
                <p>main标签内容</p>
            </main>
        </body>
        </html>
        """
        text = fetcher._extract_text(html, "https://example.com")
        assert "标题" in text
        assert "main标签内容" in text


class TestFetch:
    """fetch 方法测试（需要 mock）"""

    @patch('app.core.content_fetcher.requests.get')
    def test_fetch_success(self, mock_get):
        """成功抓取"""
        mock_response = Mock()
        # 需要足够长的内容（>100字）才不会触发重试
        mock_response.text = '<html><body><article><p>' + '测试内容' * 50 + '</p></article></body></html>'
        mock_response.apparent_encoding = 'utf-8'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = ContentFetcher()
        result = fetcher.fetch("https://example.com")

        assert "测试内容" in result
        assert mock_get.call_count >= 1

    @patch('app.core.content_fetcher.requests.get')
    def test_fetch_retry_on_error(self, mock_get):
        """失败重试"""
        import requests
        mock_get.side_effect = [
            requests.exceptions.Timeout("timeout"),
            Mock(text='<html><body><p>成功</p></body></html>', apparent_encoding='utf-8', raise_for_status=Mock())
        ]

        fetcher = ContentFetcher()
        result = fetcher.fetch("https://example.com", retry=1)

        assert "成功" in result
        assert mock_get.call_count == 2

    @patch('app.core.content_fetcher.requests.get')
    def test_fetch_max_retries_exceeded(self, mock_get):
        """超过最大重试次数"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        fetcher = ContentFetcher()
        with pytest.raises(requests.exceptions.Timeout):
            fetcher.fetch("https://example.com", retry=0)
