# 电商用户行为与转化预测 | Ecommerce Conversion Analytics

一个可复现的 RetailRocket 行为日志分析项目，面向电商转化运营与数据分析岗位作品集，同时支持大数据分析课程论文。研究对象是匿名访客的浏览、加购与交易事件；**没有广告曝光、投放成本或销售金额字段，因此不报告 CTR、ROAS、广告归因或收入提升。**

## 数据

- 原始来源：[RetailRocket recommender system dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset)，作者 Roman Zykov，许可标注为 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。
- 本地分析所用事件文件从[公开共享镜像](https://drive.google.com/drive/u/0/folders/1yh3_M87wm_bWxC5ufVez9eR4WdtgI89R)获取，SHA-256 为 `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`，与[另一处镜像](https://huggingface.co/datasets/DanielKiani/RetailRocket-Recommender-Data/tree/main/data/RetailRocket-Recommender-Data/data)的文件校验值一致。运行时记录原始行数及清洗行数，避免把网页介绍中的数值当成实测结果。
- `data/raw/events.csv` 保留原文件。商品属性文件很大，第一版仅分析事件数据；未使用未知含义的匿名属性代码。

## 已核验的第一版结果

| 指标 | 实测值 |
|---|---:|
| 原始事件 / 清洗后事件 | 2,756,101 / 2,755,641 |
| 独立访客 / 有事件商品 | 1,407,580 / 235,061 |
| 浏览访客 / 浏览后加购访客 / 按序购买访客 | 1,404,179 / 32,934 / 9,952 |
| 浏览后加购访客占比 / 完整路径访客占比 | 2.35% / 0.71% |
| 测试集样本 / 购买正例 | 146,204 / 75 |
| 测试集购买基准率 / PR-AUC | 0.0513% / 0.1328 |
| 模型前 10% 访客购买率 / 相对基准倍数 | 0.3215% / 6.27 倍 |

完整数值见 `reports/data_quality.json` 与 `reports/model_metrics.json`。测试集正例只有 75 个，模型指标对少量样本排序变化可能敏感；结果用于教学和作品展示，不代表稳定的线上收益。

## 研究口径

1. 清洗：校验时间、访客、商品和事件类型，按所有原始字段去除完全重复行。非交易事件的空 `transactionid` 属正常值。
2. 漏斗：以独立访客为单位，严格要求 `view < addtocart < transaction`，另列浏览后购买但不强求加购的访客数。该口径跨商品、跨会话，不能解释为单次访问转化率。
3. 预测：在每个 UTC 截点前 14 天有事件的访客进入样本；特征只来自截点前 14 天，标签是截点后 7 天内是否发生交易。训练截点为 6 月 1 日、6 月 15 日、7 月 1 日、7 月 15 日；8 月 1 日验证；8 月 15 日最终测试。模型比较逻辑回归和随机森林，按验证集 PR-AUC 选型，再评估一次测试集。
4. 评估同时报告正例基准率、PR-AUC、ROC-AUC、0.5 阈值召回率和前 10% 用户购买率。重复访客可能出现在不同截点，但每条特征严格在对应标签之前。

## 运行

建议 Python 3.11 或以上。安装 `requirements.txt` 后，在本目录执行：

```bash
python -m src.download_data
python -m unittest discover -s tests
python -m src.run_pipeline
python -m src.build_paper --student-id YOUR_ID --student-name YOUR_NAME
streamlit run app/dashboard.py
```

输出保存在 `data/processed/`、`reports/`、`figures/`。原始数据与处理后数据体积较大，公开 Git 仓库默认忽略 `data/raw/` 和 `data/processed/`；课程提交包包含这两类数据文件、Word 论文和完整程序。

## 文件结构

```text
data/raw/                 原始 CSV（课程提交保留）
data/processed/           清洗数据与分时点样本
sql/                     DuckDB 清洗和分析查询
src/                     Python 漏斗、特征与模型流程
app/                     Streamlit 交互看板
figures/                 论文用图
reports/                 数据核验与模型结果
tests/                   时间边界和漏斗口径测试
```

## 商业含义与限制

这个项目可用于讨论转化路径流失和购买意愿排序，并提出后续 A/B 测试假设。观察性日志不能证明某项运营措施产生了因果增量；数据也没有渠道、广告费用和真实成交金额。数据时间跨度为 2015 年，结论不能直接外推至现在的中国电商市场。
