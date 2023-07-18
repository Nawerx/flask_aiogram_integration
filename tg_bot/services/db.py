from sqlalchemy import  create_engine, URL

from config import load_config

cfg = load_config()

url = URL.create(
    drivername='postgresql+psycopg2',
    username=cfg.db.user,
    password=cfg.db.password,
    host=cfg.db.host,
    port=cfg.db.port,
    database=cfg.db.database
).render_as_string(hide_password=False)

engine = create_engine(url, echo=False)