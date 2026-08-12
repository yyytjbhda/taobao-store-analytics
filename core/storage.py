"""Data storage and loading for the Taobao Store Analytics Workbench."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USER_DIR = DATA_DIR / "user"
DEMO_DIR = DATA_DIR / "demo"
TEMPLATE_DIR = DATA_DIR / "templates"

MODE_DEMO = "demo"
MODE_USER = "user"

ORDER_COLUMNS = [
    "订单号", "成交时间", "商品ID", "商品名称", "数量", "单价",
    "实付金额", "运费", "优惠金额", "买家ID", "退款状态", "订单状态", "备注",
]
PRODUCT_COLUMNS = [
    "商品ID", "商品名称", "类目", "SKU", "成本价", "销售价",
    "库存数量", "库存预警阈值", "上架状态",
]
MARKETING_COLUMNS = ["日期", "渠道", "花费", "成交金额", "备注"]

ORDER_FILE = "orders.csv"
PRODUCT_FILE = "products.csv"
MARKETING_FILE = "marketing.csv"
SOP_FLOWS_FILE = "sop_flows.json"
SOP_TEMPLATES_FILE = "sop_templates.json"

NUMERIC_COLS = {
    "数量", "单价", "实付金额", "运费", "优惠金额", "花费", "成交金额",
    "成本价", "销售价", "库存数量", "库存预警阈值",
}

DEFAULT_SOP_TEMPLATE = {
    "name": "标准运营流程",
    "steps": [
        "市场与选品调研",
        "供应商对接",
        "上架准备（标题/主图/详情）",
        "上架",
        "推广计划",
        "活动报名",
        "发货与售后",
        "数据复盘",
        "迭代优化",
    ],
}


def _data_dir(mode: str) -> Path:
    return DEMO_DIR if mode == MODE_DEMO else USER_DIR


def _dir_writable(d: Path) -> bool:
    """True when we can write to the directory (cloud deploys are read-only)."""
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".write_probe"
        probe.write_text("1", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _mem_store() -> dict:
    """Session-scoped fallback storage for read-only (cloud) environments."""
    if "_mem_data" not in st.session_state:
        st.session_state["_mem_data"] = {}
    return st.session_state["_mem_data"]


def _is_cloud_readonly() -> bool:
    return not _dir_writable(USER_DIR)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError, UnicodeDecodeError):
        return pd.DataFrame()
    return _coerce_dtypes(df)


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric and date columns to proper dtypes."""
    if df.empty:
        return df
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for date_col in ("成交时间", "日期"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _load_csv_or_mem(path: Path, key: str) -> pd.DataFrame:
    df = _read_csv(path)
    if df.empty and key in _mem_store():
        df = _mem_store()[key]
    return df


def load_orders(mode: str = MODE_USER) -> pd.DataFrame:
    return _load_csv_or_mem(_data_dir(mode) / ORDER_FILE, ORDER_FILE)


def save_orders(df: pd.DataFrame, mode: str = MODE_USER) -> None:
    if _dir_writable(_data_dir(mode)):
        _write_csv(df, _data_dir(mode) / ORDER_FILE)
    else:
        _mem_store()[ORDER_FILE] = df.copy()


def load_products(mode: str = MODE_USER) -> pd.DataFrame:
    return _load_csv_or_mem(_data_dir(mode) / PRODUCT_FILE, PRODUCT_FILE)


def save_products(df: pd.DataFrame, mode: str = MODE_USER) -> None:
    if _dir_writable(_data_dir(mode)):
        _write_csv(df, _data_dir(mode) / PRODUCT_FILE)
    else:
        _mem_store()[PRODUCT_FILE] = df.copy()


def load_marketing(mode: str = MODE_USER) -> pd.DataFrame:
    return _load_csv_or_mem(_data_dir(mode) / MARKETING_FILE, MARKETING_FILE)


def save_marketing(df: pd.DataFrame, mode: str = MODE_USER) -> None:
    if _dir_writable(_data_dir(mode)):
        _write_csv(df, _data_dir(mode) / MARKETING_FILE)
    else:
        _mem_store()[MARKETING_FILE] = df.copy()


def _load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return _mem_store().get(str(path), default)


def _save_json(obj, path: Path) -> None:
    if _dir_writable(path.parent):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    else:
        _mem_store()[str(path)] = obj


def load_sop_flows(mode: str = MODE_USER) -> list:
    return _load_json(_data_dir(mode) / SOP_FLOWS_FILE, [])


def save_sop_flows(flows: list, mode: str = MODE_USER) -> None:
    _save_json(flows, _data_dir(mode) / SOP_FLOWS_FILE)


def load_sop_templates(mode: str = MODE_USER) -> dict:
    templates = _load_json(_data_dir(mode) / SOP_TEMPLATES_FILE, {})
    if "default" not in templates:
        templates["default"] = DEFAULT_SOP_TEMPLATE
    return templates


def save_sop_templates(templates: dict, mode: str = MODE_USER) -> None:
    _save_json(templates, _data_dir(mode) / SOP_TEMPLATES_FILE)


def _normalize_refund(df: pd.DataFrame) -> pd.DataFrame:
    """Map refund column values to 已退款 / 未退款."""
    df = df.copy()
    refund_values = {"已退款", "是", "退款", "TRUE", "True", "1", "yes"}
    df["退款状态"] = df["退款状态"].astype(str).map(
        lambda v: "已退款" if v.strip() in refund_values else "未退款"
    )
    return df


def _validate_excel(uploaded_file, columns: list[str]) -> tuple[pd.DataFrame, list[str]]:
    try:
        df = pd.read_excel(uploaded_file, dtype=str, keep_default_na=False)
    except Exception as e:  # noqa: BLE001
        return pd.DataFrame(), [f"无法读取文件：{e}"]
    missing = [c for c in columns if c not in df.columns]
    if missing:
        return pd.DataFrame(), [f"缺少必需列：{'、'.join(missing)}。请使用模板文件。"]
    return df[columns], []


def import_orders_excel(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """Validate an uploaded order Excel. Returns (df, errors)."""
    df, errors = _validate_excel(uploaded_file, ORDER_COLUMNS)
    if errors:
        return df, errors

    required = ["订单号", "成交时间", "商品ID", "商品名称", "数量", "实付金额"]
    for col in required:
        if df[col].astype(str).str.strip().eq("").any():
            bad_rows = df.index[df[col].astype(str).str.strip().eq("")].tolist()
            errors.append(f"第 {', '.join(str(i + 2) for i in bad_rows[:5])} 行缺少「{col}」")

    numeric_cols = ["数量", "单价", "实付金额", "运费", "优惠金额"]
    for col in numeric_cols:
        converted = pd.to_numeric(df[col], errors="coerce")
        bad = df.index[converted.isna() & df[col].astype(str).str.strip().ne("")]
        for i in bad[:5]:
            errors.append(f"第 {i + 2} 行「{col}」不是有效数字：{df.loc[i, col]}")

    if errors:
        return pd.DataFrame(), errors[:20]

    df = _coerce_dtypes(df)
    df = _normalize_refund(df)
    df["备注"] = df["备注"].fillna("")
    return df, []


def import_products_excel(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """Validate an uploaded product Excel. Returns (df, errors)."""
    df, errors = _validate_excel(uploaded_file, PRODUCT_COLUMNS)
    if errors:
        return df, errors

    required = ["商品ID", "商品名称", "成本价", "销售价"]
    for col in required:
        if df[col].astype(str).str.strip().eq("").any():
            bad_rows = df.index[df[col].astype(str).str.strip().eq("")].tolist()
            errors.append(f"第 {', '.join(str(i + 2) for i in bad_rows[:5])} 行缺少「{col}」")

    numeric_cols = ["成本价", "销售价", "库存数量", "库存预警阈值"]
    for col in numeric_cols:
        converted = pd.to_numeric(df[col], errors="coerce")
        bad = df.index[converted.isna() & df[col].astype(str).str.strip().ne("")]
        for i in bad[:5]:
            errors.append(f"第 {i + 2} 行「{col}」不是有效数字：{df.loc[i, col]}")

    if errors:
        return pd.DataFrame(), errors[:20]

    df = _coerce_dtypes(df)
    df = df.fillna({"库存数量": 0, "库存预警阈值": 0})
    return df, []


def import_marketing_excel(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """Validate an uploaded marketing Excel. Returns (df, errors)."""
    df, errors = _validate_excel(uploaded_file, MARKETING_COLUMNS)
    if errors:
        return df, errors

    required = ["日期", "渠道", "花费"]
    for col in required:
        if df[col].astype(str).str.strip().eq("").any():
            bad_rows = df.index[df[col].astype(str).str.strip().eq("")].tolist()
            errors.append(f"第 {', '.join(str(i + 2) for i in bad_rows[:5])} 行缺少「{col}」")

    for col in ["花费", "成交金额"]:
        converted = pd.to_numeric(df[col], errors="coerce")
        bad = df.index[converted.isna() & df[col].astype(str).str.strip().ne("")]
        for i in bad[:5]:
            errors.append(f"第 {i + 2} 行「{col}」不是有效数字：{df.loc[i, col]}")

    if errors:
        return pd.DataFrame(), errors[:20]

    df = _coerce_dtypes(df)
    df = df.fillna({"成交金额": 0})
    df["备注"] = df["备注"].fillna("")
    return df, []


def _template_bytes(columns: list[str], example_row: dict, sheet_name: str) -> bytes:
    df = pd.DataFrame(columns=columns)
    if example_row:
        df = pd.concat([df, pd.DataFrame([example_row])], ignore_index=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def make_order_template_bytes() -> bytes:
    return _template_bytes(
        ORDER_COLUMNS,
        {
            "订单号": "202601010001", "成交时间": "2026-01-01 10:30:00",
            "商品ID": "P001", "商品名称": "示例商品A", "数量": 2,
            "单价": 59.9, "实付金额": 119.8, "运费": 0, "优惠金额": 0,
            "买家ID": "U00001", "退款状态": "未退款", "订单状态": "已完成",
            "备注": "示例行，可删除",
        },
        "订单",
    )


def make_product_template_bytes() -> bytes:
    return _template_bytes(
        PRODUCT_COLUMNS,
        {
            "商品ID": "P001", "商品名称": "示例商品A", "类目": "服饰",
            "SKU": "A-白色-M", "成本价": 25.0, "销售价": 59.9,
            "库存数量": 100, "库存预警阈值": 20, "上架状态": "上架",
        },
        "商品",
    )


def make_marketing_template_bytes() -> bytes:
    return _template_bytes(
        MARKETING_COLUMNS,
        {
            "日期": "2026-01-01", "渠道": "直通车", "花费": 200.0,
            "成交金额": 800.0, "备注": "示例行，可删除",
        },
        "营销",
    )
