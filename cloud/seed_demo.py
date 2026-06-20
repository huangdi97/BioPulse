import logging
import os

from cloud.seed_data.assistant import seed_device_products, seed_surgery_reminders
from cloud.seed_data.common import _get_conn, seed_hcps, seed_products, seed_users, seed_visits
from cloud.seed_data.research import seed_research_pis, seed_research_products, seed_research_visits

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOUD_DB = os.path.join(BASE_DIR, "data", "cloud.db")
RESEARCH_DB = os.path.join(BASE_DIR, "data", "research.db")
ASSISTANT_DB = os.path.join(BASE_DIR, "data", "assistant.db")


def main() -> None:
    logger.info("→ 通用数据 ...")
    conn = _get_conn(CLOUD_DB)
    try:
        seed_users(conn)
        seed_hcps(conn)
        seed_visits(conn)
        seed_products(conn)
        seed_device_products(conn)
    finally:
        conn.close()

    logger.info("→ 科研模式数据 ...")
    conn = _get_conn(RESEARCH_DB)
    cloud_conn = _get_conn(CLOUD_DB)
    try:
        seed_research_pis(conn)
        seed_research_products(conn)
        seed_research_visits(conn, cloud_conn)
    finally:
        conn.close()
        cloud_conn.close()

    logger.info("→ 跟台助手数据 ...")
    conn = _get_conn(ASSISTANT_DB)
    try:
        seed_surgery_reminders(conn)
    finally:
        conn.close()

    logger.info("种子数据写入完成。")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
