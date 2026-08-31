#!/usr/bin/env python3
"""
手语词汇 JSON 文件合并导入 MySQL 工具
用法：python import_to_mysql.py
"""

import json
import os
import pymysql
from pathlib import Path

# ============ 配置区 ============
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'sign_language',
    'charset': 'utf8mb4'
}

# JSON 文件到分类名的映射
FILE_CATEGORY_MAP = {
    'common_sign_language_word': 'common',
    'comminicate_sign_language_word': 'communicate',
    'digital_metering_sign_language_word': 'digital_metering',
    'direction_sign_language_word': 'direction',
    'food_sign_language_word': 'food',
    'natural_landscape_sign_language_word': 'natural_landscape',
    'place_names_sign_language_word': 'place_names',
    'place_sign_language_word': 'place',
    'profession_sign_language_word': 'profession',
    'relationship_sign_language_word': 'relationship',
    'season_sign_language_word': 'season',
    'time_sign_language_word': 'time',
    'traffic_sign_language_word': 'traffic',
}

JSON_DIR = Path(__file__).parent
# ================================


def create_table_sql():
    """生成建表 SQL"""
    return """
    CREATE TABLE IF NOT EXISTS sign_language_words (
        id INT AUTO_INCREMENT PRIMARY KEY,
        word_id VARCHAR(50) NOT NULL COMMENT '手语词ID',
        word VARCHAR(100) NOT NULL COMMENT '汉字词汇',
        pinyin VARCHAR(200) COMMENT '拼音',
        video_url VARCHAR(500) COMMENT '视频URL',
        sort_order INT DEFAULT 0 COMMENT '排序序号',
        category VARCHAR(50) NOT NULL COMMENT '分类',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_category (category),
        INDEX idx_word (word),
        INDEX idx_pinyin (pinyin)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='手语词汇表';
    """


def parse_filename_category(filename: str) -> str:
    """从文件名提取分类名"""
    name = Path(filename).stem  # 去掉扩展名
    return FILE_CATEGORY_MAP.get(name, name)


def load_json_data(json_dir: Path) -> list:
    """加载所有 JSON 文件数据"""
    all_records = []
    json_files = list(json_dir.glob('*_sign_language_word.json'))

    print(f"📁 找到 {len(json_files)} 个 JSON 文件\n")

    for json_file in json_files:
        category = parse_filename_category(json_file.name)
        print(f"  📄 {json_file.name} → category: '{category}'")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            record = {
                'word_id': item.get('id', ''),
                'word': item.get('word', ''),
                'pinyin': item.get('pinyin', ''),
                'video_url': item.get('url', ''),
                'sort_order': item.get('sort', 0),
                'category': category,
            }
            all_records.append(record)

    print(f"\n✅ 共加载 {len(all_records)} 条记录\n")
    return all_records


def save_as_csv(records: list, output_path: Path):
    """导出为 CSV 文件（方便检查）"""
    import csv

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['word_id', 'word', 'pinyin', 'video_url', 'sort_order', 'category'])
        writer.writeheader()
        writer.writerows(records)

    print(f"💾 CSV 已导出: {output_path}")


def import_to_mysql(records: list, config: dict):
    """导入 MySQL"""
    try:
        conn = pymysql.connect(**config)
    except Exception as e:
        print(f"❌ MySQL 连接失败: {e}")
        print("\n💡 请确保：")
        print("   1. MySQL 服务已启动")
        print("   2. config.py 中密码正确")
        print("   3. 数据库已创建")
        return False

    try:
        with conn.cursor() as cursor:
            # 建表
            print("🔧 创建表结构...")
            cursor.execute(create_table_sql())

            # 清空旧数据（可选，取消注释启用）
            # cursor.execute("TRUNCATE TABLE sign_language_words")

            # 批量插入
            print("📥 插入数据...")
            insert_sql = """
                INSERT INTO sign_language_words
                (word_id, word, pinyin, video_url, sort_order, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            # 分批插入（每500条提交一次）
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                values = [(r['word_id'], r['word'], r['pinyin'], r['video_url'], r['sort_order'], r['category'])
                          for r in batch]
                cursor.executemany(insert_sql, values)
                conn.commit()
                print(f"   ✓ 已插入 {min(i + batch_size, len(records))}/{len(records)} 条")

            # 验证
            cursor.execute("SELECT COUNT(*) FROM sign_language_words")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT category, COUNT(*) as cnt FROM sign_language_words GROUP BY category ORDER BY cnt DESC")
            categories = cursor.fetchall()

            print(f"\n✅ 导入成功！共 {total} 条记录\n")
            print("📊 分类统计：")
            print("-" * 40)
            for cat, cnt in categories:
                print(f"   {cat:20s} : {cnt:5d} 条")
            print("-" * 40)

            return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    finally:
        conn.close()


def main():
    print("=" * 50)
    print("  手语词汇 JSON → MySQL 导入工具")
    print("=" * 50)
    print()

    # 1. 加载数据
    records = load_json_data(JSON_DIR)

    # 2. 导出 CSV 备份
    csv_path = JSON_DIR / 'sign_language_words.csv'
    save_as_csv(records, csv_path)

    # 3. 导入 MySQL
    print("🔌 连接 MySQL...")
    import_to_mysql(records, MYSQL_CONFIG)

    print("\n✨ 完成！")


if __name__ == '__main__':
    main()
