#!/usr/bin/env python3
"""
手语视频下载爬虫
单线程，间隔2秒，防封
"""

import csv
import os
import time
import requests
from pathlib import Path
from urllib.parse import urlparse

# ============ 配置区 ============
CSV_PATH = Path(__file__).parent / 'sign_language_words.csv'
DOWNLOAD_DIR = Path(__file__).parent / 'videos'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://ai-avatar-static.vivo.com.cn/',
}
INTERVAL = 2  # 间隔秒数
# ================================

DOWNLOAD_DIR.mkdir(exist_ok=True)

# 断点续传：记录已下载的 URL
DONE_FILE = Path(__file__).parent / 'downloaded_urls.txt'


def load_done_urls():
    """加载已下载的 URL"""
    if DONE_FILE.exists():
        with open(DONE_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_done_url(url):
    """保存已下载的 URL"""
    with open(DONE_FILE, 'a', encoding='utf-8') as f:
        f.write(url + '\n')


def get_filename_from_url(url):
    """从 URL 提取文件名"""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    return filename


def download_video(url, save_path, session):
    """下载单个视频"""
    try:
        response = session.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        # 检查 Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'text' in content_type or 'html' in content_type:
            return False, 'Invalid response (HTML or text)'

        # 获取文件大小
        total_size = int(response.headers.get('Content-Length', 0))

        # 下载
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 验证文件
        actual_size = save_path.stat().st_size
        if actual_size < 1000:  # 小于1KB可能是无效文件
            return False, f'Too small file: {actual_size} bytes'

        return True, actual_size

    except requests.exceptions.Timeout:
        return False, 'Timeout'
    except requests.exceptions.RequestException as e:
        return False, str(e)


def main():
    print("=" * 50)
    print("  手语视频下载爬虫")
    print("=" * 50)
    print(f"\n📁 保存目录: {DOWNLOAD_DIR}")
    print(f"⏱️  间隔时间: {INTERVAL} 秒")
    print()

    # 加载 CSV
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        videos = list(reader)

    print(f"📋 CSV 共 {len(videos)} 条记录")

    # 加载已下载记录
    done_urls = load_done_urls()
    pending_videos = [v for v in videos if v['video_url'] not in done_urls]

    print(f"✅ 已有记录: {len(done_urls)}")
    print(f"⏳ 待下载: {len(pending_videos)}")
    print()

    if not pending_videos:
        print("🎉 全部视频已下载完成！")
        return

    # 创建 session 保持连接
    session = requests.Session()
    session.headers.update(HEADERS)

    success_count = len(done_urls)
    fail_count = 0
    fail_list = []

    print("📥 开始下载...\n")

    for i, video in enumerate(pending_videos, 1):
        url = video['video_url']
        word = video['word']
        category = video['category']

        filename = get_filename_from_url(url)
        # 按分类创建子目录
        category_dir = DOWNLOAD_DIR / category
        category_dir.mkdir(exist_ok=True)
        save_path = category_dir / filename

        # 跳过已存在的文件
        if save_path.exists() and save_path.stat().st_size > 1000:
            print(f"  ⏭️  [{i}/{len(pending_videos)}] 跳过 (已存在): {filename}")
            save_done_url(url)
            success_count += 1
            time.sleep(INTERVAL)
            continue

        print(f"  ⬇️  [{i}/{len(pending_videos)}] 下载中: {word} ({filename})")

        success, result = download_video(url, save_path, session)

        if success:
            print(f"      ✅ 成功: {result} bytes")
            save_done_url(url)
            success_count += 1
        else:
            print(f"      ❌ 失败: {result}")
            fail_count += 1
            fail_list.append({'url': url, 'word': word, 'error': result})

        time.sleep(INTERVAL)

    # 保存失败列表
    if fail_list:
        fail_file = Path(__file__).parent / 'download_failed.csv'
        with open(fail_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'word', 'error'])
            writer.writeheader()
            writer.writerows(fail_list)
        print(f"\n⚠️  失败 {fail_count} 条，已保存到: {fail_file}")

    print()
    print("=" * 50)
    print("  下载完成")
    print("=" * 50)
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {fail_count}")
    print(f"  📁 保存目录: {DOWNLOAD_DIR}")


if __name__ == '__main__':
    main()
