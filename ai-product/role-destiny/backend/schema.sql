-- ========================================
-- 角色测算小程序 V1.0 - SQLite数据库建表脚本
-- ========================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  openid TEXT NOT NULL UNIQUE,
  unionid TEXT,
  nickname TEXT,
  avatar TEXT,
  phone TEXT,
  status INTEGER DEFAULT 1 CHECK(status IN (0, 1)),
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_users_unionid ON users(unionid);

-- 测试主题表
CREATE TABLE IF NOT EXISTS tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  cover_image TEXT,
  share_title TEXT,
  share_desc TEXT,
  price REAL DEFAULT 0.99,
  status INTEGER DEFAULT 1 CHECK(status IN (0, 1)),
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 题目表
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (test_id) REFERENCES tests(id)
);

CREATE INDEX IF NOT EXISTS idx_questions_test_id ON questions(test_id);

-- 选项表
CREATE TABLE IF NOT EXISTS options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  score_map TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE INDEX IF NOT EXISTS idx_options_question_id ON options(question_id);

-- 角色原型表
CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  test_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  code TEXT NOT NULL,
  description TEXT,
  image TEXT,
  detail_text TEXT,
  personality TEXT,
  destiny TEXT,
  advantages TEXT,
  weaknesses TEXT,
  suggestion TEXT,
  lucky_number TEXT,
  lucky_color TEXT,
  motto TEXT,
  rarity REAL,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (test_id) REFERENCES tests(id)
);

CREATE INDEX IF NOT EXISTS idx_roles_test_id ON roles(test_id);

-- 用户测试记录表
CREATE TABLE IF NOT EXISTS user_tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  test_id INTEGER NOT NULL,
  answers TEXT NOT NULL,
  result_role_id INTEGER,
  match_score REAL,
  is_paid INTEGER DEFAULT 0 CHECK(is_paid IN (0, 1)),
  paid_at TEXT,
  status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'expired')),
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (test_id) REFERENCES tests(id),
  FOREIGN KEY (result_role_id) REFERENCES roles(id)
);

CREATE INDEX IF NOT EXISTS idx_user_tests_user_id ON user_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tests_test_id ON user_tests(test_id);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_no TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  result_id INTEGER NOT NULL,
  test_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'refunded', 'failed')),
  transaction_id TEXT,
  pay_time TEXT,
  expire_time TEXT,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  updated_at TEXT DEFAULT (datetime('now', 'localtime')),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (result_id) REFERENCES user_tests(id),
  FOREIGN KEY (test_id) REFERENCES tests(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_transaction_id ON orders(transaction_id);
