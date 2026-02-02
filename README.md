这是一个为您生成的 `README.md` 文档。它清晰地介绍了项目的功能、安装步骤以及配置方法，可以直接保存到您的项目根目录下。

---

# 🧬 AI 财富人格实验室 (AI Wealth Personality Lab)

**AI 财富人格实验室** 是一个基于 Streamlit 和 Google Gemini 大模型的智能应用。它将 **MBTI 人格心理学** 与 **商业案例分析** 相结合，帮助用户根据自己的性格类型和现有资金，寻找历史上相似起步的亿万富豪案例，并提供个性化的 AI 创业指导。

## ✨ 核心功能

1. **🧩 便捷 MBTI 自评**
* 内置 4 维人格快速自测工具（E/I, S/N, T/F, J/P）。
* 支持手动直接选择 MBTI 类型。
* 提供每种人格的详细性格关键词和图标。


2. **💰 实时财富案例匹配**
* **动态生成**：不再使用死数据。用户输入当前的启动资金（如“5000元”、“一台电脑”或“100万”）。
* **AI 检索**：调用 Gemini 模型，在商业史中实时检索与用户 **MBTI 相同** 且 **起步资金相似** 的真实亿万富豪/企业家案例。
* **结构化展示**：卡片式展示富豪姓名、创立公司、起步资源描述以及成功策略。


3. **💬 沉浸式人格对话**
* AI 会扮演用户选定的 MBTI 人格（如 INTJ 建筑师、ESTP 企业家）。
* 结合用户的资金状况，提供符合该性格特质的务实建议、创业指导或心理激励。



## 🛠️ 技术栈

* **Frontend**: [Streamlit](https://streamlit.io/)
* **LLM Engine**: [Google Gemini (Generative AI)](https://ai.google.dev/)
* **Language**: Python 3.8+

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/ai-wealth-lab.git
cd ai-wealth-lab

```

### 2. 安装依赖

建议使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate

# 安装依赖
pip install streamlit google-generativeai

```

### 3. 配置 API Key

本项目依赖 Google Gemini API。你需要创建一个 `.streamlit/secrets.toml` 文件来存储密钥。

1. 在项目根目录下创建文件夹 `.streamlit`。
2. 在文件夹内创建文件 `secrets.toml`。
3. 写入以下内容（替换为你的真实 Key）：

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "这里填写你的Google_Gemini_API_Key"

```

> **提示**: 你可以在 [Google AI Studio](https://aistudio.google.com/) 免费申请 API Key。

### 4. 运行应用

```bash
streamlit run app.py

```

浏览器将自动打开 `http://localhost:8501`。

## 📂 项目结构

```text
ai-wealth-lab/
├── app.py                 # 主应用程序代码
├── requirements.txt       # 依赖包列表
├── .streamlit/
│   └── secrets.toml       # 配置文件 (不要提交到 Git)
└── README.md              # 项目说明文档

```

## 📝 使用指南

1. **左侧边栏**：
* 点击 **"🧩 快速自评"** 标签，回答 4 个问题，系统会自动计算你的 MBTI。
* 或者点击 **"👇 直接选择"** 标签，手动指定你的人格类型。


2. **输入资金**：
* 在侧边栏下方的文本框中，输入你现在的资源（例如：“大学在读，只有生活费” 或 “存款50万”）。
* 点击 **"🔍 生成致富案例"**。


3. **查看案例**：
* 右侧主区域将显示 3 个与你情况最匹配的历史成功案例。


4. **AI 对话**：
* 在底部聊天框输入问题，例如：“以你的性格，如果是现在的我，第一步会做什么？”
* AI 将完全代入该人格进行回答。



## ⚠️ 免责声明

* 本应用生成的商业案例和建议由 AI 模型（Gemini）实时生成，仅供娱乐和参考，不构成专业的金融或投资建议。
* MBTI 理论仅作为性格参考框架，不代表心理学诊断。

## 📄 License

MIT License
