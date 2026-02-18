import type { ResearchReport } from '$lib/types/research';

const moutai600519: ResearchReport = {
  overview: {
    ticker: '600519',
    name: '贵州茅台',
    market: 'CN',
    price: 1698.00,
    change: 12.50,
    changePercent: 0.74,
    marketCap: 2135000000000,
    pe: 28.4,
    pb: 9.8,
    sector: '消费品',
    industry: '白酒/烈酒'
  },
  rating: {
    signal: 'strong-buy',
    targetPrice: 2100,
    safetyMargin: 23.7,
    moatScore: 9.2,
    riskLevel: 'low',
    thesis: '中国顶级奢侈消费品牌，具有无可复制的品牌护城河与定价权，受益于中产阶级财富积累',
    updatedAt: '2025-02-15'
  },
  financials: [
    {
      year: 2020,
      revenue: 97996000000,
      netIncome: 46697000000,
      operatingCashFlow: 49213000000,
      freeCashFlow: 47850000000,
      eps: 37.17,
      roe: 28.4,
      debtToEquity: 0.08,
      currentRatio: 3.42
    },
    {
      year: 2021,
      revenue: 106490000000,
      netIncome: 52460000000,
      operatingCashFlow: 53100000000,
      freeCashFlow: 51300000000,
      eps: 41.76,
      roe: 29.1,
      debtToEquity: 0.07,
      currentRatio: 3.61
    },
    {
      year: 2022,
      revenue: 127988000000,
      netIncome: 62715000000,
      operatingCashFlow: 64800000000,
      freeCashFlow: 62100000000,
      eps: 49.95,
      roe: 30.7,
      debtToEquity: 0.06,
      currentRatio: 3.85
    },
    {
      year: 2023,
      revenue: 150560000000,
      netIncome: 74734000000,
      operatingCashFlow: 77200000000,
      freeCashFlow: 74500000000,
      eps: 59.49,
      roe: 31.2,
      debtToEquity: 0.05,
      currentRatio: 4.12
    },
    {
      year: 2024,
      revenue: 173200000000,
      netIncome: 86200000000,
      operatingCashFlow: 89100000000,
      freeCashFlow: 85800000000,
      eps: 68.64,
      roe: 31.8,
      debtToEquity: 0.04,
      currentRatio: 4.45
    },
    {
      year: 2025,
      revenue: 193800000000,
      netIncome: 96500000000,
      operatingCashFlow: 99200000000,
      freeCashFlow: 95600000000,
      eps: 76.82,
      roe: 32.1,
      debtToEquity: 0.03,
      currentRatio: 4.78
    }
  ],
  valuation: [
    { metric: 'PE', current: 28.4, fiveYearAvg: 38.2, industryAvg: 22.1, percentile: 35 },
    { metric: 'PB', current: 9.8, fiveYearAvg: 13.4, industryAvg: 6.2, percentile: 42 },
    { metric: 'PS', current: 14.2, fiveYearAvg: 18.6, industryAvg: 5.8, percentile: 38 },
    { metric: 'EV/EBITDA', current: 22.1, fiveYearAvg: 29.8, industryAvg: 16.4, percentile: 40 },
    { metric: 'PEG', current: 1.42, fiveYearAvg: 1.89, industryAvg: 1.21, percentile: 45 }
  ],
  moat: [
    {
      name: '品牌护城河',
      score: 9.8,
      description: '茅台是中国最具辨识度的奢侈消费品牌，品牌价值远超产品本身',
      evidence: [
        '酱香白酒市场份额超过40%，价格领导地位稳固',
        '飞天茅台零售价长期高于官方指导价20-50%',
        '国宴用酒历史，政商文化深度绑定',
        '品牌历史超过300年，难以复制'
      ]
    },
    {
      name: '定价权',
      score: 9.5,
      description: '公司可以定期提价而不失去客户，经济周期影响有限',
      evidence: [
        '2024年飞天茅台零售价1499元出厂价多次上调',
        '经济下行期销售额仍保持两位数增长',
        '黄牛溢价长期存在，显示真实需求远超供给',
        '价格弹性极低，终端消费者对价格不敏感'
      ]
    },
    {
      name: '供给约束',
      score: 8.7,
      description: '酱香型白酒生产周期长（5年以上），产能无法快速扩张',
      evidence: [
        '茅台镇赤水河流域微生物环境不可复制',
        '核心产品生产周期约5年，库存即是壁垒',
        '每年可供应量固定，无法应对需求激增',
        '新建产能需要10年以上才能形成规模'
      ]
    },
    {
      name: '分销网络',
      score: 8.2,
      description: '全国经销商网络深度覆盖，渠道管控能力行业领先',
      evidence: [
        '全国超过2000家授权经销商',
        '直销渠道占比持续提升，利润率更高',
        'i茅台APP数字化直销平台用户超4000万',
        '经销商忠诚度高，转换成本大'
      ]
    },
    {
      name: '监管护城河',
      score: 7.8,
      description: '国有企业背景提供隐性政策保护，监管风险对竞争对手更大',
      evidence: [
        '贵州省政府持股53%，政治稳定性高',
        '生产许可证获取极为困难，行政壁垒高',
        '食品安全标准制定者，行业规则制定话语权强',
        '反腐政策风险已被历史验证可恢复'
      ]
    },
    {
      name: '成本优势',
      score: 7.1,
      description: '规模效应与原材料稳定供给带来持续的成本优势',
      evidence: [
        '毛利率稳定在91-92%，行业最高水平',
        '净利率约50%，每卖出2元即有1元利润',
        '高粱采购有长期锁定合同，价格稳定',
        '老酒库存升值，时间是天然资产'
      ]
    }
  ],
  risks: [
    {
      category: '政策风险',
      severity: 'high',
      description: '反腐力度加强可能压制政务消费，占总收入约15-20%',
      monitorTrigger: '政务接待消费政策收紧；高端消费税出台；党政机关宴请新规',
      bearishArgument: '若政策收紧如2012-2015年周期重演，股价可能下跌40-60%，恢复期3-5年'
    },
    {
      category: '代际消费变迁',
      severity: 'high',
      description: '年轻消费者（25-35岁）偏好进口烈酒、精酿啤酒，对传统白酒需求低',
      monitorTrigger: '天猫/京东白酒品类年轻用户占比下降；茅台销售增速持续低于GDP',
      bearishArgument: '10年内核心消费群体（50-65岁官员/商人）退休，若年轻一代不接棒，增长将停滞'
    },
    {
      category: '食品安全事件',
      severity: 'medium',
      description: '造假、塑化剂、农残等丑闻虽历史上均已克服，但短期冲击巨大',
      monitorTrigger: '任何食品安全相关新闻报道；质检总局抽查结果',
      bearishArgument: '重大食品安全事故可能导致股价单日跌停，品牌恢复需要1-3年'
    },
    {
      category: '宏观经济下行',
      severity: 'medium',
      description: '中国经济若进入深度衰退，高端消费首当其冲',
      monitorTrigger: 'GDP增速跌破4%；失业率持续上升；房价大幅下跌',
      bearishArgument: '消费降级趋势下，茅台溢价空间收窄，散瓶成交价跌破1000元将是警告信号'
    },
    {
      category: '竞争加剧',
      severity: 'low',
      description: '五粮液、泸州老窖等竞争对手持续追赶，酱香型白酒赛道拥挤',
      monitorTrigger: '茅台市场份额低于35%；竞争对手价格突破2000元/瓶',
      bearishArgument: '酱香型白酒产能大规模扩张导致供给过剩，价格战使行业毛利率下滑'
    }
  ],
  catalysts: [
    {
      date: '2025-03-28',
      event: '2024年年报发布',
      impact: 'positive',
      probability: 95,
      description: '预计全年收入超1700亿元，净利润超860亿元，同比增长约15%，超市场预期'
    },
    {
      date: '2025-06-15',
      event: '直销渠道扩容公告',
      impact: 'positive',
      probability: 70,
      description: 'i茅台新增配额或价格调整，直销比例进一步提升至40%以上，利润率改善'
    },
    {
      date: '2025-09-01',
      event: '国庆黄金周销售旺季',
      impact: 'positive',
      probability: 85,
      description: '传统送礼旺季，散瓶价格走强将提振投资者信心，渠道库存去化加速'
    },
    {
      date: '2025-12-10',
      event: '出厂价上调预期',
      impact: 'positive',
      probability: 55,
      description: '若渠道库存健康（散瓶价>1499元），茅台可能上调出厂价，直接提升净利润'
    }
  ],
  novaAnalysis: `# Meridian AI 投资分析 — 贵州茅台 (600519.SH)

> 分析日期：2025年2月15日 | 置信度：高

## 投资结论

**强力买入。** 贵州茅台是中国资本市场最稀缺的资产之一——一家拥有真正"护城河"的消费奢侈品公司。当前估值（PE 28x）处于历史低位区间，相对于其盈利质量和增长确定性，提供了难得的安全边际。

目标价：**¥2,100**（12个月）| 潜在回报：**+23.7%**

---

## 什么让茅台与众不同

茅台不是一家普通的食品饮料公司。它是**中国文化符码的变现载体**。

在中国商业社会中，送茅台不是在送酒，而是在传递一种无声的信号——"我有资源，我有关系，我尊重你"。这种文化功能使茅台的需求几乎与经济周期脱钩，更接近爱马仕包包而非普通消费品。

从财务角度，茅台的数字令人瞠目：
- **净利润率 ~50%**：全球消费品行业前1%
- **ROE 31.8%**：无杠杆下实现，意味着资本质量极高  
- **自由现金流转化率 99%+**：利润即现金，财务质量无可挑剔
- **资产负债率 <5%**：几乎零债务，抗风险能力极强

---

## 当前买入理由

1. **估值已到达价值区间**：PE 28x处于过去10年中位数以下（历史中位数约38x），主要由于市场对消费降级的过度担忧。

2. **直销战略红利尚未充分定价**：i茅台平台使公司绕过经销商直接触达消费者，毛利率提升空间巨大。当直销比例从当前30%提升至50%时，净利润率将进一步扩张。

3. **股息率已接近3%**：对于A股消费龙头，这一股息率具有吸引力，同时公司持续提升分红比例。

4. **逆向机会**：大量机构投资者因担心政策和消费降级而低配茅台，一旦预期改善，资金回流将形成正向反馈。

---

## 核心风险与应对

**最大的担忧是政策风险**，不是估值风险，不是竞争风险。

2012-2015年的反腐周期让茅台股价跌去60%，但随后的5年让坚持者获得10倍回报。关键问题是：**这是永久性损伤还是周期性冲击？**

历史给出了答案——茅台的品牌护城河每次都完整地走出了政策低谷。但这需要持有者有足够的认知和耐心。

**监控触发器**：若散瓶成交价跌破¥1,200，说明渠道出现实质性去库存压力，需要重新评估仓位。

---

## 组合配置建议

茅台在组合中的角色是**"压舱石"**，而非进攻性仓位。

- **建议仓位**：5-8%（重仓）
- **加仓时机**：PE跌破25x；政策恐慌性下跌
- **减仓信号**：PE超过50x；直销比例增长停滞；散瓶长期破价

茅台的持有，本质上是对中国商业文化长期延续的投注。只要这个文化符号不消亡，茅台的护城河就是永久的。

---

*本分析由 Meridian AI 生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*`,
  generatedAt: '2025-02-15T08:00:00Z'
};

const tencent00700: ResearchReport = {
  overview: {
    ticker: '00700',
    name: '腾讯控股',
    market: 'HK',
    price: 452.60,
    change: -3.40,
    changePercent: -0.75,
    marketCap: 4320000000000,
    pe: 18.2,
    pb: 3.4,
    sector: '科技',
    industry: '互联网/社交媒体'
  },
  rating: {
    signal: 'buy',
    targetPrice: 560,
    safetyMargin: 19.1,
    moatScore: 8.5,
    riskLevel: 'medium',
    thesis: '中国最大的社交与游戏平台，AI转型与商业化提升驱动估值重估，监管风险已充分定价',
    updatedAt: '2025-02-15'
  },
  financials: [
    {
      year: 2020,
      revenue: 482064000000,
      netIncome: 159847000000,
      operatingCashFlow: 182400000000,
      freeCashFlow: 168000000000,
      eps: 16.85,
      roe: 22.4,
      debtToEquity: 0.42,
      currentRatio: 1.87
    },
    {
      year: 2021,
      revenue: 560118000000,
      netIncome: 238939000000,
      operatingCashFlow: 206900000000,
      freeCashFlow: 184200000000,
      eps: 25.15,
      roe: 26.8,
      debtToEquity: 0.38,
      currentRatio: 1.92
    },
    {
      year: 2022,
      revenue: 554552000000,
      netIncome: 188243000000,
      operatingCashFlow: 164800000000,
      freeCashFlow: 143000000000,
      eps: 19.84,
      roe: 19.2,
      debtToEquity: 0.45,
      currentRatio: 1.75
    },
    {
      year: 2023,
      revenue: 609015000000,
      netIncome: 157688000000,
      operatingCashFlow: 189600000000,
      freeCashFlow: 168400000000,
      eps: 16.61,
      roe: 15.8,
      debtToEquity: 0.41,
      currentRatio: 1.88
    },
    {
      year: 2024,
      revenue: 660000000000,
      netIncome: 180000000000,
      operatingCashFlow: 210000000000,
      freeCashFlow: 188000000000,
      eps: 18.96,
      roe: 17.4,
      debtToEquity: 0.38,
      currentRatio: 1.95
    },
    {
      year: 2025,
      revenue: 720000000000,
      netIncome: 208000000000,
      operatingCashFlow: 238000000000,
      freeCashFlow: 215000000000,
      eps: 21.90,
      roe: 19.2,
      debtToEquity: 0.35,
      currentRatio: 2.05
    }
  ],
  valuation: [
    { metric: 'PE', current: 18.2, fiveYearAvg: 24.6, industryAvg: 20.4, percentile: 28 },
    { metric: 'PB', current: 3.4, fiveYearAvg: 5.8, industryAvg: 4.2, percentile: 32 },
    { metric: 'PS', current: 6.1, fiveYearAvg: 9.8, industryAvg: 7.4, percentile: 30 },
    { metric: 'EV/EBITDA', current: 14.2, fiveYearAvg: 19.6, industryAvg: 16.8, percentile: 35 },
    { metric: 'PEG', current: 0.91, fiveYearAvg: 1.32, industryAvg: 1.08, percentile: 25 }
  ],
  moat: [
    {
      name: '网络效应',
      score: 9.4,
      description: '微信12亿MAU构成无法绕过的社交基础设施，用户离开成本极高',
      evidence: [
        '微信渗透率超过中国智能手机用户的95%',
        '微信支付交易量占移动支付市场38%',
        '企业微信B端用户超7亿，工作场景深度绑定',
        '视频号生态闭环逐步形成'
      ]
    },
    {
      name: '生态系统护城河',
      score: 9.0,
      description: '从社交到支付到云到游戏的完整生态，用户和企业均深度依赖',
      evidence: [
        '小程序日活用户超5亿，去App化趋势有利腾讯',
        '腾讯云市场份额第二，企业迁移成本高',
        '游戏全球发行网络覆盖200+市场',
        '腾讯音乐、腾讯视频构成内容版权护城河'
      ]
    },
    {
      name: '数据壁垒',
      score: 8.8,
      description: '12亿用户的行为数据积累无法复制，AI训练基础远超竞争对手',
      evidence: [
        '用户社交图谱数据10年以上积累',
        '支付数据+社交数据+内容数据三位一体',
        '混元大模型已接入微信小程序场景',
        '广告精准度持续领先行业'
      ]
    },
    {
      name: '品牌与内容',
      score: 8.2,
      description: '游戏和娱乐领域的内容优势，以及企业级品牌信任度',
      evidence: [
        '《王者荣耀》《和平精英》长期霸榜',
        'Epic Games 40%股权，全球游戏IP储备丰富',
        '腾讯影业、腾讯动漫完善内容产业链'
      ]
    },
    {
      name: '规模成本优势',
      score: 7.6,
      description: '超大规模用户基础摊薄固定成本，边际成本趋近于零',
      evidence: [
        '云计算业务固定成本利用率持续提升',
        '广告业务毛利率超过60%',
        '国际游戏业务共用研发资产'
      ]
    },
    {
      name: '监管关系',
      score: 6.5,
      description: '2021年监管整治后与政府关系趋于稳定，合规成本已内化',
      evidence: [
        '监管整治期主动下架3000款游戏，合规姿态积极',
        '向政府基金捐款500亿元，社会责任投入加大',
        '管理层与监管机构沟通渠道畅通',
        '2023年后游戏版号审批恢复正常'
      ]
    }
  ],
  risks: [
    {
      category: '监管风险',
      severity: 'high',
      description: '互联网监管政策持续收紧，游戏版号限制、数据安全法等增加合规成本',
      monitorTrigger: '新一轮互联网整治行动；游戏版号暂停发放；数据出境限制扩大',
      bearishArgument: '若监管环境如2021年般急剧恶化，股价可能跌回300港元以下，需要2-3年恢复'
    },
    {
      category: '竞争压力',
      severity: 'high',
      description: '抖音(TikTok)在内容消费和广告市场大幅侵蚀腾讯份额',
      monitorTrigger: '微信MAU同比下降；广告市场份额跌破20%；视频号DAU增长停滞',
      bearishArgument: '若字节跳动推出替代性社交产品，微信护城河将面临史上最严峻挑战'
    },
    {
      category: 'AI转型不及预期',
      severity: 'medium',
      description: '若混元大模型商业化落地慢于预期，AI驱动的估值重估将落空',
      monitorTrigger: '混元付费用户增长低于50%；广告AI提效低于竞争对手',
      bearishArgument: '错过AI浪潮将使腾讯估值向传统互联网公司收敛，PE压缩至12x'
    },
    {
      category: '宏观与地缘政治',
      severity: 'medium',
      description: '中美关系恶化可能影响海外游戏业务（占收入约8%）',
      monitorTrigger: '美国制裁名单扩大；Epic Games出售压力增大；海外游戏收购受阻',
      bearishArgument: '若被迫出售Epic Games和Riot Games持股，将损失核心海外资产'
    },
    {
      category: '港股流动性',
      severity: 'low',
      description: '外资持续撤离港股市场，南向资金对冲效果有限',
      monitorTrigger: '港股日均成交量低于500亿港元；外资持腾讯比例跌破15%',
      bearishArgument: '全球资金从新兴市场撤退叠加港元脱钩担忧，可能引发无基本面的技术性下跌'
    }
  ],
  catalysts: [
    {
      date: '2025-03-20',
      event: '2024年全年业绩公告',
      impact: 'positive',
      probability: 88,
      description: '预计全年收入6600亿港元，净利润1800亿，广告收入超预期增长将是股价催化剂'
    },
    {
      date: '2025-05-08',
      event: '混元大模型2.0发布',
      impact: 'positive',
      probability: 65,
      description: 'AI能力提升将强化广告精准度和小程序生态变现，预计提升广告ARPU 10-15%'
    },
    {
      date: '2025-07-01',
      event: '视频号电商GMV里程碑',
      impact: 'positive',
      probability: 75,
      description: '视频号电商GMV有望突破1万亿，带动腾讯广告收入和支付流水双提升'
    },
    {
      date: '2025-10-15',
      event: '回购计划新一轮公告',
      impact: 'positive',
      probability: 80,
      description: '腾讯持续回购股份（2024年已回购超1000亿港元），股东回报持续提升'
    }
  ],
  novaAnalysis: `# Meridian AI 投资分析 — 腾讯控股 (00700.HK)

> 分析日期：2025年2月15日 | 置信度：中高

## 投资结论

**买入。** 腾讯正处于从"监管阴影期"向"AI驱动增长期"的关键转换节点。当前估值（PE 18x，PEG 0.91）是过去5年的历史低位，而基本面正在稳步改善。

目标价：**HK$560**（12个月）| 潜在回报：**+19.1%**

---

## 核心投资逻辑

腾讯的价值来自于一件别人做不到的事：**把12亿人的数字生活关在同一个生态里**。

微信不是一个App，它是中国数字基础设施的神经中枢。支付、通讯、购物、工作、娱乐——全部在微信内完成。这种网络效应产生的护城河，在全球科技公司中只有少数几家能与之媲美（Meta的WhatsApp+Facebook组合是最接近的对标）。

**AI是新的增长引擎，但市场尚未定价：**

腾讯在AI上的优势被低估了。与百度（纯AI押注）、阿里（云优先）不同，腾讯的AI战略是**将AI嵌入已有12亿用户的产品中**——成本摊薄，效果直接。混元大模型在广告优化上的应用，已在2024年Q4呈现出广告收入超预期增长。

---

## 为什么现在买

1. **估值已回到历史底部**：2021年监管打压使股价从750港元跌至200港元。当前450港元意味着市场仍在"永久折价"定价，但证据显示监管最严峻时刻已过。

2. **回购力度空前**：2024年腾讯累计回购超过1000亿港元，相当于市值的2.3%。持续回购在低位区间加速净每股收益增长。

3. **视频号商业化刚刚开始**：视频号电商GMV从0到万亿的旅程才走了30%。相比抖音电商5万亿GMV，这个差距就是腾讯未来3-5年的增长空间。

---

## 主要风险

**最大风险是监管政策不确定性**，而非业务基本面。

腾讯的商业模式是成立的，护城河是真实的。真正的风险是政策的不可预见性——这是一个需要接受的"中国溢价"折扣。

关键判断：如果你相信中国政府理解"腾讯是中国互联网全球竞争力的核心资产"，那么毁灭性监管的概率就是低的。

---

## 组合定位

- **建议仓位**：3-5%（中等仓位，对冲地缘风险）
- **加仓时机**：PE跌破15x；新一轮无基本面恐慌性下跌
- **减仓信号**：PE超过30x；新一轮监管整治启动信号

腾讯是"买中国科技的最好方式"这一命题，在当前价位依然成立。

---

*本分析由 Meridian AI 生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*`,
  generatedAt: '2025-02-15T08:00:00Z'
};

const reports: Record<string, ResearchReport> = {
  '600519': moutai600519,
  '00700': tencent00700
};

export function getMockReport(ticker: string): ResearchReport {
  const upper = ticker.toUpperCase();
  const found = reports[ticker] || reports[upper];
  if (found) return found;

  // Default fallback — return Moutai data with adjusted ticker
  return {
    ...moutai600519,
    overview: {
      ...moutai600519.overview,
      ticker: ticker.toUpperCase(),
      name: ticker.toUpperCase()
    }
  };
}

export const availableReports = [
  { ticker: '600519', name: '贵州茅台', market: 'CN' as const, signal: 'strong-buy' as const },
  { ticker: '00700', name: '腾讯控股', market: 'HK' as const, signal: 'buy' as const }
];
