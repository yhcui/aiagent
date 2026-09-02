import os
import re
from pathlib import Path
from mcp.server.mcpserver import MCPServer, Context

mcp = MCPServer("统计mcp")

@mcp.tool()
def count_desktop_txt_files():
    """统计桌面上的txt文件数量"""
    desktop_path = Path(os.path.expanduser("~/Desktop"))
    txt_files = list(desktop_path.glob("*.txt"))
    return len(txt_files)

@mcp.tool()
def count_unique_words(file_path: str) -> dict[str, object]:
    """
    统计文件中不重复的单词数量
    
    Args:
        file_path: 文件的完整路径或相对路径
        
    Returns:
        包含统计结果的字典：
        - file_path: 文件路径
        - total_words: 总单词数
        - unique_words: 不重复单词数
        - unique_word_list: 不重复单词列表（前20个示例）
    """
    # 解析文件路径（支持绝对路径和相对路径）
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {"error": f"文件不存在: {file_path}"}
    
    if not os.path.isfile(file_path):
        return {"error": f"路径不是文件: {file_path}"}
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"无法读取文件: {str(e)}"}
    
    # 提取单词（只保留字母和数字组成的词）
    words = re.findall(r'[a-zA-Z0-9\u4e00-\u9fff]+', content.lower())
    
    # 去重统计
    unique_words = set(words)
    
    return {
        "file_path": file_path,
        "total_words": len(words),
        "unique_words": len(unique_words),
        "unique_word_list": sorted(list(unique_words))[:20],  # 只返回前20个作为示例
    }

if __name__ == '__main__':
    import sys
    if "mcp" in sys.modules and hasattr(mcp, "_server"):
        # fastmcp 内部已经包了一个官方 Server，直接暴露
        getattr(mcp, "_server").run()
    else:
        # 平时手动 python txt_counter.py 就走 fastmcp 自己的启动
        mcp.run()