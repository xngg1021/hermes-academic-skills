# 社会科学与生物医学计算配方（Domain Recipes: Social Science & Biostatistics）

社科量化分析 = 统计推断 + 心理测量 + 纵向/生存建模，全部可用已装库实现。

## 问卷信度：Cronbach's α（pingouin）

```python
import pingouin as pg
# items: DataFrame, 每列一个量表条目(已反向计分)
alpha, ci = pg.cronbach_alpha(items)
print(alpha, ci)     # α ≥ 0.7 可接受, ≥ 0.8 良好; 附 95% 置信区间
```

## 效应量与事后检验（pingouin + scipy）

```python
import pingouin as pg
# Cohen's d(独立样本)
d = pg.compute_effsize(x, y, paired=False, eftype="cohen")
# ANOVA 后两两比较(Tukey)
tukey = pg.pairwise_tukey(data=df, dv="score", between="group")
# ANOVA 表(含效应量 eta 方)
aov = pg.anova(data=df, dv="score", between="group", detailed=True)
```

## 因子分析（sklearn，已装）

```python
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
X_scaled = StandardScaler().fit_transform(items)
fa = FactorAnalysis(n_components=3, rotation="varimax").fit(X_scaled)
loadings = fa.components_.T       # 载荷矩阵, |载荷|>0.4 判归属
```

先报 KMO 与 Bartlett 球形检验（用 `pingouin` 无现成函数时手写相关矩阵检验）判断是否适合做因子分析；载荷不清晰时调整因子数重跑，不硬解读。

## 中介与调节效应（分层回归，statsmodels 手写组合）

中介三步（Baron-Kenny 经典路径，现代论文建议加 bootstrap 检验）：

```python
# 1) X→Y 显著  2) X→M 显著  3) X+M→Y, M 显著且 X 系数下降
import statsmodels.api as sm
m1 = sm.OLS(y, sm.add_constant(x)).fit()          # 总效应
m2 = sm.OLS(med, sm.add_constant(x)).fit()        # X→M
m3 = sm.OLS(y, sm.add_constant(np.c_[x, med])).fit()   # 直接效应
# 中介比例 = (a*b) / c, 用 m2.params[1] * m3.params[2] / m1.params[1]
```

调节效应：加交互项 `x*z` 入回归，交互项显著即存在调节。

## 面板数据：固定效应（两种路径）

- 轻量路径（不装新库）：个体虚拟变量 OLS——`X = pd.get_dummies(id) + 时变变量`，注意虚拟变量陷阱（去掉一组基准）。
- 完整路径：需要时用 uv 装 linearmodels（`PanelOLS.from_formula("y ~ x + EntityEffects", df)`）。注意 linearmodels 对 pandas 3 的兼容性未验证，装前确认环境 pandas 版本（当前 2.3.3）。

## 生存分析（lifelines）

```python
from lifelines import KaplanMeierFitter, CoxPHFitter
kmf = KaplanMeierFitter()
kmf.fit(durations, event_observed=events)      # 1=发生事件, 0=删失
print(kmf.survival_function_at_times([12, 24, 36]))   # 各时点生存率
kmf.plot_survival_function()                   # 生存曲线(无头环境存图)
cph = CoxPHFitter().fit(df, duration_col="t", event_col="e")
print(cph.summary)                             # 风险比 exp(coef) 与 p 值
```

要点：删失变量必须明确（失访=0 不是事件）；Cox 需满足比例风险假设（`cph.check_assumptions()`），违反时如实报告并考虑分层。

## 调查抽样：分层加权估计

```python
import numpy as np
# 各层:样本均值 mean_s, 样本量 n_s, 总体占比 W_s
est = np.sum(W * means)                       # 加权总体均值
se = np.sqrt(np.sum((W**2) * vars / n))       # 近似标准误
```

抽样权重缺失时如实说明"按等概率抽样处理"，不假装有权重。
