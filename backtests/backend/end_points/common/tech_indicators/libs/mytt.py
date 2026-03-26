# MyTT 麦语言-通达信-同花顺指标实现     https://github.com/mpquant/MyTT
# MyTT高级函数验证版本：               https://github.com/mpquant/MyTT/blob/main/MyTT_plus.py
# Python2老版本pandas特别的MyTT：      https://github.com/mpquant/MyTT/blob/main/MyTT_python2.py
# V2.1  2021-6-6   新增 BARSLAST函数 SLOPE,FORCAST线性回归预测函数
# V2.3  2021-6-13  新增 TRIX,DPO,BRAR,DMA,MTM,MASS,ROC,VR,ASI等指标
# V2.4  2021-6-27  新增 EXPMA,OBV,MFI指标, 改进SMA核心函数(核心函数彻底无循环)
# V2.7  2021-11-21 修正 SLOPE,BARSLAST,函数,新加FILTER,LONGCROSS, 感谢qzhjiang对SLOPE,SMA等函数的指正
# V2.8  2021-11-23 修正 FORCAST,WMA函数,欢迎qzhjiang,stanene,bcq加入社群，一起来完善myTT库
# V2.9  2021-11-29 新增 HHVBARS,LLVBARS,CONST, VALUEWHEN功能函数
# V2.92 2021-11-30 新增 BARSSINCEN函数,现在可以 pip install MyTT 完成安装
# V3.0  2021-12-04 改进 DMA函数支持序列,新增XS2 薛斯通道II指标
# V3.1  2021-12-19 新增 TOPRANGE,LOWRANGE一级函数
# 以下所有函数如无特别说明，输入参数S均为numpy序列或者列表list，N为整型int
# 应用层1级函数完美兼容通达信或同花顺，具体使用方法请参考通达信
import math
import numpy as np
import pandas as pd


# ------------------ 0级：核心工具函数 --------------------------------------------
def RD(N, D=3):   return np.round(N, D)  # 四舍五入取3位小数


def RET(S, N=1):  return np.array(S)[-N]  # 返回序列倒数第N个值,默认返回最后一个


def ABS(S):      return np.abs(S)  # 返回N的绝对值


def LN(S):       return np.log(S)  # 求底是e的自然对数,


def POW(S, N):    return np.power(S, N)  # 求S的N次方


def SQRT(S):     return np.sqrt(S)  # 求S的平方根


def MAX(S1, S2):  return np.maximum(S1, S2)  # 序列max


def MIN(S1, S2):  return np.minimum(S1, S2)  # 序列min


def IF(S, A, B):   return np.where(S, A, B)  # 序列布尔判断 return=A  if S==True  else  B


def REF(S, N=1):  # 对序列整体下移动N,返回序列(shift后会产生NAN)
    default_value = False if S.dtype == bool else np.nan
    if isinstance(N, (int, float)):
        return pd.Series(S).shift(N, fill_value=default_value).values
    else:
        res = np.repeat(default_value, len(S))
        for i in range(len(N)):
            n_i = N[i]
            new_s = pd.Series(S).shift(n_i).values
            new_s_i = default_value if math.isnan(new_s[i]) else new_s[i]
            res[i] = new_s_i
        return res

def DIFF(S, N=1):  # 前一个值减后一个值,前面会产生nan
    return pd.Series(S).diff(N).values  # np.diff(S)直接删除nan，会少一行


def STD(S, N):  # 求序列的N日标准差，返回序列
    return pd.Series(S).rolling(N).std(ddof=0).values


# def SUM(S, N):  # 对序列求N天累计和，返回序列    N=0对序列所有依次求和
#     return pd.Series(S).rolling(N).sum().values if N > 0 else pd.Series(S).cumsum().values

# SUM is equivalent to COUNT when S is bool, but in SUM, S can be int or float as well
def SUM(S, N):  # 对序列求N天累计和，返回序列    N<=0对序列所有依次求和
    if isinstance(N, (int, float)):
        return pd.Series(S).rolling(N).sum().values if N > 0 else pd.Series(S).cumsum().values
    else:
        res = np.repeat(0, len(S))
        for i in range(len(S)):
            n_i = N[i]
            if np.isnan(n_i): continue
            s_index = i + 1 - n_i if n_i <= i + 1 else 0
            s_i = S[s_index: i + 1]
            res[i] = s_i.sum()
        return res


def CONST(S):  # 返回序列S最后的值组成常量序列
    return np.full(len(S), S[-1])


# def HHV(S, N):  # HHV(C, 5) 最近5天收盘最高价
#     return pd.Series(S).rolling(N).max().values
#
# def LLV(S, N):  # LLV(C, 5) 最近5天收盘最低价
#     return pd.Series(S).rolling(N).min().values

def HHV(S, N):  # HHV,支持N为序列版本
    # type: (np.ndarray, Optional[int,float, np.ndarray]) -> np.ndarray
    """
    HHV(C, 5)  # 最近5天收盘最高价
    """
    if isinstance(N, (int, float)):
        return pd.Series(S).rolling(N).max().values if N > 0 else pd.Series(S).cummax().values
    else:
        res = np.repeat(np.nan, len(S))
        for i in range(len(S)):
            if N[i] == 0: # if N = 0, cummax S
                res[i] = S[0:i + 1].max()
            elif (not np.isnan(N[i])) and N[i] <= i + 1:
                res[i] = S[i + 1 - N[i]:i + 1].max()
        return res


def LLV(S, N):  # LLV,支持N为序列版本
    # type: (np.ndarray, Optional[int,float, np.ndarray]) -> np.ndarray
    """
    LLV(C, 5)  # 最近5天收盘最低价
    """
    if isinstance(N, (int, float)):
        return pd.Series(S).rolling(N).min().values if N > 0 else pd.Series(S).cummin().values
    else:
        res = np.repeat(np.nan, len(S))
        for i in range(len(S)):
            if N[i] == 0: # if N = 0, cummin S
                res[i] = S[0:i + 1].min()
            elif (not np.isnan(N[i])) and N[i] <= i + 1:
                res[i] = S[i + 1 - N[i]:i + 1].min()
        return res


def HHVBARS(S, N):  # 求N周期内S最高值到当前周期数, 返回序列
    return pd.Series(S).rolling(N).apply(lambda x: np.argmax(x[::-1]), raw=True).values


def LLVBARS(S, N):  # 求N周期内S最低值到当前周期数, 返回序列
    return pd.Series(S).rolling(N).apply(lambda x: np.argmin(x[::-1]), raw=True).values


def MA(S, N):  # 求序列的N日简单移动平均值，返回序列
    return pd.Series(S).rolling(N).mean().values


def EMA(S, N):  # 指数移动平均,为了精度 S>4*N  EMA至少需要120周期     alpha=2/(span+1)
    return pd.Series(S).ewm(span=N, adjust=False).mean().values


def SMA(S, N, M=1):  # 中国式的SMA,至少需要120周期才精确 (雪球180周期)    alpha=1/(1+com)
    return pd.Series(S).ewm(alpha=M / N, adjust=False).mean().values  # com=N-M/M


def WMA(S, N):  # 通达信S序列的N日加权移动平均 Yn = (1*X1+2*X2+3*X3+...+n*Xn)/(1+2+3+...+n)
    return pd.Series(S).rolling(N).apply(lambda x: x[::-1].cumsum().sum() * 2 / N / (N + 1), raw=True).values


def DMA(S, A):  # 求S的动态移动平均，A作平滑因子,必须 0<A<1  (此为核心函数，非指标）
    if isinstance(A, (int, float)): return pd.Series(S).ewm(alpha=A, adjust=False).mean().values
    A = np.array(A);
    A[np.isnan(A)] = 1.0;
    Y = np.zeros(len(S));
    Y[0] = S[0]
    for i in range(1, len(S)): Y[i] = A[i] * S[i] + (1 - A[i]) * Y[i - 1]  # A支持序列 by jqz1226
    return Y


def AVEDEV(S, N):  # 平均绝对偏差  (序列与其平均值的绝对差的平均值)
    return pd.Series(S).rolling(N).apply(lambda x: (np.abs(x - x.mean())).mean()).values


def SLOPE(S, N):  # 返S序列N周期回线性回归斜率
    return pd.Series(S).rolling(N).apply(lambda x: np.polyfit(range(N), x, deg=1)[0], raw=True).values


def FORCAST(S, N):  # 返回S序列N周期回线性回归后的预测值， jqz1226改进成序列出
    return pd.Series(S).rolling(N).apply(lambda x: np.polyval(np.polyfit(range(N), x, deg=1), N - 1), raw=True).values


def LAST(S, A, B):  # 从前A日到前B日一直满足S_BOOL条件, 要求A>B & A>0 & B>=0
    return np.array(pd.Series(S).rolling(A + 1).apply(lambda x: np.all(x[::-1][B:]), raw=True), dtype=bool)


# ------------------   1级：应用层函数(通过0级核心函数实现）使用方法请参考通达信--------------------------------
# TODO: this count only works if S is bool sieries and is equivalent to SUM
def COUNT(S, N):  # COUNT(CLOSE>O, N):  最近N天满足S_BOO的天数  True的天数
    if isinstance(N, (int, float)):
        return SUM(S, N)
    else:
        res = np.repeat(0, len(S))
        for i in range(len(S)):
            n_i = N[i]
            if (not np.isnan(n_i)) and n_i <= i + 1:
                s_i = S[i + 1 - n_i:i + 1]
                res[i] = s_i.sum()
        return res


# def EVERY(S, N):  # EVERY(CLOSE>O, 5)   最近N天是否都是True
#     return IF(SUM(S, N) == N, True, False)

def EVERY(S, N):  # EVERY(CLOSE>O, 5)   最近N天是否都是True
    if isinstance(N, (int, float)):
        return IF(SUM(S, N) == N, True, False)
    else:
        res = np.repeat(False, len(S))
        for i in range(len(S)):
            n_i = N[i]
            if (not np.isnan(n_i)) and n_i <= i + 1:
                s_i = S[i + 1 - n_i:i + 1]
                res[i] = True if s_i.sum() == n_i else False
        return res


def EXIST(S, N):  # EXIST(CLOSE>3010, N=5)  n日内是否存在一天大于3000点
    return IF(SUM(S, N) > 0, True, False)


def FILTER(S, N):  # FILTER函数，S满足条件后，将其后N周期内的数据置为0, FILTER(C==H,5)
    for i in range(len(S)): S[i + 1:i + 1 + N] = 0 if S[i] else S[i + 1:i + 1 + N]
    return S  # 例：FILTER(C==H,5) 涨停后，后5天不再发出信号


def BARSLAST(S):  # 上一次条件成立到当前的周期, BARSLAST(C/REF(C,1)>=1.1) 上一次涨停到今天的天数
    M = np.concatenate(([0], np.where(S, 1, 0)))
    for i in range(1, len(M)):  M[i] = 0 if M[i] else M[i - 1] + 1
    return M[1:]


def BARSLASTCOUNT(S):  # 统计连续满足S条件的周期数        by jqz1226
    rt = np.zeros(len(S) + 1)  # BARSLASTCOUNT(CLOSE>OPEN)表示统计连续收阳的周期数
    for i in range(len(S)): rt[i + 1] = rt[i] + 1 if S[i] else rt[i + 1]
    return rt[1:]


def BARSSINCEN(S, N):  # N周期内第一次S条件成立到现在的周期数,N为常量  by jqz1226
    return pd.Series(S).rolling(N).apply(lambda x: N - 1 - np.argmax(x) if np.argmax(x) or x[0] else 0,
                                         raw=True).fillna(0).values.astype(int)


#input 必须是 narray
def CROSS(S1, S2):  # 判断向上金叉穿越 CROSS(MA(C,5),MA(C,10))  判断向下死叉穿越 CROSS(MA(C,10),MA(C,5))
    return np.concatenate(([False], np.logical_not((S1 > S2)[:-1]) & (S1 > S2)[1:]))  # 不使用0级函数,移植方便  by jqz1226


def LONGCROSS(S1, S2, N):  # 两条线维持一定周期后交叉,S1在N周期内都小于S2,本周期从S1下方向上穿过S2时返回1,否则返回0
    return np.array(np.logical_and(LAST(S1 < S2, N, 1), (S1 > S2)), dtype=bool)  # N=1时等同于CROSS(S1, S2)


def VALUEWHEN(S, X):  # 当S条件成立时,取X的当前值,否则取VALUEWHEN的上个成立时的X值   by jqz1226
    return pd.Series(np.where(S, X, np.nan)).ffill().values


def BETWEEN(S, A, B):  # S处于A和B之间时为真。 包括 A<S<B 或 A>S>B
    return ((A < S) & (S < B)) | ((A > S) & (S > B))


def TOPRANGE(S):  # TOPRANGE(HIGH)表示当前最高价是近多少周期内最高价的最大值 by jqz1226
    rt = np.zeros(len(S))
    for i in range(1, len(S)):  rt[i] = np.argmin(np.flipud(S[:i] < S[i]))
    return rt.astype('int')


def LOWRANGE(S):  # LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值 by jqz1226
    rt = np.zeros(len(S))
    for i in range(1, len(S)):  rt[i] = np.argmin(np.flipud(S[:i] > S[i]))
    return rt.astype('int')

def DSMA(X, N):  # 偏差自适应移动平均线   type: (np.ndarray, int) -> np.ndarray
    """
    Deviation Scaled Moving Average (DSMA)    Python by: jqz1226, 2021-12-27
    Referred function from myTT: SUM, DMA
    """
    a1 = math.exp(- 1.414 * math.pi * 2 / N)
    b1 = 2 * a1 * math.cos(1.414 * math.pi * 2 / N)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    Zeros = np.pad(X[2:] - X[:-2], (2, 0), 'constant')
    Filt = np.zeros(len(X))
    for i in range(len(X)):
        Filt[i] = c1 * (Zeros[i] + Zeros[i - 1]) / 2 + c2 * Filt[i - 1] + c3 * Filt[i - 2]

    RMS = np.sqrt(SUM(np.square(Filt), N) / N)
    ScaledFilt = Filt / RMS
    alpha1 = np.abs(ScaledFilt) * 5 / N
    return DMA(X, alpha1)


#TODO: doesn't work when X is bool series
# def SUMBARSFAST(X, A):
#     # type: (np.ndarray, Optional[np.ndarray, float, int]) -> np.ndarray
#     """
#     通达信SumBars函数的Python实现  by jqz1226
#     SumBars函数将X向前累加，直到大于等于A, 返回这个区间的周期数。例如SUMBARS(VOL, CAPITAL),求完全换手的周期数。
#     :param X: 数组。被累计的源数据。 源数组中不能有小于0的元素。
#     :param A: 数组（一组）或者浮点数（一个）或者整数（一个），累加截止的界限数
#     :return:  数组。各K线分别对应的周期数
#     """
#     if any(X <= 0):   raise ValueError('数组X的每个元素都必须大于0！')
#
#     X = np.flipud(X)  # 倒转
#     length = len(X)
#
#     if isinstance(A * 1.0, float):  A = np.repeat(A, length)  # 是单值则转化为数组
#     A = np.flipud(A)  # 倒转
#     sumbars = np.zeros(length)  # 初始化sumbars为0
#     Sigma = np.insert(np.cumsum(X), 0, 0.0)  # 在累加值前面插入一个0.0（元素变多1个，便于引用）
#
#     for i in range(length):
#         k = np.searchsorted(Sigma[i + 1:], A[i] + Sigma[i])
#         if k < length - i:  # 找到
#             sumbars[length - i - 1] = k + 1
#     return sumbars.astype(int)

def SUMBARS(X, A):
    # type: (np.ndarray, Optional[np.ndarray, float, int]) -> np.ndarray
    """
    通达信SumBars函数的Python实现  by jqz1226
    SumBars函数将X向前累加，直到大于等于A, 返回这个区间的周期数。例如SUMBARS(VOL, CAPITAL),求完全换手的周期数。
    :param X: 数组。被累计的源数据。 源数组中不能有小于0的元素。
    :param A: 数组（一组）或者浮点数（一个）或者整数（一个），累加截止的界限数
    :return:  数组。各K线分别对应的周期数
    """
    if any(X < 0):
        raise ValueError('数组X的每个元素都必须大于0！')

    X = np.flipud(X)  # 倒转
    length = len(X)

    if isinstance(A * 1.0, float):  A = np.repeat(A, length)  # 是单值则转化为数组
    A = np.flipud(A)  # 倒转
    sumbars = np.zeros(length)  # 初始化sumbars为0
    cumsum = np.cumsum(X)
    Sigma = np.insert(cumsum, 0, 0.0)  # 在累加值前面插入一个0.0（元素变多1个，便于引用）

    for i in range(length):
        k = np.searchsorted(Sigma[i + 1:], A[i] + Sigma[i])
        if k < length - i:  # 找到
            sumbars[length - i - 1] = k + 1
    return sumbars.astype(int)
