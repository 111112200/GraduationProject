"""
迁移脚本：将 report 表的 experiment_id 列从 NOT NULL 改为 NULLABLE。

SQLite 不支持 ALTER COLUMN，所以需要：
1. 关闭外键约束
2. 重命名旧表
3. 用新 schema 创建新表
4. 复制数据
5. 删除旧表
6. 重建外键约束
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"


def migrate():
    if not DB_PATH.exists():
        print(f"数据库文件不存在: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 检查当前 schema
    c.execute("PRAGMA table_info(report)")
    columns = c.fetchall()
    exp_col = [col for col in columns if col[1] == "experiment_id"]
    if not exp_col:
        print("未找到 experiment_id 列，跳过迁移")
        return
    
    is_notnull = exp_col[0][3]  # notnull flag
    if not is_notnull:
        print("experiment_id 已经是 NULLABLE，无需迁移")
        return

    print(f"当前 experiment_id notnull={is_notnull}，开始迁移...")

    # 备份数据量
    c.execute("SELECT COUNT(*) FROM report")
    count = c.fetchone()[0]
    print(f"report 表共 {count} 条记录")

    try:
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("BEGIN TRANSACTION")

        # 1. 重命名旧表
        c.execute("ALTER TABLE report RENAME TO report_old")

        # 2. 创建新表 (experiment_id 允许 NULL)
        c.execute("""
            CREATE TABLE report (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                class_id INTEGER NOT NULL,
                student_name VARCHAR(64),
                student_id VARCHAR(64),
                file_name VARCHAR(256),
                file_path VARCHAR(512) NOT NULL,
                status VARCHAR(32),
                parse_error TEXT,
                parsed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(experiment_id) REFERENCES experiment(id),
                FOREIGN KEY(class_id) REFERENCES clazz(id)
            )
        """)

        # 3. 复制数据
        c.execute("""
            INSERT INTO report (id, experiment_id, class_id, student_name, student_id,
                                file_name, file_path, status, parse_error, parsed_at,
                                created_at, updated_at)
            SELECT id, experiment_id, class_id, student_name, student_id,
                   file_name, file_path, status, parse_error, parsed_at,
                   created_at, updated_at
            FROM report_old
        """)

        # 4. 删除旧表
        c.execute("DROP TABLE report_old")

        conn.commit()
        c.execute("PRAGMA foreign_keys=ON")

        # 验证
        c.execute("PRAGMA table_info(report)")
        columns = c.fetchall()
        exp_col = [col for col in columns if col[1] == "experiment_id"]
        print(f"迁移完成！experiment_id notnull={exp_col[0][3]}")

        c.execute("SELECT COUNT(*) FROM report")
        new_count = c.fetchone()[0]
        print(f"迁移后 report 表共 {new_count} 条记录 (迁移前 {count} 条)")

        if new_count != count:
            print("⚠️ 警告：数据量不一致！")
        else:
            print("✅ 数据完整性验证通过")

    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败，已回滚: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
