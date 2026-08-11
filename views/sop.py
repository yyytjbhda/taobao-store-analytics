"""SOP 流程管理：选品→上架→推广→复盘 标准流程跟进。"""

import datetime as dt

import pandas as pd
import streamlit as st

from core import storage, ui

STATUS_OPTIONS = ["未开始", "进行中", "已完成"]


def flow_progress(flow: dict) -> tuple[int, int]:
    steps = flow["steps"]
    done = sum(1 for s in steps if s["status"] == "已完成")
    return done, len(steps)


def overview() -> None:
    st.subheader("流程总览")
    flows = storage.load_sop_flows(storage.MODE_USER)
    if not flows:
        st.info("暂无流程，可在「创建新流程」开始第一条。")
        return
    rows = []
    for f in flows:
        done, total = flow_progress(f)
        rows.append({
            "流程ID": f["flow_id"],
            "商品": f.get("product_name", ""),
            "模板": f.get("template_name", ""),
            "进度": f"{done}/{total}",
            "创建时间": f.get("created_at", ""),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def create_flow() -> None:
    with st.expander("＋ 创建新流程", expanded=True):
        products = storage.load_products(storage.MODE_USER)
        if products.empty:
            st.caption("暂无商品数据：可在「商品管理」导入后创建，也可直接填写商品名称。")
            product_name = st.text_input("商品名称 *")
            product_id = st.text_input("商品ID（选填）")
        else:
            options = [f"{r['商品ID']}｜{r['商品名称']}" for _, r in products.iterrows()]
            choice = st.selectbox("选择商品", options)
            product_id, product_name = choice.split("｜", 1)
        templates = storage.load_sop_templates(storage.MODE_USER)
        tpl_key = st.selectbox(
            "选择流程模板",
            list(templates.keys()),
            format_func=lambda k: templates[k].get("name", k),
        )
        if st.button("创建流程"):
            if not product_name.strip():
                st.error("请填写商品名称。")
            else:
                flows = storage.load_sop_flows(storage.MODE_USER)
                fid = f"F-{dt.datetime.now():%Y%m%d%H%M%S}"
                steps = [
                    {"name": n, "status": "未开始", "owner": "", "date": "", "note": ""}
                    for n in templates[tpl_key]["steps"]
                ]
                flows.append({
                    "flow_id": fid,
                    "product_id": product_id,
                    "product_name": product_name,
                    "template_name": templates[tpl_key].get("name", tpl_key),
                    "steps": steps,
                    "created_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                storage.save_sop_flows(flows, storage.MODE_USER)
                st.success("流程已创建。")
                st.rerun()


def flow_detail() -> None:
    flows = storage.load_sop_flows(storage.MODE_USER)
    if not flows:
        return
    st.subheader("流程跟进")
    fid = st.selectbox("选择流程", [f["flow_id"] for f in flows])
    flow = next(f for f in flows if f["flow_id"] == fid)
    done, total = flow_progress(flow)
    st.progress(done / total if total else 0)
    st.caption(f"商品：{flow['product_name']}（{flow['product_id']}）｜模板：{flow['template_name']}｜进度 {done}/{total}")

    with st.form(f"flow_form_{fid}"):
        for i, step in enumerate(flow["steps"]):
            c1, c2, c3, c4 = st.columns([2.2, 1, 1.2, 2.5])
            c1.markdown(f"**{step['name']}**")
            step["status"] = c2.selectbox(
                "状态", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(step["status"]),
                key=f"st_{fid}_{i}",
            )
            step["owner"] = c3.text_input("负责人", value=step["owner"], key=f"ow_{fid}_{i}")
            step["note"] = c4.text_input("备注", value=step["note"], key=f"no_{fid}_{i}")
        if st.form_submit_button("保存进度"):
            storage.save_sop_flows(flows, storage.MODE_USER)
            st.success("进度已保存。")
            st.rerun()


def delete_flow() -> None:
    flows = storage.load_sop_flows(storage.MODE_USER)
    if not flows:
        return
    with st.expander("🗑️ 删除流程"):
        fid = st.selectbox("选择要删除的流程", [f["flow_id"] for f in flows], key="del_flow_select")
        if st.button("删除", key="del_flow_btn"):
            flows = [f for f in flows if f["flow_id"] != fid]
            storage.save_sop_flows(flows, storage.MODE_USER)
            st.success("已删除。")
            st.rerun()


def template_manager() -> None:
    with st.expander("模板管理（自定义流程步骤）", expanded=False):
        templates = storage.load_sop_templates(storage.MODE_USER)
        tpl_key = st.selectbox(
            "选择模板", list(templates.keys()),
            format_func=lambda k: templates[k].get("name", k),
            key="tpl_select",
        )
        current = templates[tpl_key]
        steps_text = st.text_area(
            "流程步骤（每行一步）", value="\n".join(current["steps"]), key="tpl_steps"
        )
        if st.button("保存模板修改", key="save_tpl"):
            steps = [s.strip() for s in steps_text.splitlines() if s.strip()]
            templates[tpl_key]["steps"] = steps
            storage.save_sop_templates(templates, storage.MODE_USER)
            st.success("模板已更新。")
            st.rerun()
        st.divider()
        new_name = st.text_input("新模板名称", key="new_tpl_name")
        new_steps = st.text_area("新模板步骤（每行一步）", key="new_tpl_steps")
        if st.button("创建新模板", key="create_tpl"):
            steps = [s.strip() for s in new_steps.splitlines() if s.strip()]
            if not (new_name.strip() and steps):
                st.error("请填写模板名称和至少一个步骤。")
            else:
                key = f"custom_{dt.datetime.now():%Y%m%d%H%M%S}"
                templates[key] = {"name": new_name.strip(), "steps": steps}
                storage.save_sop_templates(templates, storage.MODE_USER)
                st.success("新模板已创建。")
                st.rerun()
        if tpl_key != "default" and st.button("删除当前模板", key="del_tpl"):
            templates.pop(tpl_key)
            storage.save_sop_templates(templates, storage.MODE_USER)
            st.success("已删除。")
            st.rerun()


mode, _, _ = ui.load_data()
st.title("✅ SOP 流程管理")
st.caption("电商运营标准流程：选品 → 供应商 → 上架准备 → 上架 → 推广 → 活动 → 发货售后 → 复盘 → 迭代")
overview()
create_flow()
flow_detail()
delete_flow()
template_manager()

