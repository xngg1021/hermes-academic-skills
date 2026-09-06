# 金融计算配方（Domain Recipes: Finance）

金融计算的底层是优化 + 统计 + 蒙特卡洛，全部可用 numpy/scipy/statsmodels/arch 实现，无需额外金融库。

## 收益率与绩效指标

```python
# smoke-test: true
import numpy as np
prices = np.array([100., 102., 101., 105., 107.])  # 正价格、等间隔日频；短序列仅教学
assert np.isfinite(prices).all() and np.all(prices > 0) and len(prices) >= 3
log_rets = np.diff(np.log(prices))
ann_log_ret = log_rets.mean() * 252
geometric_ann_ret = np.expm1(ann_log_ret)
rets = prices[1:] / prices[:-1] - 1  # 常规 Sharpe 用简单超额收益
rf_annual = 0.0  # 明确零无风险年有效利率假设；实际任务替换
rf_daily = np.expm1(np.log1p(rf_annual) / 252)
excess = rets - rf_daily
ann_vol = excess.std(ddof=1) * np.sqrt(252)
sharpe = excess.mean() * 252 / ann_vol if ann_vol > 0 else np.nan
assert np.isclose(np.exp(log_rets.sum()), prices[-1] / prices[0])
assert np.isfinite(sharpe)
print(ann_log_ret, geometric_ann_ret, ann_vol, sharpe)
```

252 为交易日假设；平方根年化要求相关性可忽略且方差稳定。对数收益年化、几何年化与算术期望收益不能混称。零波动时 Sharpe 未定义，价格须先处理拆股/分红与缺失。

## 马科维茨组合优化（纯 scipy）

均值-方差前沿：最大化夏普或给定目标收益最小化方差，约束权重和为 1、可加卖空约束。

```python
import numpy as np
from scipy.optimize import minimize

# smoke-test: true
# 教学输入：年化简单收益 mu、年化协方差 Sigma；真实任务必须同频同单位。
mu = np.array([.06, .10])
Sigma = np.diag([.04, .09])
r_target = .08
# 日收益协方差在无序列相关假设下乘 252，波动率才乘 sqrt(252)。
def portfolio_var(w, Sigma):
    return w @ Sigma @ w

n = len(mu)
cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]   # 权重和=1
bnds = [(0, 1)] * n                                     # 禁止卖空;允许卖空则改 (-1, 1)
# 最小方差组合
res = minimize(portfolio_var, np.ones(n)/n, args=(Sigma,), constraints=cons, bounds=bnds)
assert res.success, res.message
w_minvar = res.x
assert np.allclose(w_minvar, [9/13, 4/13], atol=1e-5)
# 给定目标收益 r_target 下最小方差
cons2 = cons + [{"type": "eq", "fun": lambda w: w @ mu - r_target}]
res2 = minimize(portfolio_var, np.ones(n)/n, args=(Sigma,), constraints=cons2, bounds=bnds)
assert res2.success, res2.message
assert np.isclose(res2.x.sum(), 1) and np.isclose(res2.x @ mu, r_target)
assert np.allclose(res2.x, [.5, .5], atol=1e-6)
```

要点：协方差矩阵用样本估计时注意样本量小的问题（收缩估计可提但默认用样本协方差并说明）；边界解（某些权重为 0）是正常结果。

## 风险指标 VaR / CVaR（历史模拟）

```python
# smoke-test: true
import numpy as np
def var_cvar(returns, alpha=0.05):
    """alpha 是尾部概率；输出损失口径 VaR、ES，置信水平为 1-alpha。
    对等权经验分布，ES 取最差 alpha 质量；尾边界观察值按比例计入。
    全盈利样本的风险值可为负，不强制截断为零。
    """
    r = np.asarray(returns, dtype=float)
    if r.ndim != 1 or r.size == 0 or not np.isfinite(r).all() or not 0 < alpha < 1:
        raise ValueError('finite nonempty 1-D returns and 0 < alpha < 1 required')
    losses = np.sort(-r)[::-1]
    mass = alpha * r.size
    whole = int(np.floor(mass))
    fraction = mass - whole
    es = (losses[:whole].sum() + fraction * losses[min(whole, r.size-1)]) / mass
    var = np.quantile(-r, 1-alpha, method='inverted_cdf')
    return float(var), float(es)
assert np.allclose(var_cvar([-.10, -.04, .02, .05], .375), [.04, .08])
assert np.allclose(var_cvar([.01, .01], .05), [-.01, -.01])
```

经验分布的分位数约定已显式给出；ES（常称 CVaR）用尾部概率质量定义，避免小样本/并列分位点时简单条件平均改变尾部权重。历史模拟不指定参数分布，但依赖历史样本对未来风险的代表性。

## 期权定价：Black-Scholes（scipy.stats）

```python
# smoke-test: true
from scipy.stats import norm
import numpy as np

def bs_call(S, K, T, r, sigma):
    if not np.isfinite([S, K, T, r, sigma]).all() or S <= 0 or K <= 0 or T < 0 or sigma < 0:
        raise ValueError('finite S,K>0 and T,sigma>=0 required')
    if T == 0:
        return max(S-K, 0.)
    if sigma == 0:
        return max(S-K*np.exp(-r*T), 0.)
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
assert abs(bs_call(100, 100, 1, .05, .2) - 10.450583572185565) < 1e-8
assert bs_call(110, 100, 0, .05, .2) == 10
assert np.isclose(bs_call(100, 100, 1, .05, 0), 100-100*np.exp(-.05))
```

假设无分红欧式期权、恒定年化连续复利 r 与年化 sigma，T 以年计；忽略交易摩擦。

欧式看跌用平价关系 `P = C - S + K*e^(-rT)`。蒙特卡洛定价：几何布朗运动路径 `S_t = S_0 * exp((r-σ²/2)t + σ√t·Z)`，到期收益折现取均值，结果附标准误。

## 波动率建模 GARCH（arch 包）

```python
# smoke-test: true
from arch import arch_model
import numpy as np

rng = np.random.default_rng(1)
r = rng.normal(0, 0.01, 1000)
am = arch_model(r * 100, vol="Garch", p=1, q=1, dist="normal")   # 收益按百分比放大数值稳定性
res = am.fit(disp="off")
assert res.convergence_flag == 0, res.optimization_result.message
print(res.summary())
fore = res.forecast(horizon=5)
variance_decimal = fore.variance.iloc[-1].to_numpy() / 100**2
volatility_decimal = np.sqrt(variance_decimal)  # 每期小数收益波动率，不是年化
assert np.all(variance_decimal >= 0) and np.isfinite(volatility_decimal).all()
assert np.allclose(volatility_decimal**2 * 100**2, fore.variance.iloc[-1])
print('period volatility (decimal):', volatility_decimal)
# 含动态均值时 variance 与 residual_variance 不同；这里默认常数均值。
```

要点：GARCH 拟合对初值与缩放敏感，收益先放大 100 倍；拟合失败报收敛问题，不硬凑结论。

## 因子回归（Fama-French 风格，statsmodels）

```python
# smoke-test: true
import numpy as np
rng = np.random.default_rng(14)
factors = rng.normal(size=(100, 3))
ret_e = .01 + factors @ np.array([.2, -.1, .3])  # 无噪声代数核验，不用于显著性推断
import statsmodels.api as sm
# 组合超额收益 ret_e (T,), 因子矩阵 factors (T,k) (市场/规模/价值)
import numpy as np
X = sm.add_constant(np.asarray(factors, dtype=float), has_constant='add')
model = sm.OLS(ret_e, X).fit()
alpha = model.params[0]     # 截距 alpha；显著性依赖模型与误差假设，不等于可实现套利
assert np.allclose(model.params, [.01, .2, -.1, .3])
print(model.params)
```

## ARIMA 预测（statsmodels）

```python
# smoke-test: true
import numpy as np
rng = np.random.default_rng(12)
series = np.cumsum(rng.normal(size=300))  # 教学随机游走
from statsmodels.tsa.arima.model import ARIMA
model = ARIMA(series, order=(1, 1, 0)).fit()
forecast = model.forecast(steps=10)
assert model.mle_retvals['converged']
assert forecast.shape == (10,) and np.isfinite(forecast).all()
```

先做平稳性检验（`adfuller`）再定差分阶数；季频数据用 SARIMAX（同库，加 seasonal_order）。
