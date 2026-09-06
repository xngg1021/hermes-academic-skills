# 金融计算配方（Domain Recipes: Finance）

金融计算的底层是优化 + 统计 + 蒙特卡洛，全部可用 numpy/scipy/statsmodels/arch 实现，无需额外金融库。

## 收益率与绩效指标

```python
import numpy as np
prices = np.array([100, 102, 101, 105, 107])          # 收盘价序列
rets = np.diff(np.log(prices))                         # 对数收益率
ann_ret = rets.mean() * 252                            # 年化(假设日频)
ann_vol = rets.std(ddof=1) * np.sqrt(252)
sharpe = ann_ret / ann_vol
print(ann_ret, ann_vol, sharpe)
```

## 马科维茨组合优化（纯 scipy）

均值-方差前沿：最大化夏普或给定目标收益最小化方差，约束权重和为 1、可加卖空约束。

```python
import numpy as np
from scipy.optimize import minimize

# 输入:期望收益 mu(n,), 协方差 Sigma(n,n)
def portfolio_var(w, Sigma):
    return w @ Sigma @ w

n = len(mu)
cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]   # 权重和=1
bnds = [(0, 1)] * n                                     # 禁止卖空;允许卖空则改 (-1, 1)
# 最小方差组合
res = minimize(portfolio_var, np.ones(n)/n, args=(Sigma,), constraints=cons, bounds=bnds)
w_minvar = res.x
# 给定目标收益 r_target 下最小方差
cons2 = cons + [{"type": "eq", "fun": lambda w: w @ mu - r_target}]
res2 = minimize(portfolio_var, np.ones(n)/n, args=(Sigma,), constraints=cons2, bounds=bnds)
```

要点：协方差矩阵用样本估计时注意样本量小的问题（收缩估计可提但默认用样本协方差并说明）；边界解（某些权重为 0）是正常结果。

## 风险指标 VaR / CVaR（历史模拟）

```python
def var_cvar(returns, alpha=0.05):
    """returns: 组合历史收益率数组; alpha: 置信水平(5% = 95% VaR)"""
    var = np.quantile(returns, alpha)
    cvar = returns[returns <= var].mean()
    return var, cvar
```

参数法与蒙特卡洛法见通用配方蒙特卡洛节；历史模拟是最直观且无分布假设的基线。

## 期权定价：Black-Scholes（scipy.stats）

```python
from scipy.stats import norm
import numpy as np

def bs_call(S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
```

欧式看跌用平价关系 `P = C - S + K*e^(-rT)`。蒙特卡洛定价：几何布朗运动路径 `S_t = S_0 * exp((r-σ²/2)t + σ√t·Z)`，到期收益折现取均值，结果附标准误。

## 波动率建模 GARCH（arch 包）

```python
from arch import arch_model
import numpy as np

rng = np.random.default_rng(1)
r = rng.normal(0, 0.01, 1000)
am = arch_model(r * 100, vol="Garch", p=1, q=1, dist="normal")   # 收益按百分比放大数值稳定性
res = am.fit(disp="off")
print(res.summary())
fore = res.forecast(horizon=5)
print(fore.variance.tail(1).values)     # 未来波动率预测
```

要点：GARCH 拟合对初值与缩放敏感，收益先放大 100 倍；拟合失败报收敛问题，不硬凑结论。

## 因子回归（Fama-French 风格，statsmodels）

```python
import statsmodels.api as sm
# 组合超额收益 ret_e (T,), 因子矩阵 factors (T,k) (市场/规模/价值)
X = sm.add_constant(factors)
model = sm.OLS(ret_e, X).fit()
alpha = model.params["const"]     # 截距=alpha, 显著非零说明存在因子未解释的超额收益
print(model.summary())
```

## ARIMA 预测（statsmodels）

```python
from statsmodels.tsa.arima.model import ARIMA
model = ARIMA(series, order=(1, 1, 0)).fit()
forecast = model.forecast(steps=10)
```

先做平稳性检验（`adfuller`）再定差分阶数；季频数据用 SARIMAX（同库，加 seasonal_order）。
