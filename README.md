# 电信号码爬虫

这是一个基于 Playwright 的爬虫，用于爬取广东电信选号吧的手机号列表。

## ✨ 功能特点

- 支持选择不同城市（深圳、广州等21个城市）
- 自动搜索 000* 到 999* 的所有号码模式
- 提取手机号、最低消费、预存话费等信息
- 自动保存结果到 JSON 文件
- 支持无头模式运行

## 📦 安装依赖

### 方法1: 使用已有虚拟环境（推荐）

如果你已经在 `telecom_spider` 目录下，虚拟环境已经设置好了：

```bash
# 激活虚拟环境
source venv/bin/activate

# 依赖已安装，直接使用
```

### 方法2: 从零开始安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖包
pip install playwright

# 4. 安装Playwright浏览器
playwright install chromium
```

## 🚀 使用方法

### 方法1: 多城市爬虫（推荐）✨

```bash
# 激活虚拟环境
source venv/bin/activate

# 爬取多个城市
python spider_multi_city.py --cities 深圳 广州 东莞

# 只爬取一个城市
python spider_multi_city.py --cities 深圳
```

### 方法2: 单城市爬虫

```bash
# 激活虚拟环境
source venv/bin/activate

# 爬取深圳地区（默认）
python spider_simple.py

# 爬取指定城市
python spider_simple.py --city 广州
```

### 其他方式

#### 方式1: 测试网站访问
```bash
# 测试是否能正常访问网站
python test_access.py
```

#### 方式2: 使用Scrapy（兼容性问题，不推荐）
```bash
# 注意：scrapy-playwright与最新版Scrapy有兼容性问题
scrapy crawl telecom -a city=深圳
```

## 输出结果

### 新版格式（按城市分组，每个号码单独一行）✨

爬虫运行完成后，会在当前目录生成JSON文件：

- 单城市：`phones_深圳_20260107_120341.json`
- 多城市：`phones_multi_20260107_120341.json`

JSON文件格式：
```json
[
  {
    "city": "深圳",
    "phone": [
      "13302482161",
      "13302914611",
      "18124070483"
    ]
  },
  {
    "city": "广州",
    "phone": [
      "13316458671",
      "17727422038"
    ]
  }
]
```

### 核心功能特点

1. ✅ **精确模式匹配** - 只提取真正匹配搜索条件的号码
   - 验证号码后7位是否包含搜索模式（如 `000`, `111`, `444`）
   - 过滤掉网站推荐的不相关号码
   - 避免误提取推荐号码

2. ✅ **按城市分组的JSON格式** - 易于处理和分析
   - 每个号码单独一行，便于阅读
   - 支持多城市数据在同一文件

3. ✅ **支持批量爬取多个城市** - 使用 `spider_multi_city.py`
   - 单城市爬取约30-60秒
   - 高效快速，不加载推荐号码

## 支持的城市

广州、深圳、佛山、中山、江门、珠海、东莞、惠州、汕头、揭阳、潮州、汕尾、湛江、茂名、阳江、云浮、肇庆、梅州、清远、河源、韶关

## 注意事项

1. 爬虫会搜索10个号码模式（000* 到 999*），整个过程可能需要较长时间
2. 为避免对服务器造成压力，已设置了延迟时间（2秒）
3. 如果需要爬取更多模式，可以修改 `telecom.py` 中的搜索循环逻辑

## 项目结构

```
telecom_spider/
├── phone_spider/          # Scrapy项目目录
│   ├── spiders/
│   │   └── telecom.py    # 爬虫主文件
│   ├── settings.py       # Scrapy配置
│   └── ...
├── run_spider.py         # 运行脚本
├── README.md            # 说明文档
└── venv/                # 虚拟环境
```

## 常见问题

### 1. 找不到scrapy命令
确保已激活虚拟环境：
```bash
source venv/bin/activate
```

### 2. Playwright浏览器启动失败
重新安装Playwright浏览器：
```bash
playwright install chromium
```

### 3. 爬取失败或超时
可以调整 `telecom.py` 中的延迟时间和超时设置。

