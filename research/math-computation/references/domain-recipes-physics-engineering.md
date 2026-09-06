# 物理与工程计算配方（Domain Recipes: Physics & Engineering）

物理/工程计算 = 微分方程 + 信号处理 + 数值方法，numpy/scipy 全覆盖，不引入 FEM 类重型工具。

## 偏微分方程：有限差分（热传导，numpy 手写）

```python
import numpy as np
# 一维热传导 u_t = α u_xx, 显式格式
nx, nt = 50, 1000
alpha, dx, dt = 0.01, 1.0/(nx-1), 0.001
assert alpha*dt/dx**2 < 0.5, "违反 CFL 稳定性条件"     # 显式格式必须检查
u = np.zeros((nt+1, nx))
u[0, nx//2] = 1.0                                     # 初始点热源
for n in range(nt):
    u[n+1, 1:-1] = u[n, 1:-1] + alpha*dt/dx**2 * (u[n, 2:] - 2*u[n, 1:-1] + u[n, :-2])
```

要点：显式差分必须验证 CFL 条件，违反会数值爆炸；二维扩散同理用五点格式。

## 信号处理：滤波与功率谱（scipy.signal）

```python
from scipy import signal
import numpy as np

# 低通 Butterworth 滤波
b, a = signal.butter(4, 0.1, btype="low")          # 4 阶, 归一化截止频率
filtered = signal.lfilter(b, a, raw_signal)

# 功率谱密度(Welch)
f, Pxx = signal.welch(signal_data, fs=1000, nperseg=256)
dominant = f[np.argmax(Pxx)]                        # 主频
```

要点：报滤波结果时说明滤波器阶数与截止频率；Welch 的 nperseg 影响频率分辨率，主频结论附分辨率说明。

## ODE 系统：SIR 传染病模型（solve_ivp）

```python
import numpy as np
from scipy.integrate import solve_ivp

def sir(t, y, beta, gamma):
    S, I, R = y
    N = S + I + R
    return [-beta*S*I/N, beta*S*I/N - gamma*I, gamma*I]

sol = solve_ivp(sir, [0, 200], [0.999, 0.001, 0.0], args=(0.3, 0.1), dense_output=True)
peak = sol.y[1].max()
R0 = 0.3 / 0.1                                    # 基本再生数 beta/gamma
print("R0 =", R0, "| 感染峰值 =", round(peak, 3))
```

要点：报 ODE 结论时必报参数与 R0 这类无纲量；参数来自文献时给引用。

## 线性时不变系统：传递函数响应（scipy.signal）

```python
from scipy import signal
sys = signal.TransferFunction([1], [1, 2, 1])     # 1 / (s²+2s+1)
t, y = signal.step(sys)                           # 阶跃响应
t2, y2, x2 = signal.lsim(sys, U=u_input, T=t)     # 任意输入
```

## 数值方法长尾速查

| 需求 | 方法 | 位置 |
| --- | --- | --- |
| 常微分方程初值 | solve_ivp | 主 SKILL.md |
| 常微分方程边值 | solve_bvp | references/advanced-recipes.md |
| 偏微分方程 | 有限差分手写 | 本文件 |
| 傅里叶分析 | fft / welch | 主 SKILL.md + 本文件 |
| 插值与拟合 | interp1d / curve_fit | 主 SKILL.md |
| 随机微分方程 | Euler-Maruyama 手写(需装 sdeint 或 numpy 实现) | 需要时装库 |

## 边界声明

有限元、CFD 等重型数值模拟超出本技能范围（需专业工具如 FEniCS/OpenFOAM），遇到这类需求如实说明并建议走专用软件，不硬用 numpy 凑。
