"""Generate the course paper only after the empirical pipeline has completed."""

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]


def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.first_line_indent = Cm(0.75)
    p.paragraph_format.space_after = Pt(7)
    return p


def set_cjk_font(style, family):
    style.font.name = family
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.rFonts
    rfonts.set(qn("w:eastAsia"), family)
    rfonts.set(qn("w:hint"), "eastAsia")


def main():
    parser = argparse.ArgumentParser(description="Build the course paper from verified results")
    parser.add_argument("--course", default="大数据分析")
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--student-name", required=True)
    args = parser.parse_args()
    out = ROOT / "reports" / f"{args.course}-{args.student_id}-{args.student_name}.docx"
    quality = json.loads((ROOT / "reports/data_quality.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "reports/model_metrics.json").read_text(encoding="utf-8"))
    f = quality["ordered_funnel"]
    val = model["validation"]
    test = model["test"]
    winner = model["chosen_by_validation_pr_auc"]
    view_cart = f["view_to_cart"] / f["view"]
    full_path = f["view_cart_to_purchase"] / f["view"]
    cart_purchase = f["view_cart_to_purchase"] / f["view_to_cart"]
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.8)
    normal = doc.styles["Normal"]
    set_cjk_font(normal, "Songti SC")
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.45
    for style_name, size in [("Title", 18), ("Heading 1", 14), ("Heading 2", 12)]:
        style = doc.styles[style_name]
        set_cjk_font(style, "STHeiti")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = None
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("基于机器学习的电商用户转化行为分析与购买意愿预测")
    title_ppr = title._p.get_or_add_pPr()
    border = title_ppr.find(qn("w:pBdr"))
    if border is not None:
        title_ppr.remove(border)
    meta = doc.add_paragraph(f"课程：{args.course}　学号：{args.student_id}　姓名：{args.student_name}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("摘要", 1)
    add_body(doc, f"本文以 RetailRocket 公开的匿名电商行为日志为对象，研究用户从浏览、加购到购买的行为路径，并建立基于历史行为的未来七天购买预测基线。研究保留原始事件文件，利用 DuckDB 和 Python 完成字段校验、完全重复行剔除、访客级有序漏斗统计及分时点特征构建。原始文件包含 {quality['raw_rows']:,} 条记录；清洗后保留 {quality['clean_rows']:,} 条事件、{quality['visitors']:,} 名访客。浏览后加购访客占浏览访客的 {view_cart:.2%}，按序完成浏览、加购、购买的访客占 {full_path:.2%}。预测部分采用历史十四天特征和未来七天标签，按时间设置训练、验证和测试截点；验证集选择的 {winner} 在独立测试集取得 PR-AUC {test['pr_auc']:.4f}，测试集购买基准率为 {test['base_rate']:.2%}。研究结果说明，事件日志能够支持转化路径诊断与购买意愿排序，但无法直接证明运营动作的因果效果，也不能计算广告投放回报。")
    add_body(doc, "关键词：电商用户行为；转化漏斗；购买意愿预测；时间切分；RetailRocket")
    doc.add_heading("目录", 1)
    for line in ["1 研究背景", "2 文献综述", "3 研究框架与方法", "4 数据来源与处理", "5 数据分析与模型结果", "6 讨论与结论", "参考文献"]:
        doc.add_paragraph(line)
    doc.add_heading("1 研究背景", 1)
    add_body(doc, "电商平台持续记录商品浏览、加入购物车与交易等行为。单个事件只表明一次操作，多个事件按访客和时间连接后，才能描述购物路径与后续购买的可能性。对运营人员而言，发现用户在何处停止前进，有助于提出商品发现、购物车提醒和触达优先级等可检验的改进假设。对数据分析工作而言，关键并非只画出事件数量图，而是把业务问题转化为明确的统计单位、时间窗口和评价标准。")
    add_body(doc, "本研究围绕两个问题展开：其一，在可观察的行为日志里，有多少访客依次经历浏览、加购和购买？其二，只利用预测时点以前的行为，能否识别未来七天更可能购买的访客？前一个问题属于描述性分析，后一个问题属于预测性分析。二者相互补充，但不能互相替代；漏斗比例不能当作预测模型性能，预测分数也不能说明某种营销干预必然有效。")
    add_body(doc, "该选题兼顾课程作业与商业分析作品集的要求。一方面，公开数据规模达到百万级，能够展示数据读取、清洗、聚合、可视化和建模的完整过程；另一方面，访客转化与购买倾向是电商运营和效果营销岗位经常讨论的问题。本数据集没有广告曝光、渠道、投放费用或可靠的成交金额，所以研究严格限定在站内行为与交易事件，不将结果解释为点击率、广告归因或投资回报。")
    doc.add_heading("2 文献综述", 1)
    add_body(doc, "RetailRocket 数据集说明指出，原始日志记录了 view、addtocart、transaction 三类行为，用户和商品标识经过匿名处理，商品属性还随时间变化[1]。这意味着事件可用于行为序列研究，但用户人口属性、广告来源和真实价格语义无法从日志中直接恢复。基于原始数据字段定义研究问题，比先假设营销渠道和收入指标更加稳健。")
    add_body(doc, "在二分类任务中，类别分布会显著影响指标解释。Davis 与 Goadrich 对精确率—召回率曲线和 ROC 曲线的关系进行研究，指出当正例稀少时，精确率—召回率视角能更清晰反映模型在关注类别上的表现[2]。本研究以未来购买为正例，除了 ROC-AUC，还报告平均精确率（作为 PR-AUC 的离散估计）及购买基准率，避免只凭一个综合分数判断模型价值。平均精确率的计算采用 scikit-learn 文档定义[3]。")
    add_body(doc, "模型方面，逻辑回归为线性、可解释的基础方法，随机森林通过多棵随机化决策树的组合拟合非线性关系。Breiman 对随机森林的基本结构与泛化性质作出系统论述[4]。本研究使用二者进行基线比较，不通过复杂模型堆叠追求表面高分。商业行动方面，Kohavi 等强调使用受控在线实验评价产品改动[5]；因此，本文提出的运营建议均属于待验证假设，不能从观察性日志中直接宣称增量转化。")
    add_body(doc, "现有电商分析报告常把浏览、加购与购买事件的总次数直接相除，但这些计数单位并不一致：同一访客可能浏览多次、加购多个商品，也可能在已加购商品之外购买其他商品。本研究以访客为基本单位，并对阶段先后顺序提出严格要求。同时，建模使用多组不重叠的预测截点，明确特征窗口与标签窗口的边界，从设计上减少未来信息泄漏。")
    doc.add_heading("3 研究框架与方法", 1)
    doc.add_heading("3.1 研究流程", 2)
    add_body(doc, "研究流程由原始数据核验、事件清洗、描述统计、有序漏斗、用户时点样本构建、模型训练与评估、商业解释七步构成。原始 CSV 留存于 data/raw；DuckDB 执行字段转换、完全重复行去除和日期聚合；Python 负责访问路径与特征计算；模型输出和图表被保存为独立文件，供看板与论文同时读取。这样的文件关系使结果可以从原始数据重建，而不依赖手工修改图表或论文数字。")
    doc.add_heading("3.2 转化漏斗口径", 2)
    add_body(doc, "对每个访客，先确定最早的浏览时间，再查找严格晚于该浏览的第一次加购时间，最后查找严格晚于该加购的交易时间。漏斗的三个阶段分别为至少一次浏览、浏览后至少一次加购，以及浏览—加购—购买均按序发生。另计算浏览后购买访客，不要求其中必须有加购行为。每个阶段按独立访客去重，分母为上一阶段或浏览阶段的访客数。由于没有会话标识，路径允许跨商品与跨访问日，因此它是观察期访客路径，不是单会话或同一商品的成交漏斗。")
    doc.add_heading("3.3 预测任务与时间切分", 2)
    add_body(doc, "每个预测截点只纳入此前十四天至少发生一次事件的访客。历史特征为浏览次数、加购次数、交易次数、不同商品数、活跃天数和距离截点最近一次行为的天数；标签定义为截点起未来七天内是否发生 transaction。特征窗口左闭右开，即截点前十四天至截点前；标签窗口也是左闭右开，即截点至未来第七天前。这一设置使截点当日以后发生的行为只用于标签，不能进入特征。")
    add_body(doc, "训练截点为 2015 年 6 月 1 日、6 月 15 日、7 月 1 日和 7 月 15 日；验证截点为 8 月 1 日；测试截点为 8 月 15 日，均按 UTC 解释。每个截点间隔大于七天，标签区间不重叠。模型先在训练样本拟合，再以验证集 PR-AUC 选择模型，最后仅对测试集计算一次指标。相同访客可能在不同截点进入样本，但每条样本的特征与标签在时间上分离；这一限制在解释模型泛化能力时需要保留。")
    add_body(doc, "在模型比较中，逻辑回归先对输入特征进行标准化，并使用类别权重缓解正负例不平衡；随机森林固定随机种子和树的深度、叶节点最小样本数，也使用类别权重。评价包含平均精确率、ROC-AUC、0.5 阈值下的精确率与召回率，以及模型分数最高的前十分之一访客的实际购买率及其相对总体基准率的倍数。前十分之一只衡量排序集中度，不表示向这些访客投放广告后会增加多少购买。")
    doc.add_heading("4 数据来源与处理", 1)
    add_body(doc, f"原始数据源为 RetailRocket 推荐系统公开数据集[1]。本项目使用其中的 events.csv 文件，并记录其 SHA-256 校验值为 {quality['raw_sha256']}。文件包括毫秒级 Unix 时间戳、visitorid、event、itemid 和 transactionid 五列。完整原始文件实际读取 {quality['raw_rows']:,} 行，清洗后剩余 {quality['clean_rows']:,} 行；剔除或合并 {quality['removed_rows']:,} 行。清洗过程验证时间戳、访客标识和商品标识可解析，事件属于三种已知类型，并按五个原始字段完全一致去重。非交易行为中 transactionid 留空是数据定义的一部分，不作为无效记录删除。")
    add_body(doc, f"清洗后的日志覆盖 {quality['first_utc']} 至 {quality['last_utc']}（UTC），包含 {quality['visitors']:,} 名独立访客、{quality['items']:,} 个有记录的商品。三类事件分别为浏览 {quality['clean_event_counts'].get('view', 0):,} 条、加购 {quality['clean_event_counts'].get('addtocart', 0):,} 条、交易 {quality['clean_event_counts'].get('transaction', 0):,} 条。商品属性文件未纳入本轮建模，原因是其属性值多数匿名且具有时间变化；若未经时间回溯直接拼接最新商品信息，可能把未来属性泄漏到过去样本。")
    add_body(doc, "在数据质量方面，本研究分别报告原始与清洗后记录数、独立访客数、商品数和日期边界，并以每日事件量检查时间分布。清洗没有根据某个预期结果强行删除高频访客，也没有把购买者特征与非购买者特征在全观察期聚合，因为这样的处理会把预测时点后的活动混入历史信息。原始文件、清洗脚本与输出报告共同构成可审查的证据链。")
    doc.add_heading("5 数据分析与模型结果", 1)
    doc.add_heading("5.1 事件分布和访客路径", 2)
    add_body(doc, "按 UTC 日期汇总的三类事件量见图 1。浏览事件在整个观察期内始终占多数，加购与交易事件量明显较少。三条曲线均有日际起伏，但仅凭此图不能判断波动由星期、促销或流量渠道造成。观察期最后一个 UTC 日期只覆盖至约 02:59，末端的明显下降主要受不完整日期影响，不应当解读为业务突然恶化。纵轴采用对数刻度，便于在同一图上比较量级差异；图中曲线是事件次数，不是独立访客转化率。")
    daily_fig = ROOT / "figures/daily_events.png"
    if daily_fig.exists():
        doc.add_picture(str(daily_fig), width=Cm(14))
        caption = doc.add_paragraph("图 1　按 UTC 日期统计的浏览、加购与交易事件量（对数纵轴）")
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_body(doc, f"在访客级有序漏斗中，至少发生一次浏览的访客为 {f['view']:,} 人；浏览后发生加购的访客为 {f['view_to_cart']:,} 人，占浏览访客的 {view_cart:.2%}。在此前提下继续完成购买的访客为 {f['view_cart_to_purchase']:,} 人，占浏览访客的 {full_path:.2%}，占浏览后加购访客的 {cart_purchase:.2%}。另有 {f['view_to_purchase_any']:,} 名访客在浏览后发生购买，这一数值不要求加购阶段。不同指标回答的问题不同，不能把事件次数与独立访客数交叉相除。")
    add_body(doc, "漏斗显示大量浏览访客未进入可观察的加购阶段，但不能直接归因为商品详情页问题：访客可能只是查看信息，也可能在数据观察期外完成购买，或者从不同设备访问而被记为不同匿名标识。加购到购买的路径同样可能受库存、配送、价格感知和结算流程影响，而数据中缺少足以区分这些原因的字段。因此，本研究将路径差异当作需要进一步调研和实验的线索。")
    fig = ROOT / "figures/ordered_funnel.png"
    if fig.exists():
        doc.add_picture(str(fig), width=Cm(14))
        caption = doc.add_paragraph("图 2　按事件顺序统计的访客转化路径")
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading("5.2 购买意愿预测", 2)
    add_body(doc, f"训练集共 {model['split_sizes']['train']:,} 条时点样本，验证集 {model['split_sizes']['validation']:,} 条，测试集 {model['split_sizes']['test']:,} 条。验证集逻辑回归的 PR-AUC 为 {val['logistic_regression']['pr_auc']:.4f}，随机森林为 {val['random_forest']['pr_auc']:.4f}。按事先规定的验证集指标，选定 {winner}。独立测试集包含 {test['buyers']:,} 个正例，购买基准率 {test['base_rate']:.2%}；选定模型的 PR-AUC 为 {test['pr_auc']:.4f}，ROC-AUC 为 {test['roc_auc']:.4f}。这些数字只来自已运行的程序输出。")
    add_body(doc, f"在固定 0.5 阈值下，测试集召回率为 {test['recall_at_0_5']:.2%}，精确率为 {test['precision_at_0_5']:.2%}。模型分数最高的前 10% 样本实际购买率为 {test['top_decile_precision']:.2%}，是测试集总体购买率的 {test['top_decile_lift']:.2f} 倍。类别权重可能改变模型分数的校准性质，因此 0.5 阈值并非业务最优阈值；真正上线前应结合触达成本、用户体验和可承受的误报量选定阈值。模型也没有在真实营销活动中做在线检验，不能把前十位百分比解释为真实投放收益。")
    doc.add_heading("5.3 运营解释", 2)
    add_body(doc, "从分析流程可以提出两类下一步实验。其一，针对浏览后没有加购的访客，设计商品信息呈现或相关商品推荐的 A/B 测试，观察加购率、购买率及负面体验指标是否同步变化。其二，对历史行为显示更高购买倾向的访客尝试有限频次的触达，并随机留出对照组，比较真实增量购买而非仅比较自然购买率。实验应预先定义分流单位、观察期和成功指标，避免事后挑选有利结果。")
    add_body(doc, "如果运营资源有限，模型排序可帮助确定首先观察哪些访客，但高购买概率者本来也可能自然成交。把资源全部投向高分群体，可能浪费触达成本，也可能忽略低分却更易受干预影响的人。未来若能获得渠道、优惠、曝光和成本数据，可以将购买倾向预测与增量响应估计区分开来，进一步评价真实商业价值。本研究现有字段只支持前者。")
    doc.add_heading("6 讨论与结论", 1)
    add_body(doc, f"本文在保留原始文件的基础上，完成了 {quality['raw_rows']:,} 条 RetailRocket 行为记录的读取和核验，建立了可重现的 SQL 与 Python 处理流程。访客级有序漏斗明确区分事件数与独立访客数，并验证浏览、加购、购买的先后顺序。预测任务使用固定的十四天历史和七天未来窗口，通过时间分离的训练、验证与测试截点比较两种基线模型。测试集的 PR-AUC 为 {test['pr_auc']:.4f}，应与 {test['base_rate']:.2%} 的购买基准率一起解读。")
    add_body(doc, f"研究的主要贡献是口径清楚、过程可复现和边界明确。它将运营问题拆解为描述性路径与预测性排序，展示了如何防止未来行为进入特征，并通过独立测试集约束结果选择。然而，测试集只有 {test['buyers']:,} 个购买正例，指标可能对少量样本的排序变化敏感；匿名访客也不一定等同于自然人。行为路径允许跨会话、跨商品，样本时间处于 2015 年，商品属性、库存和真实价格尚未进入分析。这些条件限制了结论的外推范围，也使某些流失原因无法被识别。")
    add_body(doc, "后续可在保持时间因果顺序的前提下，增加按商品及会话划分的漏斗，使用商品属性的历史快照构造更细的特征，并进行模型概率校准与不同时间段稳定性检查。如果能获取合规的触达和成本记录，应通过随机对照实验评估干预增量。课程提交包含论文 Word、原始数据及完整程序；作品集提供 README、SQL、图表和本地交互看板，便于审阅者逐步核对研究结论。")
    doc.add_heading("参考文献", 1)
    refs = [
        "[1] Zykov R. Retailrocket recommender system dataset. Kaggle. https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset",
        "[2] Davis J, Goadrich M. The Relationship Between Precision-Recall and ROC Curves. Proceedings of ICML, 2006. https://mlanthology.org/icml/2006/davis2006icml-relationship/",
        "[3] scikit-learn developers. average_precision_score documentation. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html",
        "[4] Breiman L. Random Forests. Machine Learning, 45: 5–32, 2001. https://doi.org/10.1023/A:1010933404324",
        "[5] Kohavi R, Henne R M, Sommerfield D. Practical Guide to Controlled Experiments on the Web. KDD, 2007. https://ai.stanford.edu/~ronnyk/2007GuideControlledExperiments.pdf",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(3)
        for run in p.runs:
            run.font.size = Pt(9)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(f"{args.student_name} · {args.course}")
    out.parent.mkdir(exist_ok=True)
    doc.save(out)
    print(out)
    print("body_chars", sum(len(p.text) for p in doc.paragraphs))


if __name__ == "__main__":
    main()
