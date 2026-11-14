"""Local Streamlit dashboard for verified pipeline outputs."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

st.set_page_config(page_title="电商转化分析", page_icon="🛒", layout="wide")
st.title("电商用户行为与转化预测")
st.caption("RetailRocket 公开匿名行为日志 · 时间序列验证 · 2015 年数据")

quality_file = REPORTS / "data_quality.json"
model_file = REPORTS / "model_metrics.json"
if not (quality_file.exists() and model_file.exists()):
    st.info("请先在项目目录运行 `python -m src.run_pipeline`，看板将读取实际分析结果。")
    st.stop()

quality = json.loads(quality_file.read_text(encoding="utf-8"))
model = json.loads(model_file.read_text(encoding="utf-8"))
funnel = quality["ordered_funnel"]

overview, path, prediction, caveats = st.tabs(["数据概览", "转化路径", "购买预测", "研究边界"])
with overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("清洗后事件", f"{quality['clean_rows']:,}")
    c2.metric("独立访客", f"{quality['visitors']:,}")
    c3.metric("商品数", f"{quality['items']:,}")
    c4.metric("去除或无效行", f"{quality['removed_rows']:,}")
    st.write(f"时间范围（UTC）：{quality['first_utc']} 至 {quality['last_utc']}")
    counts = pd.Series(quality["clean_event_counts"], name="事件数")
    st.bar_chart(counts)
    daily = pd.read_csv(REPORTS / "daily_events.csv", parse_dates=["event_date"])
    kinds = st.multiselect("选择事件类型", sorted(daily.event.unique()), default=sorted(daily.event.unique()))
    subset = daily[daily.event.isin(kinds)].pivot(index="event_date", columns="event", values="events").fillna(0)
    st.line_chart(subset)
with path:
    stages = pd.DataFrame({
        "阶段": ["至少一次浏览", "浏览后加购", "浏览→加购→购买"],
        "访客": [funnel["view"], funnel["view_to_cart"], funnel["view_cart_to_purchase"]],
    }).set_index("阶段")
    st.bar_chart(stages)
    st.metric("浏览后购买（不限加购）", f"{funnel['view_to_purchase_any']:,}")
    st.write(f"浏览后加购访客占浏览访客：{funnel['view_to_cart'] / funnel['view']:.2%}")
    st.write(f"按序购买访客占浏览访客：{funnel['view_cart_to_purchase'] / funnel['view']:.2%}")
    st.caption(quality["funnel_definition"])
with prediction:
    st.write("14 天历史特征预测未来 7 天购买。根据验证集 PR-AUC 选择模型后，只对测试集评估一次。")
    st.dataframe(pd.DataFrame(model["validation"]).T)
    st.write(f"验证集选定模型：**{model['chosen_by_validation_pr_auc']}**")
    test = model["test"]
    a, b, c, d = st.columns(4)
    a.metric("测试集购买基准率", f"{test['base_rate']:.2%}")
    b.metric("测试集 PR-AUC", f"{test['pr_auc']:.4f}")
    c.metric("前 10% 购买率", f"{test['top_decile_precision']:.2%}")
    d.metric("前 10% 相对提升倍数", f"{test['top_decile_lift']:.2f}×" if test['top_decile_lift'] else "—")
    st.caption("前 10% 指模型分数最高的十分之一访客；这不是干预后的增量效果。")
with caveats:
    st.markdown("""
    - 漏斗按访客跨商品、跨会话统计，不能视作单次会话转化率。
    - 日志未包含广告曝光、渠道成本或真实成交金额，不能估计 CTR、ROAS 或广告归因。
    - 模型用于购买意愿排序，不证明触达用户会提高购买率；运营建议需用 A/B 测试检验。
    - 数据来自 2015 年的匿名电商站点，不能直接代表当前中国市场。
    """)
    st.code(f"原始 events.csv SHA-256: {quality['raw_sha256']}")
