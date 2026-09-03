import { DatabaseSync } from 'node:sqlite';
import * as fs from 'fs';
import * as path from 'path';

const DB_DIR = path.join(process.cwd(), 'data');
const DB_PATH = path.join(DB_DIR, 'haven.db');

if (!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });

const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA journal_mode = WAL;');
db.exec(`CREATE TABLE IF NOT EXISTS ideas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL,
  is_completed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  completed_at TEXT
)`);

const stmt = db.prepare('INSERT INTO ideas (content, created_at) VALUES (?, ?)');
stmt.run('test idea', new Date().toISOString());

const rows = db.prepare('SELECT * FROM ideas').all();
console.log('ROWS:', JSON.stringify(rows));
console.log('NODE_SQLITE_OK');
db.close();
