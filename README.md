# anki

一个简易的 anki 模拟程序, 随机从语料库中抽取 card(一个记忆单元) 进行 review.

## Usage

在 `corpus` 文件夹中按照 `example.json` 所示的格式进行语料的添加; 在 `db_config.json` 中配置数据库连接信息; 最后执行 `main.py` 运行加载即可开始 review.

此时被加载的 json 文件会被添加上 `id`, 这与数据库中对应的 card 是一一对应的, 你可以直接修改 json 文件并重新加载, 数据库中对应的 card 也会被同步修改.

如果想移除被添加的 `id`, 只需调用 `op.unload(directory)` 方法即可.

## Algorithm Design

根据 forgetting curve 的基本原理, 一个记忆单元的 strength 随着 time 的增加而逐渐减小, 我们绘制如下图片:

![img](https://imgur.com/udFsixM.png)

*Stability 表示记忆的稳定性, 因人因材料而异*

从图中可以看出 memory 衰减的大致规律和程度, 只要我们通过 review 就可以保持和恢复 memory 的 strenth 并增强 stability 使其成为 long-term memory, 这也是 spaced repetition(间隔重复) 的基本原理.

这时候我们需要计算到达下一次 review 时间的 interval, 主要涉及到两个因素:

1. 当前 review 的 interval
2. 该 card 的 ease factor(难度系数)
2. memory 的 strength

如果一个 card 对于我们越轻松, 那么就需要增加其 ease factor 从而使其 review 的 interval 变大. 根据经验一般其取值区间为 [1.3, 2.5], 从而使得 interval 逐渐增加.

除此之外, 还可以考虑增加其他因素, 用于平衡 ease factor 的影响. 比如这里还额外使用了 success rate(成功率).


对于 ease factor 同样也需要通过指标进行衡量, 这里仅仅简单地使用回答时间.

## DB Design

数据库这里使用 mysql8, 涉及的字段有:

- `id`
- `language_type`: 语言类型
- `material_type`: 类型, 分为 word, phrase, sentence
- `original_content`: 原文
- `phonetic_alphabet`: 音标
- `translated_content`: 翻译后的原文
- `explanation`: 注解
- `test_times`: 测试次数
- `success_times`: 成功次数
- `last_review_date`: 最后 review 日期
- `memory_strangth`: 记忆强度
- `ease_factor`: 难度系数
- `next_review_date`: 下次 review 日期
- `inserted_date`: 插入日期