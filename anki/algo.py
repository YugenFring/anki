import math
import difflib
import re

from datetime import datetime

def forgetting_curve(
        initial_strength: float,
        time_elapsed: float,
        stability=2.5
        ) -> float:
    """
    计算 memory 的 strength, 其公式为 f(x) = e^-x, x = t/s.
    根据 graph 可知 x = 0 时, f(x) = 1, f(x) 随 x 递增而递减, s 为记忆稳定性.
    s 的取值一般为 [1,7], 根据经验这里设置为 2.5.

    param:
    - initial_strength: memory 初始强度, 一般为 1, 表示 100% ([0, 1])
    - time_elapsed: 距离上次 review 所经过的时间 (单位: day)
    - stability: memory 的稳定性, 也就是对于 memory 的保持能力 (单位: day)

    return:
    - 新的 memory strength
    """
    return initial_strength * math.exp(-time_elapsed / stability)


def calculate_review_interval(
        current_interval: float,
        ease_factor: float,
        current_strength: float,
        success_rate: float
        ) -> float:
    """
    计算下次 review 的间隔

    param:
    - current_interval: 当前 review 间隔 (单位: day)
    - ease_factor: 难度系数 ([1.3, 2.5])
    - current_strength: 当前记忆强度 ([0, 1])
    - success_rate: answer 的成功率 ([0, 1])

    return:
    - 下次 review interval
    """
    strength_factor = 1 + (current_strength - 0.5) * 2  # 将 0-1 映射到 0-2
    success_factor = 0.8 + success_rate * 0.4  # 将成功率映射到 0.8-1.2
    new_interval = current_interval * ease_factor * strength_factor * success_factor
    min_interval = 0.25
    max_interval = 30
    return max(min_interval, min(round(new_interval, 2), max_interval))


def calculate_memory_strength(
        review_date: datetime,
        last_review_date: datetime,
        current_strength: float,
        stability=2.5
        ) -> float:
    """
    更新 memory 的 strength

    param:
    - review_date: 当前复习时间
    - last_review_date: 上次复习时间
    - current_strength: 当前 memory 的 strength
    - stability: memory 的稳定性
    """
    time_elapsed = (review_date - last_review_date).total_seconds()
    time_elapsed = round(time_elapsed / (24 * 3600), 2)
    new_strength = forgetting_curve(current_strength, time_elapsed, stability)
    return new_strength


def update_ease_factor(
        ease_factor: float,
        response_time: float,
        expected_time=30
        ) -> float:
    """
    根据 response_time 来更新 ease 系数

    param:
    - ease_factor: 难度系数
    - response_time: answer 时间
    - expected_time: 期望 answer 时间
    """
    time_ratio = response_time / expected_time
    # 最多为 2 倍的期望时间
    performance = max(0, min(2, time_ratio))
    # 以 1 为平衡点对 performance 进行 normalization 使得 f(x) 的 取值范围为 [-1, 1]
    normalized_performance = (performance - 1)
    # 使用 sigmoid 函数对 normalized_performance 进行平滑处理
    adjustment = 2 / (1 + math.exp(normalized_performance)) - 1
    # 限制 ease factor 的变化幅度为 20%
    new_ease_factor = ease_factor * (1 + 0.2 * adjustment)
    return max(1.3, min(2.5, new_ease_factor))


def compare_sentences(input_sentence: str, real_sentence: str) -> float:
    """
    使用 SequenceMatcher 计算两个句子的相似度

    param:
    - input_sentence: 被比较的 sentence
    - real_sentence: 正确的 sentence

    return:
    - 两个句子之间的百分比相似度
    """
    punctuations = r'[、。，．・：；？?！!～ー―‐\-＿_（）()［］\[\]｛｝{}' \
        '「」『』【】＜＞<>《》〈〉""''＂\"""''\'｀´¨＾\^…‥※＊\*＆\&＄\$＃\#＠\@。、\,\.\-]'
    input_sentence = re.sub(punctuations, '', input_sentence)
    real_sentence = re.sub(punctuations, '', real_sentence)
    similarity = difflib.SequenceMatcher(
        None, input_sentence, real_sentence).ratio()

    return similarity
