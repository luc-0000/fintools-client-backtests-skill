# MyTT 麦语言-通达信-同花顺指标实现     https://github.com/mpquant/MyTT
# 高级函数版本，本文件函数计算结果经过验证完全正确，可以正常使用，但代码比较复杂，做为进阶使用。
# MyTT团队对每个函数精益求精，力争效率速度，代码优雅的完美统一，如果您有更好的实现方案，请不吝赐教！
# 感谢以下团队成员的努力和贡献： 火焰，jqz1226, stanene, bcq
from end_points.common.tech_indicators.libs.mytt import *


# ------------------   2级：技术指标函数(全部通过0级，1级函数实现） ------------------------------
def MACD(CLOSE, SHORT=12, LONG=26, M=9):  # EMA的关系，S取120日，和雪球小数点2位相同
    DIF = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG);
    DEA = EMA(DIF, M);
    MACD = (DIF - DEA) * 2
    return RD(DIF), RD(DEA), RD(MACD)


def KDJ(CLOSE, HIGH, LOW, N=9, M1=3, M2=3):  # KDJ指标
    RSV = (CLOSE - LLV(LOW, N)) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    K = EMA(RSV, (M1 * 2 - 1));
    D = EMA(K, (M2 * 2 - 1));
    J = K * 3 - D * 2
    return K, D, J


def RSI(CLOSE, N=24):  # RSI指标,和通达信小数点2位相同
    DIF = CLOSE - REF(CLOSE, 1)
    return RD(SMA(MAX(DIF, 0), N) / SMA(ABS(DIF), N) * 100)


def WR(CLOSE, HIGH, LOW, N=10, N1=6):  # W&R 威廉指标
    WR = (HHV(HIGH, N) - CLOSE) / (HHV(HIGH, N) - LLV(LOW, N)) * 100
    WR1 = (HHV(HIGH, N1) - CLOSE) / (HHV(HIGH, N1) - LLV(LOW, N1)) * 100
    return RD(WR), RD(WR1)


def BIAS(CLOSE, L1=6, L2=12, L3=24):  # BIAS乖离率
    BIAS1 = (CLOSE - MA(CLOSE, L1)) / MA(CLOSE, L1) * 100
    BIAS2 = (CLOSE - MA(CLOSE, L2)) / MA(CLOSE, L2) * 100
    BIAS3 = (CLOSE - MA(CLOSE, L3)) / MA(CLOSE, L3) * 100
    return RD(BIAS1), RD(BIAS2), RD(BIAS3)


def BOLL(CLOSE, N=20, P=2):  # BOLL指标，布林带
    MID = MA(CLOSE, N);
    UPPER = MID + STD(CLOSE, N) * P
    LOWER = MID - STD(CLOSE, N) * P
    return RD(UPPER), RD(MID), RD(LOWER)


def PSY(CLOSE, N=12, M=6):
    PSY = COUNT(CLOSE > REF(CLOSE, 1), N) / N * 100
    PSYMA = MA(PSY, M)
    return RD(PSY), RD(PSYMA)


def CCI(CLOSE, HIGH, LOW, N=14):
    TP = (HIGH + LOW + CLOSE) / 3
    return (TP - MA(TP, N)) / (0.015 * AVEDEV(TP, N))


def ATR(CLOSE, HIGH, LOW, N=20):  # 真实波动N日平均值
    TR = MAX(MAX((HIGH - LOW), ABS(REF(CLOSE, 1) - HIGH)), ABS(REF(CLOSE, 1) - LOW))
    return MA(TR, N)


def BBI(CLOSE, M1=3, M2=6, M3=12, M4=20):  # BBI多空指标
    return (MA(CLOSE, M1) + MA(CLOSE, M2) + MA(CLOSE, M3) + MA(CLOSE, M4)) / 4


def DMI(CLOSE, HIGH, LOW, M1=14, M2=6):  # 动向指标：结果和同花顺，通达信完全一致
    TR = SUM(MAX(MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1))), ABS(LOW - REF(CLOSE, 1))), M1)
    HD = HIGH - REF(HIGH, 1);
    LD = REF(LOW, 1) - LOW
    DMP = SUM(IF((HD > 0) & (HD > LD), HD, 0), M1)
    DMM = SUM(IF((LD > 0) & (LD > HD), LD, 0), M1)
    PDI = DMP * 100 / TR;
    MDI = DMM * 100 / TR
    ADX = MA(ABS(MDI - PDI) / (PDI + MDI) * 100, M2)
    ADXR = (ADX + REF(ADX, M2)) / 2
    return PDI, MDI, ADX, ADXR


def TAQ(HIGH, LOW, N):  # 唐安奇通道(海龟)交易指标，大道至简，能穿越牛熊
    UP = HHV(HIGH, N);
    DOWN = LLV(LOW, N);
    MID = (UP + DOWN) / 2
    return UP, MID, DOWN


def KTN(CLOSE, HIGH, LOW, N=20, M=10):  # 肯特纳交易通道, N选20日，ATR选10日
    MID = EMA((HIGH + LOW + CLOSE) / 3, N)
    ATRN = ATR(CLOSE, HIGH, LOW, M)
    UPPER = MID + 2 * ATRN;
    LOWER = MID - 2 * ATRN
    return UPPER, MID, LOWER


def TRIX(CLOSE, M1=12, M2=20):  # 三重指数平滑平均线
    TR = EMA(EMA(EMA(CLOSE, M1), M1), M1)
    TRIX = (TR - REF(TR, 1)) / REF(TR, 1) * 100
    TRMA = MA(TRIX, M2)
    return TRIX, TRMA


def VR(CLOSE, VOL, M1=26):  # VR容量比率
    LC = REF(CLOSE, 1)
    return SUM(IF(CLOSE > LC, VOL, 0), M1) / SUM(IF(CLOSE <= LC, VOL, 0), M1) * 100


def EMV(HIGH, LOW, VOL, N=14, M=9):  # 简易波动指标
    VOLUME = MA(VOL, N) / VOL;
    MID = 100 * (HIGH + LOW - REF(HIGH + LOW, 1)) / (HIGH + LOW)
    EMV = MA(MID * VOLUME * (HIGH - LOW) / MA(HIGH - LOW, N), N);
    MAEMV = MA(EMV, M)
    return EMV, MAEMV


def DPO(CLOSE, M1=20, M2=10, M3=6):  # 区间震荡线
    DPO = CLOSE - REF(MA(CLOSE, M1), M2);
    MADPO = MA(DPO, M3)
    return DPO, MADPO


def BRAR(OPEN, CLOSE, HIGH, LOW, M1=26):  # BRAR-ARBR 情绪指标
    AR = SUM(HIGH - OPEN, M1) / SUM(OPEN - LOW, M1) * 100
    BR = SUM(MAX(0, HIGH - REF(CLOSE, 1)), M1) / SUM(MAX(0, REF(CLOSE, 1) - LOW), M1) * 100
    return AR, BR


def DFMA(CLOSE, N1=10, N2=50, M=10):  # 平行线差指标
    DIF = MA(CLOSE, N1) - MA(CLOSE, N2);
    DIFMA = MA(DIF, M)  # 通达信指标叫DMA 同花顺叫新DMA
    return DIF, DIFMA


def MTM(CLOSE, N=12, M=6):  # 动量指标
    MTM = CLOSE - REF(CLOSE, N);
    MTMMA = MA(MTM, M)
    return MTM, MTMMA


def MASS(HIGH, LOW, N1=9, N2=25, M=6):  # 梅斯线
    MASS = SUM(MA(HIGH - LOW, N1) / MA(MA(HIGH - LOW, N1), N1), N2)
    MA_MASS = MA(MASS, M)
    return MASS, MA_MASS


def ROC(CLOSE, N=12, M=6):  # 变动率指标
    ROC = 100 * (CLOSE - REF(CLOSE, N)) / REF(CLOSE, N);
    MAROC = MA(ROC, M)
    return ROC, MAROC


def EXPMA(CLOSE, N1=12, N2=50):  # EMA指数平均数指标
    return EMA(CLOSE, N1), EMA(CLOSE, N2);


def OBV(CLOSE, VOL):  # 能量潮指标
    return SUM(IF(CLOSE > REF(CLOSE, 1), VOL, IF(CLOSE < REF(CLOSE, 1), -VOL, 0)), 0) / 10000


def MFI(CLOSE, HIGH, LOW, VOL, N=14):  # MFI指标是成交量的RSI指标
    TYP = (HIGH + LOW + CLOSE) / 3
    V1 = SUM(IF(TYP > REF(TYP, 1), TYP * VOL, 0), N) / SUM(IF(TYP < REF(TYP, 1), TYP * VOL, 0), N)
    return 100 - (100 / (1 + V1))


def ASI(OPEN, CLOSE, HIGH, LOW, M1=26, M2=10):  # 振动升降指标
    LC = REF(CLOSE, 1);
    AA = ABS(HIGH - LC);
    BB = ABS(LOW - LC);
    CC = ABS(HIGH - REF(LOW, 1));
    DD = ABS(LC - REF(OPEN, 1));
    R = IF((AA > BB) & (AA > CC), AA + BB / 2 + DD / 4, IF((BB > CC) & (BB > AA), BB + AA / 2 + DD / 4, CC + DD / 4));
    X = (CLOSE - LC + (CLOSE - OPEN) / 2 + LC - REF(OPEN, 1));
    SI = 16 * X / R * MAX(AA, BB);
    ASI = SUM(SI, M1);
    ASIT = MA(ASI, M2);
    return ASI, ASIT


def XSII(CLOSE, HIGH, LOW, N=102, M=7):  # 薛斯通道II
    AA = MA((2 * CLOSE + HIGH + LOW) / 4, 5)  # 最新版DMA才支持 2021-12-4
    TD1 = AA * N / 100;
    TD2 = AA * (200 - N) / 100
    CC = ABS((2 * CLOSE + HIGH + LOW) / 4 - MA(CLOSE, 20)) / MA(CLOSE, 20)
    DD = DMA(CLOSE, CC);
    TD3 = (1 + M / 100) * DD;
    TD4 = (1 - M / 100) * DD
    return TD1, TD2, TD3, TD4

    # 望大家能提交更多指标和函数  https://github.com/mpquant/MyTT

def SAR(HIGH, LOW, N=10, S=2, M=20):
    """
    求抛物转向。 例如SAR(10,2,20)表示计算10日抛物转向，步长为2%，步长极限为20%
    Created by: jqz1226, 2021-11-24首次发表于聚宽(www.joinquant.com)

    :param HIGH: high序列
    :param LOW: low序列
    :param N: 计算周期
    :param S: 步长
    :param M: 步长极限
    :return: 抛物转向
    """
    f_step = S / 100;
    f_max = M / 100;
    af = 0.0
    is_long = HIGH[N - 1] > HIGH[N - 2]
    b_first = True
    length = len(HIGH)

    s_hhv = REF(HHV(HIGH, N), 1)  # type: np.ndarray
    s_llv = REF(LLV(LOW, N), 1)  # type: np.ndarray
    sar_x = np.repeat(np.nan, length)  # type: np.ndarray
    for i in range(N, length):
        if b_first:  # 第一步
            af = f_step
            sar_x[i] = s_llv[i] if is_long else s_hhv[i]
            b_first = False
        else:  # 继续多 或者 空
            ep = s_hhv[i] if is_long else s_llv[i]  # 极值
            if (is_long and HIGH[i] > ep) or ((not is_long) and LOW[i] < ep):  # 顺势：多创新高 或者 空创新低
                af = min(af + f_step, f_max)
            #
            sar_x[i] = sar_x[i - 1] + af * (ep - sar_x[i - 1])

        if (is_long and LOW[i] < sar_x[i]) or ((not is_long) and HIGH[i] > sar_x[i]):  # 反空 或者 反多
            is_long = not is_long
            b_first = True
    return sar_x


def TDX_SAR(High, Low, iAFStep=2, iAFLimit=20):  # type: (np.ndarray, np.ndarray, int, int) -> np.ndarray
    """  通达信SAR算法,和通达信SAR对比完全一致   by: jqz1226, 2021-12-18
    :param High: 最高价序列
    :param Low: 最低价序列
    :param iAFStep: AF步长
    :param iAFLimit: AF极限值
    :return: SAR序列
    """
    af_step = iAFStep / 100;
    af_limit = iAFLimit / 100
    SarX = np.zeros(len(High))  # 初始化返回数组

    # 第一个bar
    bull = True
    af = af_step
    ep = High[0]
    SarX[0] = Low[0]
    # 第2个bar及其以后
    for i in range(1, len(High)):
        # 1.更新：hv, lv, af, ep
        if bull:  # 多
            if High[i] > ep:  # 创新高
                ep = High[i]
                af = min(af + af_step, af_limit)
        else:  # 空
            if Low[i] < ep:  # 创新低
                ep = Low[i]
                af = min(af + af_step, af_limit)
        # 2.计算SarX
        SarX[i] = SarX[i - 1] + af * (ep - SarX[i - 1])

        # 3.修正SarX
        if bull:
            SarX[i] = max(SarX[i - 1], min(SarX[i], Low[i], Low[i - 1]))
        else:
            SarX[i] = min(SarX[i - 1], max(SarX[i], High[i], High[i - 1]))

        # 4. 判断是否：向下跌破，向上突破
        if bull:  # 多
            if Low[i] < SarX[i]:  # 向下跌破，转空
                bull = False
                tmp_SarX = ep  # 上阶段的最高点
                ep = Low[i]
                af = af_step
                if High[i - 1] == tmp_SarX:  # 紧邻即最高点
                    SarX[i] = tmp_SarX
                else:
                    SarX[i] = tmp_SarX + af * (ep - tmp_SarX)
        else:  # 空
            if High[i] > SarX[i]:  # 向上突破, 转多
                bull = True
                ep = High[i]
                af = af_step
                SarX[i] = min(Low[i], Low[i - 1])
    # end for
    return SarX




