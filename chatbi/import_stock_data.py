# -*- coding: utf-8 -*-
import openpyxl
import pymysql
bt = chr(96)
q = chr(39)

wb = openpyxl.load_workbook('D:/OpenCode-Project/aiagent/chatbi/final_merged_stock_data_20200101_to_20251220.xlsx', read_only=True)
ws = wb.active
rows = ws.iter_rows(values_only=True)
headers = list(next(rows))
data_rows = list(rows)
print('Data rows:', len(data_rows))

cols_names = ', '.join(bt + h + bt for h in headers)
ph = ', '.join(['%s'] * len(headers))

def sql_escape(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return q + v.replace(q, '\\'+q) + q
    if isinstance(v, (int, float)): return str(v)
    return q + str(v).replace(q, '\\'+q) + q

cc = [
  bt+'id'+bt+' BIGINT AUTO_INCREMENT PRIMARY KEY',
  bt+'ts_code'+bt+' VARCHAR(20)',
  bt+'trade_date'+bt+' VARCHAR(12)',
  bt+'open'+bt+' DECIMAL(12,4)',
  bt+'high'+bt+' DECIMAL(12,4)',
  bt+'low'+bt+' DECIMAL(12,4)',
  bt+'close'+bt+' DECIMAL(12,4)',
  bt+'pre_close'+bt+' DECIMAL(12,4)',
  bt+'change'+bt+' DECIMAL(12,4)',
  bt+'pct_chg'+bt+' DECIMAL(10,4)',
  bt+'vol'+bt+' DECIMAL(18,4)',
  bt+'amount'+bt+' DECIMAL(18,4)',
  bt+'stock_name'+bt+' VARCHAR(50)',
  'UNIQUE KEY '+bt+'uk_ts_trade'+bt+' ('+bt+'ts_code'+bt+', '+bt+'trade_date'+bt+')',
  'INDEX '+bt+'idx_trade_date'+bt+' ('+bt+'trade_date'+bt+')',
  'INDEX '+bt+'idx_ts_code'+bt+' ('+bt+'ts_code'+bt+')',
  'INDEX '+bt+'idx_stock_name'+bt+' ('+bt+'stock_name'+bt+')',
]
create_sql = 'CREATE TABLE daily_kline (\n  ' + ',\n  '.join(cc) + ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'

sql_lines = []
sql_lines.append('-- Stock data from Tushare')
sql_lines.append('CREATE DATABASE IF NOT EXISTS stock_data DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
sql_lines.append('USE stock_data;')
sql_lines.append('')
sql_lines.append('DROP TABLE IF EXISTS daily_kline;')
sql_lines.append(create_sql + ';')
sql_lines.append('')
batch_size = 500
for i in range(0, len(data_rows), batch_size):
    batch = data_rows[i:i+batch_size]
    vals = []
    for r in batch:
        esc = [sql_escape(v) for v in r]
        vals.append('(' + ', '.join(esc) + ')')
    sql_lines.append('INSERT INTO daily_kline (' + cols_names + ') VALUES ')
    sql_lines.append(','.join(vals) + ';')
    sql_lines.append('')
sql_content = '\n'.join(sql_lines)
with open('D:/OpenCode-Project/aiagent/chatbi/stock_data.sql', 'w', encoding='utf-8') as f:
    f.write(sql_content)
print('SQL file written')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', charset='utf8mb4')
cur = conn.cursor()
cur.execute('CREATE DATABASE IF NOT EXISTS stock_data DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
cur.execute('USE stock_data')
cur.execute('DROP TABLE IF EXISTS daily_kline')
cur.execute(create_sql)
insert_sql = 'INSERT INTO daily_kline (' + cols_names + ') VALUES (' + ph + ')'
cur.executemany(insert_sql, data_rows)
conn.commit()
cur.execute('SELECT COUNT(*) FROM daily_kline')
total = cur.fetchone()[0]
print('Done! Total records:', total)
cur.close()
conn.close()
print('Database import complete.')
