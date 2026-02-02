import streamlit as st
import google.generativeai as genai
import datetime
import time
import re
import sqlite3
import uuid

# -------------------------------------------------------------
# --- 0. 页面核心配置 ---
# -------------------------------------------------------------
st.set_page_config(
    page_title="MBTI人格自评与富豪案例助手", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# --- 1. CSS 注入 (适配自评/资金输入/案例展示模块) ---
# -------------------------------------------------------------
st.markdown("""
<style>
    /* 全局基础样式 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f4f7f9 !important;
        font-family: 'Noto Sans SC', sans-serif !important;
        color: #333 !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    .main .block-container {
        padding: 0 !important;
        padding-bottom: 6rem !important;
        max-width: 100% !important;
    }

    /* 顶部导航栏 */
    .nav-bar {
        background: #fff; border-bottom: 1px solid #e0e0e0; padding: 15px 40px;
        position: sticky; top: 0; z-index: 999; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .logo-text { font-size: 1.2rem; font-weight: 700; color: #6a5acd; letter-spacing: 0.5px; }
    .nav-tag {
        background: #f0e6ff; color: #6a5acd; font-size: 0.75rem;
        padding: 4px 8px; border-radius: 4px; margin-left: 12px; font-weight: 500;
    }

    /* 主内容容器 */
    .main-content-wrapper { max-width: 900px; margin: 0 auto; padding: 30px 20px; }

    /* 标题区域 */
    .hero-section { margin-bottom: 30px; text-align: left; }
    .page-title { font-size: 2rem !important; font-weight: 700 !important; color: #1a1a1a !important; margin-bottom: 8px !important; }
    .subtitle { font-size: 1rem !important; color: #666 !important; font-weight: 400 !important; line-height: 1.5; }

    /* 功能卡片（核心模块样式） */
    .func-card {
        background: #fff; border-radius: 10px; border: 1px solid #e0e0e0;
        padding: 24px; margin-bottom: 24px; box-shadow: 0 3px 10px rgba(0,0,0,0.02);
    }
    .func-card-title {
        font-size: 1.1rem; font-weight: 700; color: #6a5acd;
        margin-bottom: 20px; padding-left: 10px; border-left: 4px solid #6a5acd;
        display: flex; align-items: center; gap: 8px;
    }
    .func-card-desc {
        font-size: 0.9rem; color: #666; margin-bottom: 20px; line-height: 1.6;
    }

    /* MBTI自评选项样式 */
    .mbti-question {
        font-weight: 600; margin-bottom: 12px; color: #333; font-size: 0.95rem;
    }
    .mbti-options {
        display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
    }
    .mbti-option {
        flex: 1; min-width: 120px;
    }
    .stRadio > div { gap: 8px; }
    .stRadio label { font-size: 0.9rem; padding: 8px 12px; border-radius: 6px; }
    .stRadio label:hover { background: #f8f5ff; }

    /* 资金输入样式 */
    .fund-input { display: flex; align-items: center; gap: 12px; margin: 16px 0; }
    .fund-input .stNumberInput { flex: 1; }
    .fund-unit { font-size: 0.95rem; font-weight: 500; color: #555; }

    /* 富豪案例展示样式 */
    .case-card {
        background: #f8f9fa; border-radius: 8px; padding: 16px;
        margin-bottom: 12px; border-left: 3px solid #6a5acd;
    }
    .case-title {
        font-weight: 700; color: #222; margin-bottom: 8px; font-size: 0.95rem;
    }
    .case-content {
        font-size: 0.9rem; color: #444; line-height: 1.7;
    }
    .case-highlight { color: #6a5acd; font-weight: 600; }

    /* 聊天气泡样式 */
    [data-testid="stChatMessage"] { background: transparent !important; padding: 10px 0 !important; }
    [data-testid="stChatMessage"] > div:first-child { display: none !important; }
    .chat-row { display: flex; margin-bottom: 20px; width: 100%; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    .chat-avatar {
        width: 36px; height: 36px; border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; flex-shrink: 0;
    }
    .assistant .chat-avatar { background: #6a5acd; color: white; margin-right: 12px; }
    .user .chat-avatar { background: #9370db; color: white; margin-left: 12px; order: 2; }
    .chat-bubble {
        padding: 16px 20px; border-radius: 8px; font-size: 0.95rem;
        line-height: 1.6; max-width: 85%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .assistant .chat-bubble { background: #fff; border: 1px solid #e0e0e0; color: #1a1a1a; }
    .user .chat-bubble { background: #6a5acd; color: white; }

    /* 模型回复卡片 */
    .model-section-title {
        font-size: 0.9rem; font-weight: 700; color: #555;
        margin: 30px 0 15px 0; text-transform: uppercase;
        letter-spacing: 0.5px; border-left: 4px solid #6a5acd;
        padding-left: 10px;
    }
    .model-card {
        background: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
        margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .model-card-header {
        padding: 12px 20px; font-size: 0.9rem; font-weight: 600;
        background: #f8f9fa; border-bottom: 1px solid #e0e0e0;
        display: flex; align-items: center;
    }
    .gemini-header { color: #6a5acd; }
    .model-card-content {
        padding: 20px; font-size: 0.95rem; line-height: 1.7; color: #333;
    }

    /* 按钮样式统一 */
    div.stButton > button {
        border-radius: 8px !important; border: 1px solid #dcdfe6 !important;
        background: white !important; color: #333 !important;
        font-weight: 500 !important; transition: all 0.2s !important;
        padding: 8px 16px !important;
    }
    div.stButton > button:hover {
        border-color: #6a5acd !important; color: #6a5acd !important;
        background: #f0e6ff !important;
    }
    .primary-btn {
        background: #6a5acd !important; color: white !important;
        border-color: #6a5acd !important;
    }
    .primary-btn:hover {
        background: #5a4dbc !important; border-color: #5a4dbc !important;
        color: white !important;
    }
    .reset-btn {
        border-style: dashed !important; margin-top: 10px !important;
    }

    /* 底部输入框 */
    [data-testid="stChatInput"] {
        background: white !important; padding: 20px 0 !important;
        border-top: 1px solid #e0e0e0 !important;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.03) !important;
        z-index: 1000;
    }
    [data-testid="stChatInput"] > div { max-width: 900px !important; margin: 0 auto !important; }

    /* 光标动画 */
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    .blinking-cursor { animation: blink 1s infinite; color: #6a5acd; font-weight: bold; margin-left: 2px;}

    /* 统计模块 */
    .metric-container {
        display: flex; justify-content: center; gap: 20px;
        margin-top: 30px; padding: 15px; background: #f8f9fa;
        border-radius: 10px; border: 1px solid #e9ecef;
    }
    .metric-box { text-align: center; }
    .metric-sub { font-size: 0.8rem; color: #666; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 工具函数：文本格式化/通用处理 ---
# -------------------------------------------------------------
def clean_extra_newlines(text):
    """清理冗余换行和空格"""
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    cleaned = re.sub(r'　+', '', cleaned)
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip('\n')

def markdown_to_html(text):
    """Markdown转HTML，适配页面样式"""
    lines = [re.sub(r'###+', '', line.strip()) for line in text.split("\n") if not line.strip().startswith("###")]
    html_lines, in_list = [], False
    for line in lines:
        if not line: continue
        # 处理加粗标题
        if line.startswith("**") and line.endswith("**"):
            if in_list: html_lines.append("</ul>"); in_list = False
            content = line.strip("*")
            html_lines.append(f"<div style='color: #6a5acd; font-weight: 700; margin: 16px 0 8px; font-size: 1rem;'>{content}</div>")
        # 处理列表
        elif line.startswith(("- ", "* ")):
            if not in_list: html_lines.append("<ul style='margin: 0 0 16px 20px; padding: 0;'>"); in_list = True
            content = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', line[2:].strip())
            html_lines.append(f"<li style='margin-bottom: 6px;'>{content}</li>")
        # 处理普通段落
        else:
            if in_list: html_lines.append("</ul>"); in_list = False
            line = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', line)
            html_lines.append(f"<p style='margin-bottom: 10px;'>{line}</p>")
    if in_list: html_lines.append("</ul>")
    return "\n".join(html_lines)

# -------------------------------------------------------------
# --- 常量定义：MBTI维度/类型/人格描述 ---
# -------------------------------------------------------------
USER_ICON = "👤"
ASSISTANT_ICON = "🧠"
GEMINI_ICON = "♊️"

# MBTI 4个核心维度（自评题目）
MBTI_DIMENSIONS = [
    {
        "id": "EI",
        "question": "1. 你的精力获取方式？",
        "options": {
            "E": "外向 (E) - 从社交、外界互动中获取精力",
            "I": "内向 (I) - 从独处、内心思考中获取精力"
        }
    },
    {
        "id": "SN",
        "question": "2. 你的信息接收方式？",
        "options": {
            "S": "实感 (S) - 关注事实、细节、当下的实际情况",
            "N": "直觉 (N) - 关注灵感、趋势、未来的可能性"
        }
    },
    {
        "id": "TF",
        "question": "3. 你的决策判断方式？",
        "options": {
            "T": "思考 (T) - 基于逻辑、理性、客观分析做决策",
            "F": "情感 (F) - 基于感受、价值观、他人需求做决策"
        }
    },
    {
        "id": "JP",
        "question": "4. 你的生活行事方式？",
        "options": {
            "J": "判断 (J) - 喜欢计划、有序、有明确目标的生活",
            "P": "感知 (P) - 喜欢灵活、随性、随遇而安的生活"
        }
    }
]

# MBTI 16型人格完整映射（4维度组合 -> 人格名称+特质）
MBTI_16_TYPES_MAP = {
    "ISTJ": ("检查员", "注重实际、稳重可靠、责任感强，做事有条理，按规则行事"),
    "ISFJ": ("守护者", "富有同情心、乐于助人，注重和谐，善于照顾他人感受"),
    "INFJ": ("咨询师", "富有洞察力、理想主义，善于理解他人内心，有创造力"),
    "INTJ": ("策划师", "理性、创新、有战略眼光，善于分析和长期规划"),
    "ISTP": ("手艺人", "务实、灵活、善于动手，喜欢探索和解决实际问题"),
    "ISFP": ("艺术家", "敏感、温和、富有创造力，热爱生活和美好事物"),
    "INFP": ("调停者", "理想主义、富有想象力，追求内心和谐，善于共情"),
    "INTP": ("逻辑学家", "理性、好奇、善于分析，喜欢探索抽象概念和逻辑"),
    "ESTP": ("企业家", "外向、务实、善于应变，喜欢冒险和挑战新事物"),
    "ESFP": ("表演者", "外向、热情、善于交际，享受生活，富有感染力"),
    "ENFP": ("活动家", "外向、富有创造力，充满热情，善于激励和带动他人"),
    "ENTP": ("辩论家", "外向、机智、善于思辨，喜欢挑战传统，追求创新"),
    "ESTJ": ("总经理", "外向、务实、有领导力，注重效率和实际结果"),
    "ESFJ": ("执政官", "外向、热情、善于交际，注重和谐，乐于服务他人"),
    "ENFJ": ("教育家", "外向、富有同理心，有领导力，善于激励和引导他人"),
    "ENTJ": ("指挥官", "外向、果断、有战略眼光，善于领导和统筹规划")
}

# 生成带后缀的MBTI完整名称（如 ISTJ - 检查员）
def get_mbti_full_name(mbti_code):
    if mbti_code in MBTI_16_TYPES_MAP:
        name, _ = MBTI_16_TYPES_MAP[mbti_code]
        return f"{mbti_code} - {name}"
    return "未知人格类型"

# 获取MBTI人格描述
def get_mbti_desc(mbti_code):
    if mbti_code in MBTI_16_TYPES_MAP:
        _, desc = MBTI_16_TYPES_MAP[mbti_code]
        return desc
    return "暂无该人格的详细描述"

# MBTI人格系统对话指令
def get_mbti_system_prompt(mbti_code):
    full_name = get_mbti_full_name(mbti_code)
    desc = get_mbti_desc(mbti_code)
    return f"""你是{full_name}型人格，{desc}。你的沟通风格完全贴合该人格的核心特质，回答问题时保持一致的性格倾向，语言自然、符合该人格的思维和表达习惯。"""

# -------------------------------------------------------------
# --- 核心逻辑函数：自评计算/大模型调用/案例生成 ---
# -------------------------------------------------------------
def calculate_mbti_from_answers(answers):
    """【核心】根据4维度自评答案，计算用户的MBTI人格代码"""
    mbti_code = ""
    # 按EI、SN、TF、JP顺序拼接代码
    for dim in MBTI_DIMENSIONS:
        dim_id = dim["id"]
        mbti_code += answers.get(dim_id, "")
    # 验证代码有效性（4位大写字母）
    if re.match(r'^[EISNTFJP]{4}$', mbti_code):
        return mbti_code
    return None

def stream_gemini_response(prompt, model, max_retries=3):
    """Gemini流式回复函数，带429配额重试机制"""
    for attempt in range(max_retries):
        try:
            stream = model.generate_content(prompt, stream=True)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
                    time.sleep(0.02)
            return
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    yield f"⚠️ Gemini调用失败（429配额超限）：多次重试后仍失败，请稍后再试。{error_str[:80]}..."
                    break
            else:
                yield f"⚠️ Gemini调用失败：{error_str[:80]}..."
                break

def generate_billionaire_cases(mbti_code, start_fund, model):
    """【核心】调用大模型，生成同MBTI人格、同起步资金的3个真实亿万富豪案例"""
    mbti_full_name = get_mbti_full_name(mbti_code)
    mbti_desc = get_mbti_desc(mbti_code)
    
    # 精准提示词：确保案例真实、匹配资金量、贴合人格特质
    prompt = f"""
    你是全球商业史和MBTI人格研究专家，现需为{mbti_full_name}型人格用户，生成3个**真实、知名的白手起家亿万富豪案例**，要求严格遵循以下规则：
    1. 核心匹配：富豪的MBTI人格必须是{mbti_code}（{mbti_full_name}），创业起步资金必须与用户的{start_fund}万元人民币高度接近（误差不超过±50%）；
    2. 案例结构：每个案例包含「人物姓名+核心成就」「起步资金与创业起点」「创业路径与关键决策」「人格特质与商业成功的关联」4部分，逻辑清晰；
    3. 内容要求：基于真实商业史料，拒绝虚构人物/事件，语言简洁专业，每个案例200字左右，3个案例总字数不超过700字；
    4. 格式要求：用「1. 案例标题」开头，分点清晰，关键信息（如起步资金、人格特质）可加粗，便于阅读；
    5. 附加价值：案例需体现{mbti_code}人格的核心优势如何帮助富豪从该资金量起步实现财富跃迁，为用户提供可参考的商业思路。

    请直接输出案例内容，无需额外开场白和结束语！
    """
    try:
        # 调用Gemini生成结果（非流式，确保内容完整）
        response = model.generate_content(prompt)
        if response and response.text:
            return clean_extra_newlines(response.text)
        return "⚠️ 未生成有效案例内容，请稍后重试。"
    except Exception as e:
        return f"⚠️ 案例生成失败：{str(e)[:100]}..."

# -------------------------------------------------------------
# --- 全局状态初始化 ---
# -------------------------------------------------------------
# 初始化Gemini API配置
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
st.session_state["api_configured"] = bool(gemini_api_key)

# 初始化MBTI自评相关状态
if "mbti_answers" not in st.session_state:
    st.session_state["mbti_answers"] = {}  # 存储4维度自评答案
if "user_mbti_code" not in st.session_state:
    st.session_state["user_mbti_code"] = None  # 存储计算出的MBTI代码
if "user_mbti_full_name" not in st.session_state:
    st.session_state["user_mbti_full_name"] = ""  # 存储带后缀的MBTI名称

# 初始化资金和案例相关状态
if "start_fund" not in st.session_state:
    st.session_state["start_fund"] = 10  # 起步资金默认值（万元）
if "billionaire_cases" not in st.session_state:
    st.session_state["billionaire_cases"] = ""  # 存储生成的富豪案例

# 初始化对话相关状态
if "selected_mbti_code" not in st.session_state:
    st.session_state["selected_mbti_code"] = "ISTJ"  # 对话人格默认值
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "您好！完成MBTI自评和资金输入后，可生成专属富豪案例，也可直接选择人格开始对话～"}]

# 初始化Gemini通用模型（用于生成富豪案例+对话）
@st.cache_resource
def initialize_gemini_model():
    if not gemini_api_key:
        return None
    system_prompt = """
    你是专业的MBTI人格与商业创业结合的专家，同时能精准模拟16型MBTI人格的沟通风格。
    生成富豪案例时，严格遵循真实、匹配、专业的原则；进行人格对话时，完全贴合对应人格的核心特质和表达习惯。
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt
    )
gemini_model = initialize_gemini_model()

# -------------------------------------------------------------
# --- 页面核心渲染：模块化布局 ---
# -------------------------------------------------------------
# 顶部导航栏
st.markdown("""
<div class="nav-bar">
    <div class="logo-text">🧠 MBTI人格自评与富豪案例助手</div>
    <div class="nav-tag">4维度便捷自评 | 按资金量匹配真实案例 | 人格专属对话 | Powered by Gemini</div>
</div>
""", unsafe_allow_html=True)

# 主内容容器
st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

# 页面标题区域
st.markdown("""
<div class="hero-section">
    <h1 class="page-title">MBTI人格自评 + 专属亿万富豪案例</h1>
    <div class="subtitle">
        4道题快速完成MBTI自评 → 输入你的创业起步资金 → 生成「同人格+同资金量」的3个真实白手起家亿万富豪案例<br>
        基于Gemini大模型，案例100%真实，为你的创业/财富积累提供可参考的商业思路
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------- 模块1：MBTI 4维度便捷自评 --------------------------
st.markdown('<div class="func-card">', unsafe_allow_html=True)
st.markdown('<div class="func-card-title">📝 MBTI人格4维度便捷自评</div>', unsafe_allow_html=True)
st.markdown('<div class="func-card-desc">只需回答4道核心问题，快速判断你的MBTI人格类型，所有问题无对错，选择最贴合你的选项即可</div>', unsafe_allow_html=True)

# 渲染4个维度的自评问题和选项
for dim in MBTI_DIMENSIONS:
    dim_id = dim["id"]
    st.markdown(f'<div class="mbti-question">{dim["question"]}</div>', unsafe_allow_html=True)
    # 渲染单选框，存储答案到session_state
    selected_option = st.radio(
        label=dim["question"],
        options=list(dim["options"].keys()),
        format_func=lambda x: dim["options"][x],
        key=f"mbti_{dim_id}",
        horizontal=True,
        label_visibility="collapsed"
    )
    # 更新答案状态
    st.session_state["mbti_answers"][dim_id] = selected_option

# 自评提交按钮
col_calc, col_reset_self = st.columns([1, 3])
with col_calc:
    if st.button("✅ 完成自评，计算我的MBTI", use_container_width=True, type="primary"):
        # 计算MBTI代码
        mbti_code = calculate_mbti_from_answers(st.session_state["mbti_answers"])
        if mbti_code:
            st.session_state["user_mbti_code"] = mbti_code
            st.session_state["user_mbti_full_name"] = get_mbti_full_name(mbti_code)
            st.success(f"✅ 你的MBTI人格类型：{st.session_state['user_mbti_full_name']}")
            st.balloons()
        else:
            st.error("❌ 自评答案不完整，请完成所有4道题的选择后重试")
with col_reset_self:
    if st.button("🔄 重置自评答案", use_container_width=True, type="secondary"):
        # 重置所有自评相关状态
        st.session_state["mbti_answers"] = {}
        st.session_state["user_mbti_code"] = None
        st.session_state["user_mbti_full_name"] = ""
        st.session_state["billionaire_cases"] = ""
        st.rerun()

# 展示自评结果（若已计算）
if st.session_state["user_mbti_code"]:
    st.markdown(f"""
    <div style="margin-top: 20px; padding: 16px; background: #f8f5ff; border-radius: 8px; border: 1px solid #e9d8fd;">
        <div style="font-weight: 600; color: #6a5acd; margin-bottom: 8px;">你的MBTI人格结果</div>
        <div style="font-size: 0.95rem;">
            <span style="font-weight: 700;">{st.session_state['user_mbti_full_name']}</span> - {get_mbti_desc(st.session_state['user_mbti_code'])}
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 模块2：起步资金输入 + 富豪案例生成 --------------------------
st.markdown('<div class="func-card">', unsafe_allow_html=True)
st.markdown('<div class="func-card-title">💰 输入起步资金，生成专属富豪案例</div>', unsafe_allow_html=True)

# 仅当完成自评后，才显示资金输入和案例生成功能
if st.session_state["user_mbti_code"] and gemini_model:
    st.markdown(f'<div class="func-card-desc">基于你的「{st.session_state["user_mbti_full_name"]}」人格，输入你的创业/财富积累起步资金（万元），将为你生成3个<strong>同人格+同资金量</strong>的真实白手起家亿万富豪案例</div>', unsafe_allow_html=True)
    
    # 资金输入框（万元，范围1-10000，步长1）
    st.session_state["start_fund"] = st.number_input(
        label="起步资金（单位：万元人民币）",
        min_value=1,
        max_value=10000,
        value=st.session_state["start_fund"],
        step=1,
        key="fund_input",
        help="请输入你的实际资金量，案例将严格匹配该金额起步的富豪"
    )
    
    # 案例生成按钮
    if st.button("🚀 生成专属亿万富豪案例", use_container_width=True, type="primary"):
        with st.spinner(f"正在为你生成「{st.session_state['user_mbti_full_name']}」人格·{st.session_state['start_fund']}万元起步的真实富豪案例..."):
            # 调用大模型生成案例
            cases = generate_billionaire_cases(
                mbti_code=st.session_state["user_mbti_code"],
                start_fund=st.session_state["start_fund"],
                model=gemini_model
            )
            st.session_state["billionaire_cases"] = cases
    
    # 展示生成的案例（格式化展示）
    if st.session_state["billionaire_cases"]:
        st.markdown('<div style="margin-top: 24px;"><strong>📚 你的专属亿万富豪案例（真实·同人格·同资金量）</strong></div>', unsafe_allow_html=True)
        # 按换行拆分案例，格式化渲染
        case_lines = st.session_state["billionaire_cases"].split("\n")
        current_case = ""
        for line in case_lines:
            if line.startswith(("1.", "2.", "3.")) and current_case:
                st.markdown(f'<div class="case-card">{current_case}</div>', unsafe_allow_html=True)
                current_case = line
            else:
                current_case += line + "<br>"
        if current_case:
            st.markdown(f'<div class="case-card">{current_case}</div>', unsafe_allow_html=True)
elif not st.session_state["user_mbti_code"]:
    st.markdown('<div class="func-card-desc" style="color: #888;">👉 请先完成上方的MBTI4维度自评，再输入资金生成案例</div>', unsafe_allow_html=True)
elif not gemini_model:
    st.error("❌ 未配置有效的Gemini API Key，无法生成富豪案例，请在Streamlit Secrets中配置GEMINI_API_KEY")
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 模块3：MBTI人格对话（保留并融合自评结果） --------------------------
st.markdown('<div class="func-card">', unsafe_allow_html=True)
st.markdown('<div class="func-card-title">💬 MBTI人格专属对话</div>', unsafe_allow_html=True)
st.markdown('<div class="func-card-desc">选择任意MBTI人格，模拟该人格的核心特质进行对话，可选择你自评的人格，也可选择其他人格体验不同沟通风格</div>', unsafe_allow_html=True)

# 人格选择框（展示所有16型人格）
mbti_selector_options = [get_mbti_full_name(code) for code in MBTI_16_TYPES_MAP.keys()]
selected_mbti_full = st.selectbox(
    label="选择对话的MBTI人格",
    options=mbti_selector_options,
    # 优先选择用户自评的人格，否则选默认值
    index=mbti_selector_options.index(st.session_state["user_mbti_full_name"]) if st.session_state["user_mbti_full_name"] in mbti_selector_options else 0,
    key="mbti_chat_selector",
    label_visibility="collapsed"
)
# 提取选择的人格代码
st.session_state["selected_mbti_code"] = selected_mbti_full.split(" - ")[0]

# 重置对话按钮
if st.button("🔄 重置当前对话", use_container_width=True, type="secondary"):
    st.session_state.messages = [{"role": "assistant", "content": f"您好！我现在是{selected_mbti_full}人格，{get_mbti_desc(st.session_state['selected_mbti_code'])}，有什么想聊的吗？"}]
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 渲染对话历史
st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "assistant"
    avatar = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    content_html = markdown_to_html(msg["content"])
    st.markdown(f"""
    <div class="chat-row {role_class}">
        <div class="chat-avatar">{avatar}</div>
        <div class="chat-bubble">{content_html}</div>
    </div>
    """, unsafe_allow_html=True)

# 对话输入处理
if st.session_state.get("api_configured", False) and gemini_model:
    chat_input_text = st.chat_input(f"和{selected_mbti_full}聊聊天吧...")
    user_input = chat_input_text

    if user_input:
        # 显示用户消息
        st.markdown(f"""
        <div class="chat-row user">
            <div class="chat-avatar">{USER_ICON}</div>
            <div class="chat-bubble">{user_input}</div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 初始化对话专用模型（按选择的人格配置系统指令）
        chat_model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=get_mbti_system_prompt(st.session_state["selected_mbti_code"])
        )

        # 模型回复占位容器
        st.markdown('<div class="model-section-title">🔍 Gemini 人格专属回复</div>', unsafe_allow_html=True)
        gemini_placeholder = st.empty()

        # 生成流式回复
        gemini_full = ""
        with st.spinner(f"正在以{selected_mbti_full}人格回复..."):
            for chunk in stream_gemini_response(user_input, chat_model):
                gemini_full += chunk
                gemini_html = markdown_to_html(clean_extra_newlines(gemini_full))
                gemini_placeholder.markdown(f"""
                <div class="model-card">
                    <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({selected_mbti_full})</div>
                    <div class="model-card-content">{gemini_html}<span class="blinking-cursor">|</span></div>
                </div>
                """, unsafe_allow_html=True)

        # 完成态去除光标，保存对话历史
        gemini_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({selected_mbti_full})</div>
            <div class="model-card-content">{markdown_to_html(clean_extra_newlines(gemini_full))}</div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": gemini_full})
else:
    st.chat_input("请配置有效的Gemini API Key后开始对话", disabled=True)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 访问统计模块（保留并优化） --------------------------
DB_FILE = "visit_stats.db"
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_traffic (date TEXT PRIMARY KEY, pv_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitors (visitor_id TEXT PRIMARY KEY, first_visit_date TEXT)''')
    c.execute("PRAGMA table_info(visitors)")
    columns = [info[1] for info in c.fetchall()]
    if "last_visit_date" not in columns:
        try:
            c.execute("ALTER TABLE visitors ADD COLUMN last_visit_date TEXT")
            c.execute("UPDATE visitors SET last_visit_date = first_visit_date WHERE last_visit_date IS NULL")
        except Exception as e:
            print(f"数据库升级失败: {e}")
    conn.commit()
    conn.close()

def get_visitor_id():
    if "visitor_id" not in st.session_state:
        st.session_state["visitor_id"] = str(uuid.uuid4())
    return st.session_state["visitor_id"]

def track_and_get_stats():
    init_db()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    today_str = datetime.datetime.utcnow().date().isoformat()
    visitor_id = get_visitor_id()
    if "has_counted" not in st.session_state:
        try:
            c.execute("INSERT OR IGNORE INTO daily_traffic (date, pv_count) VALUES (?, 0)", (today_str,))
            c.execute("UPDATE daily_traffic SET pv_count = pv_count + 1 WHERE date=?", (today_str,))
            c.execute("SELECT visitor_id FROM visitors WHERE visitor_id=?", (visitor_id,))
            exists = c.fetchone()
            if exists:
                c.execute("UPDATE visitors SET last_visit_date=? WHERE visitor_id=?", (today_str, visitor_id))
            else:
                c.execute("INSERT INTO visitors (visitor_id, first_visit_date, last_visit_date) VALUES (?, ?, ?)", (visitor_id, today_str, today_str))
            conn.commit()
            st.session_state["has_counted"] = True
        except Exception as e:
            st.error(f"数据库写入错误: {e}")
    # 获取统计数据
    c.execute("SELECT COUNT(*) FROM visitors WHERE last_visit_date=?", (today_str,))
    today_uv = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM visitors")
    total_uv = c.fetchone()[0]
    c.execute("SELECT pv_count FROM daily_traffic WHERE date=?", (today_str,))
    res_pv = c.fetchone()
    today_pv = res_pv[0] if res_pv else 0
    conn.close()
    return today_uv, total_uv, today_pv

# 展示统计数据
try:
    today_uv, total_uv, today_pv = track_and_get_stats()
except Exception as e:
    today_uv, total_uv, today_pv = 0, 0, 0

st.markdown(f"""
<div class="metric-container">
    <div class="metric-box">
        <div class="metric-sub">今日独立访客：{today_uv} 人</div>
    </div>
    <div class="metric-box" style="border-left: 1px solid #dee2e6; border-right: 1px solid #dee2e6; padding: 0 20px;">
        <div class="metric-sub">历史总独立访客：{total_uv} 人</div>
    </div>
    <div class="metric-box">
        <div class="metric-sub">今日总访问量：{today_pv} 次</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 闭合主内容容器
st.markdown('</div>', unsafe_allow_html=True)
