# 进阶配方（Advanced Recipes）

主 SKILL.md 的 API 速查覆盖常用路径，本文件放组合型配方。需要时按节取用，不必整篇加载。

## 线性规划（scipy.optimize.linprog）

标准形式是 `min c^T x, s.t. A_ub x <= b_ub, A_eq x = b_eq, bounds`。注意目标是最小化，最大化就把 c 取负。

```python
from scipy.optimize import linprog
# 例：max 3x+2y，s.t. x+y<=4，x<=2，x,y>=0
res = linprog(c=[-3, -2], A_ub=[[1, 1], [1, 0]], b_ub=[4, 2], bounds=[(0, None), (0, None)])
print(res.fun, res.x)   # res.success=False 时检查 A/b 是否写反
```

整数规划 scipy 不支持，需要时用 uv 装 pulp（`uv pip install --python <venv python> pulp`）。

## ODE 边值问题（solve_bvp）

初值问题用 solve_ivp；两端定边界条件的问题用 solve_bvp。

```python
import numpy as np
from scipy.integrate import solve_bvp
# 例：y'' = -y，y(0)=0，y(pi)=0 的平凡解；换 y(pi/2)=1 验证非零解
def fun(x, y):
    return np.vstack((y[1], -y[0]))
def bc(ya, yb):
    return np.array([ya[0], yb[0] - 0.0])
x = np.linspace(0, np.pi, 20)
y0 = np.zeros((2, x.size)); y0[0] = np.sin(x)   # 初猜给形状
sol = solve_bvp(fun, bc, x, y0)
print(sol.success, sol.sol(np.pi/4)[0], np.sin(np.pi/4))
```

要点：初猜要给非平凡形状，否则收敛到平凡解；`sol.sol(t)` 返回插值函数。

## 功效分析（样本量计算）

```python
from statsmodels.stats.power import TTestIndPower, NormalIndPower
# 独立双样本 t 检验：效应量 0.5、alpha 0.05、功效 0.8 → 所需每组样本量
n = TTestIndPower().solve_power(effect_size=0.5, nobs1=None, alpha=0.05, power=0.8)
print(n)   # 约 64
# 反向：给定样本量求功效
p = TTestIndPower().solve_power(effect_size=0.5, nobs1=40, alpha=0.05, power=None)
print(p)
```

效应量惯例：Cohen's d 的 0.2/0.5/0.8 = 小/中/大。

## 蒙特卡洛模拟

```python
import numpy as np
rng = np.random.default_rng(2026)
# 例：估算 pi（单位圆/正方形面积比）
n = 1_000_000
pts = rng.uniform(-1, 1, size=(n, 2))
inside = (pts**2).sum(axis=1) < 1
print("pi ≈", 4 * inside.mean(), "| 标准误", 4 * inside.std(ddof=1) / np.sqrt(n))
```

要点：报蒙特卡洛结果必须带标准误或置信区间；样本量按误差平方反比增长（误差 0.01 需约 1e4 倍于误差 0.1 的样本）。

## torch 自动微分（梯度/雅可比）

```python
import torch
# 多变量梯度
x = torch.tensor([1.0, 2.0], requires_grad=True)
f = (x[0]**2 + 3 * x[0] * x[1]).sum()
f.backward()
print(x.grad)   # [2x0+3x1, 3x0] = [8, 3]

# 高阶：create_graph 链式求二阶导
x = torch.tensor(1.5, requires_grad=True)
y = x**3
g = torch.autograd.grad(y, x, create_graph=True)[0]
g2 = torch.autograd.grad(g, x)[0]
print(g.item(), g2.item())   # 3x²=6.75, 6x=9
```

## 3D 曲面与等高线

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

X, Y = np.meshgrid(np.linspace(-3, 3, 100), np.linspace(-3, 3, 100))
Z = np.sin(np.sqrt(X**2 + Y**2))
fig = plt.figure(figsize=(12, 5))
ax1 = fig.add_subplot(121, projection='3d')
ax1.plot_surface(X, Y, Z, cmap='viridis')
ax2 = fig.add_subplot(122)
c = ax2.contourf(X, Y, Z, levels=20, cmap='viridis')
fig.colorbar(c, ax=ax2)
fig.savefig('~/plots/surface.png', dpi=120, bbox_inches='tight')
print('saved: ~/plots/surface.png')
```

## 符号 → 数值的完整链路（sympy 求导 + lambdify + 数值绘图）

```python
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

x = sp.symbols('x')
expr = sp.exp(-x**2 / 2) / sp.sqrt(2 * sp.pi)          # 标准正态密度
d1 = sp.diff(expr, x)                                    # 符号一阶导
f, f1 = sp.lambdify(x, expr, 'numpy'), sp.lambdify(x, d1, 'numpy')
xs = np.linspace(-4, 4, 200)
fig, ax = plt.subplots()
ax.plot(xs, f(xs), label='pdf'); ax.plot(xs, f1(xs), label='dpdf')
ax.legend(); fig.savefig('~/plots/gauss.png', dpi=120)
print('saved: ~/plots/gauss.png')
```

## 拟合的完整工作流（含拟合优度与置信带）

```python
import numpy as np
from scipy import optimize, stats

def model(x, a, b):
    return a * np.exp(-b * x)

rng = np.random.default_rng(1)
x = np.linspace(0, 4, 30)
y = model(x, 2.5, 0.8) + rng.normal(0, 0.15, x.size)
popt, pcov = optimize.curve_fit(model, x, y, p0=[1, 1])
perr = np.sqrt(np.diag(pcov))
resid = y - model(x, *popt)
ss_res = (resid**2).sum()
ss_tot = ((y - y.mean())**2).sum()
r2 = 1 - ss_res / ss_tot
t = popt / perr
pvals = 2 * (1 - stats.t.cdf(np.abs(t), df=x.size - len(popt)))
print("参数±标准误:", popt, perr)
print("R²:", r2, "| p 值:", pvals)
```

要点：拟合必须报参数不确定度（pcov 对角线开方）和 R²，只报参数值等于没报。
