import streamlit as st
import google.generativeai as genai
import datetime
import os
import time
import re
import sqlite3
import uuid

# -------------------------------------------------------------
# --- 0. 页面配置 ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="MBTI人格对话助手", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# --- 1. CSS 注入 (调整风格适配MBTI主题) ---
# -------------------------------------------------------------

st.markdown("""
<style>
    /* === 1. 全局重置与字体 === */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

    * {
        box-sizing: border-box;
    }
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f4f7f9 !important;
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        color: #333333 !important;
    }

    /* === 2. 彻底去除顶部留白 === */
    [data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stToolbar"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 6rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }
    
    /* === 3. 顶部导航栏模拟 === */
    .nav-bar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 15px 40px;
        position: sticky;
        top: 0;
        z-index: 999;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .logo-text {
        font-size: 1.2rem;
        font-weight: 700;
        color: #6a5acd; /* MBTI主题紫 */
        letter-spacing: 0.5px;
    }
    .nav-tag {
        background-color: #f0e6ff;
        color: #6a5acd;
        font-size: 0.75rem;
        padding: 4px 8px;
        border-radius: 4px;
        margin-left: 12px;
        font-weight: 500;
    }

    /* === 4. 主容器限制 === */
    .main-content-wrapper {
        max-width: 900px;
        margin: 0 auto;
        padding: 30px 20px;
    }

    /* === 5. 标题区域 === */
    .hero-section {
        margin-bottom: 30px;
        text-align: left;
    }
    .page-title {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
        margin-bottom: 8px !important;
    }
    .subtitle {
        font-size: 1rem !important;
        color: #666666 !important;
        font-weight: 400 !important;
    }

    /* === 6. 聊天气泡 (MBTI风格) === */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 10px 0 !important;
    }
    [data-testid="stChatMessage"] > div:first-child {
        display: none !important; /* 隐藏默认头像，使用自定义 */
    }
    
    /* 自定义气泡容器 */
    .chat-row {
        display: flex;
        margin-bottom: 20px;
        width: 100%;
    }
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.assistant {
        justify-content: flex-start;
    }
    
    .chat-avatar {
        width: 36px;
        height: 36px;
        border-radius: 6px; /* 方形圆角 */
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }
    .assistant .chat-avatar {
        background-color: #6a5acd;
        color: white;
        margin-right: 12px;
    }
    .user .chat-avatar {
        background-color: #9370db;
        color: white;
        margin-left: 12px;
        order: 2;
    }

    .chat-bubble {
        padding: 16px 20px;
        border-radius: 8px;
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 85%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .assistant .chat-bubble {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        color: #1a1a1a;
    }
    .user .chat-bubble {
        background-color: #6a5acd;
        color: white;
        text-align: left;
    }

    /* === 7. MBTI选择器样式 === */
    .mbti-selector {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    /* === 8. 模型卡片 (仅保留Gemini) === */
    .model-section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #555;
        margin: 30px 0 15px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-left: 4px solid #6a5acd;
        padding-left: 10px;
    }

    .model-card {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    .model-card-header {
        padding: 12px 20px;
        font-size: 0.9rem;
        font-weight: 600;
        background-color: #f8f9fa;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        align-items: center;
    }
    
    .gemini-header { color: #6a5acd; }

    .model-card-content {
        padding: 20px;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #333;
    }

    /* === 9. 底部输入框 === */
    [data-testid="stChatInput"] {
        background-color: white !important;
        padding: 20px 0 !important;
        border-top: 1px solid #e0e0e0 !important;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.03) !important;
        z-index: 1000;
    }
    [data-testid="stChatInput"] > div {
        max-width: 900px !important;
        margin: 0 auto !important;
    }

    /* === 10. 按钮样式 (扁平化) === */
    div.stButton > button {
        border-radius: 6px !important;
        border: 1px solid #dcdfe6 !important;
        background-color: white !important;
        color: #333 !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    div.stButton > button:hover {
        border-color: #6a5acd !important;
        color: #6a5acd !important;
        background-color: #f0e6ff !important;
    }
    
    /* 清除按钮特殊样式 */
    [data-testid="stButton"] button[kind="secondary"] {
        margin-top: 20px;
        width: 100%;
        border-style: dashed !important;
    }

    /* 光标动画 */
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    .blinking-cursor { animation: blink 1s infinite; color: #6a5acd; font-weight: bold; margin-left: 2px;}
    
    /* === 11. 统计模块样式 === */
    .metric-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    .metric-box {
        text-align: center;
    }
    .metric-label {
        color: #6c757d;
        font-size: 0.85rem;
        margin-bottom: 2px;
    }
    .metric-value {
        color: #212529;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-sub {
        font-size: 0.7rem;
        color: #adb5bd;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 工具函数：Markdown 渲染 + 格式化 ---
# -------------------------------------------------------------
def clean_extra_newlines(text):
    """清理冗余换行/空格"""
    cleaned = re.sub(r'\n{3,}', '\n\n', text) # 保留最多两个换行
    cleaned = re.sub(r'　+', '', cleaned)
    cleaned = cleaned.strip('\n')
    return cleaned

def markdown_to_html(text):
    """
    将 Markdown 转为 HTML，过滤 ### 标题，优化 MBTI 风格输出。
    """
    # 第一步：彻底删除所有 ### 开头的行 + 清理孤立的 ### 符号
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        # 过滤 ### 标题行 + 清理行内孤立的 ###
        if not line.startswith("###"):
            clean_line = re.sub(r'###+', '', line)  # 删除所有###符号
            lines.append(clean_line)
    
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        
        # 处理加粗标题 (**标题**)
        if line.startswith("**") and line.endswith("**"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = line.strip("*")
            html_lines.append(f"<div style='color: #6a5acd; font-weight: 700; margin-top: 16px; margin-bottom: 8px; font-size: 1rem;'>{content}</div>")
            
        # 处理列表项 (- xxx)
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_lines.append("<ul style='margin: 0 0 16px 20px; padding: 0;'>")
                in_list = True
            content = line[2:].strip()
            content = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', content)
            html_lines.append(f"<li style='margin-bottom: 6px;'>{content}</li>")
            
        # 处理普通段落
        elif line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            line = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#6a5acd; font-weight:600;">\1</span>', line)
            html_lines.append(f"<p style='margin-bottom: 10px;'>{line}</p>")
            
    if in_list:
        html_lines.append("</ul>")
        
    return "\n".join(html_lines)

# -------------------------------------------------------------
# --- 1. 常量定义 ---
# -------------------------------------------------------------
USER_ICON = "👤"
ASSISTANT_ICON = "🧠"
GEMINI_ICON = "♊️"

# MBTI 16型人格定义
MBTI_16_TYPES = [
    "ISTJ - 检查员", "ISFJ - 守护者", "INFJ - 咨询师", "INTJ - 策划师",
    "ISTP - 手艺人", "ISFP - 艺术家", "INFP - 调停者", "INTP - 逻辑学家",
    "ESTP - 企业家", "ESFP - 表演者", "ENFP - 活动家", "ENTP - 辩论家",
    "ESTJ - 总经理", "ESFJ - 执政官", "ENFJ - 教育家", "ENTJ - 指挥官"
]

# 不同MBTI人格的系统指令模板
def get_mbti_system_prompt(mbti_type):
    """根据选择的MBTI类型生成对应的系统指令"""
    mbti_desc = {
        "ISTJ - 检查员": "你是ISTJ型人格（检查员），注重实际、稳重可靠、责任感强，做事有条理，喜欢按规则和传统行事，沟通风格直接、务实、注重细节。",
        "ISFJ - 守护者": "你是ISFJ型人格（守护者），富有同情心、乐于助人、有责任心，注重和谐，善于照顾他人感受，沟通风格温和、耐心、体贴。",
        "INFJ - 咨询师": "你是INFJ型人格（咨询师），富有洞察力、理想主义、有创造力，善于理解他人内心，沟通风格深刻、富有同理心、充满智慧。",
        "INTJ - 策划师": "你是INTJ型人格（策划师），理性、创新、有战略眼光，追求完美，善于分析和规划，沟通风格简洁、逻辑严密、直击核心。",
        "ISTP - 手艺人": "你是ISTP型人格（手艺人），务实、灵活、善于动手，喜欢探索和解决实际问题，沟通风格简洁、直接、注重实际效果。",
        "ISFP - 艺术家": "你是ISFP型人格（艺术家），敏感、温和、富有创造力，热爱生活和美好事物，沟通风格温柔、真诚、富有感染力。",
        "INFP - 调停者": "你是INFP型人格（调停者），理想主义、富有想象力、追求内心和谐，善于理解他人情感，沟通风格温柔、富有同理心、充满理想。",
        "INTP - 逻辑学家": "你是INTP型人格（逻辑学家），理性、好奇、善于分析，喜欢探索抽象概念，沟通风格理性、客观、富有逻辑性。",
        "ESTP - 企业家": "你是ESTP型人格（企业家），外向、务实、善于应变，喜欢冒险和挑战，沟通风格直接、自信、充满活力。",
        "ESFP - 表演者": "你是ESFP型人格（表演者），外向、热情、善于交际，喜欢享受生活，沟通风格活泼、热情、富有感染力。",
        "ENFP - 活动家": "你是ENFP型人格（活动家），外向、富有创造力、充满热情，善于激励他人，沟通风格活泼、富有想象力、充满正能量。",
        "ENTP - 辩论家": "你是ENTP型人格（辩论家），外向、机智、善于辩论，喜欢挑战和创新，沟通风格机智、幽默、富有思辨性。",
        "ESTJ - 总经理": "你是ESTJ型人格（总经理），外向、务实、有领导力，注重效率和结果，沟通风格直接、果断、富有权威性。",
        "ESFJ - 执政官": "你是ESFJ型人格（执政官），外向、热情、善于交际，注重和谐和他人感受，沟通风格热情、体贴、善于倾听。",
        "ENFJ - 教育家": "你是ENFJ型人格（教育家），外向、富有同理心、有领导力，善于激励和引导他人，沟通风格热情、富有感染力、充满智慧。",
        "ENTJ - 指挥官": "你是ENTJ型人格（指挥官），外向、果断、有战略眼光，善于领导和规划，沟通风格直接、自信、富有权威性。"
    }
    return mbti_desc.get(mbti_type, "你是一个MBTI人格对话助手，能够模拟不同人格的沟通风格。")

# -------------------------------------------------------------
# --- 2. 核心逻辑函数 ---
# -------------------------------------------------------------

def stream_gemini_response(prompt, model, max_retries=3):
    for attempt in range(max_retries):
        try:
            stream = model.generate_content(prompt, stream=True)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
                    time.sleep(0.02)
            return # 成功后退出函数
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 2秒, 4秒, 8秒
                    print(f"遇到 429 错误，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    # 达到最大重试次数，最终失败
                    yield f"⚠️ Gemini调用失败 (429 Quota Exceeded)：多次重试后仍失败。{error_str[:100]}..."
                    break # 退出循环
            else:
                # 其他非 429 错误，直接报告
                yield f"⚠️ Gemini调用失败：{error_str[:100]}..."
                break

# -------------------------------------------------------------
# --- 3. 初始化与状态 ---
# -------------------------------------------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
st.session_state["api_configured"] = bool(gemini_api_key)

# 初始化MBTI选择状态
if "selected_mbti" not in st.session_state:
    st.session_state["selected_mbti"] = MBTI_16_TYPES[0]  # 默认选择第一个

# 根据选择的MBTI类型初始化Gemini模型
@st.cache_resource
def initialize_gemini_model(mbti_type):
    if not gemini_api_key: return None
    system_prompt = get_mbti_system_prompt(mbti_type)
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash', 
        system_instruction=system_prompt
    )

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！请先选择一种MBTI人格，然后我们可以开始对话～"}
    ]

# -------------------------------------------------------------
# --- 4. 页面渲染 ---
# -------------------------------------------------------------

# --- 自定义顶部导航栏 ---
st.markdown("""
<div class="nav-bar">
    <div class="logo-text">🧠 MBTI人格对话助手</div>
    <div class="nav-tag">Powered by Gemini</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

# --- Hero 区域 ---
st.markdown("""
<div class="hero-section">
    <h1 class="page-title">MBTI 16型人格对话</h1>
    <div class="subtitle">选择一种人格类型，体验不同风格的沟通方式</div>
</div>
""", unsafe_allow_html=True)

# --- MBTI选择器 ---
st.markdown('<div class="mbti-selector">', unsafe_allow_html=True)
selected_mbti = st.selectbox(
    "选择MBTI人格类型",
    MBTI_16_TYPES,
    index=MBTI_16_TYPES.index(st.session_state["selected_mbti"]),
    key="mbti_selector"
)
# 如果选择了新的MBTI类型，重置对话
if selected_mbti != st.session_state["selected_mbti"]:
    st.session_state["selected_mbti"] = selected_mbti
    st.session_state.messages = [
        {"role": "assistant", "content": f"您好！我现在是{selected_mbti}人格，有什么想聊的吗？"}
    ]
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 历史消息渲染 (自定义 HTML 气泡) ---
st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "assistant"
    avatar = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    
    # 简单的 Markdown 转 HTML 用于历史记录
    content_html = markdown_to_html(msg["content"])
    
    st.markdown(f"""
    <div class="chat-row {role_class}">
        <div class="chat-avatar">{avatar}</div>
        <div class="chat-bubble">{content_html}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 输入处理 ---
chat_input_text = st.chat_input(f"和{st.session_state['selected_mbti']}聊聊天吧...")
user_input = chat_input_text

if user_input and st.session_state.get("api_configured", False):
    # 1. 显示用户提问
    st.markdown(f"""
    <div class="chat-row user">
        <div class="chat-avatar">{USER_ICON}</div>
        <div class="chat-bubble">{user_input}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. 初始化对应MBTI类型的Gemini模型
    gemini_model = initialize_gemini_model(st.session_state["selected_mbti"])
    
    # 3. 占位容器
    st.markdown('<div class="model-section-title">🔍 Gemini 回复</div>', unsafe_allow_html=True)
    gemini_placeholder = st.empty()

    # 4. Gemini生成回复
    gemini_full = ""
    with st.spinner(f"正在获取 {GEMINI_ICON} Gemini Flash 的回复..."):
        for chunk in stream_gemini_response(user_input, gemini_model):
            gemini_full += chunk
            # 实时更新占位符
            gemini_html = markdown_to_html(clean_extra_newlines(gemini_full))
            gemini_placeholder.markdown(f"""
            <div class="model-card">
                <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({st.session_state['selected_mbti']})</div>
                <div class="model-card-content">{gemini_html}<span class="blinking-cursor">|</span></div>
            </div>
            """, unsafe_allow_html=True)
    
    # 完成态去除光标
    gemini_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">{GEMINI_ICON} Gemini Flash ({st.session_state['selected_mbti']})</div>
        <div class="model-card-content">{markdown_to_html(clean_extra_newlines(gemini_full))}</div>
    </div>
    """, unsafe_allow_html=True)

    # 保存历史
    st.session_state.messages.append({"role": "assistant", "content": gemini_full})

# --- 底部清空 ---
if st.button('重置对话', key="reset_btn", help="清空所有历史"):
    st.session_state.messages = [
        {"role": "assistant", "content": f"您好！我现在是{st.session_state['selected_mbti']}人格，有什么想聊的吗？"}
    ]
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 访问统计模块 (保留原有功能) ---
# -------------------------------------------------------------

# -------------------------- 配置 --------------------------
DB_FILE = "visit_stats.db"

def init_db():
    """初始化数据库（包含自动修复旧表结构的功能）"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    # 1. 确保表存在
    c.execute('''CREATE TABLE IF NOT EXISTS daily_traffic 
                 (date TEXT PRIMARY KEY, 
                  pv_count INTEGER DEFAULT 0)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS visitors 
                 (visitor_id TEXT PRIMARY KEY, 
                  first_visit_date TEXT)''')
    
    # 2. 手动检查并添加缺失的列
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
    """获取或生成访客ID"""
    if "visitor_id" not in st.session_state:
        st.session_state["visitor_id"] = str(uuid.uuid4())
    return st.session_state["visitor_id"]

def track_and_get_stats():
    """核心统计逻辑"""
    init_db()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    today_str = datetime.datetime.utcnow().date().isoformat()
    visitor_id = get_visitor_id()

    # --- 写操作 (仅当本Session未计数时执行) ---
    if "has_counted" not in st.session_state:
        try:
            # 1. 更新每日PV
            c.execute("INSERT OR IGNORE INTO daily_traffic (date, pv_count) VALUES (?, 0)", (today_str,))
            c.execute("UPDATE daily_traffic SET pv_count = pv_count + 1 WHERE date=?", (today_str,))
            
            # 2. 更新访客UV信息
            c.execute("SELECT visitor_id FROM visitors WHERE visitor_id=?", (visitor_id,))
            exists = c.fetchone()
            
            if exists:
                c.execute("UPDATE visitors SET last_visit_date=? WHERE visitor_id=?", (today_str, visitor_id))
            else:
                c.execute("INSERT INTO visitors (visitor_id, first_visit_date, last_visit_date) VALUES (?, ?, ?)", 
                          (visitor_id, today_str, today_str))
            
            conn.commit()
            st.session_state["has_counted"] = True
            
        except Exception as e:
            st.error(f"数据库写入错误: {e}")

    # --- 读操作 ---
    # 1. 获取今日UV
    c.execute("SELECT COUNT(*) FROM visitors WHERE last_visit_date=?", (today_str,))
    today_uv = c.fetchone()[0]
    
    # 2. 获取历史总UV
    c.execute("SELECT COUNT(*) FROM visitors")
    total_uv = c.fetchone()[0]

    # 3. 获取今日PV
    c.execute("SELECT pv_count FROM daily_traffic WHERE date=?", (today_str,))
    res_pv = c.fetchone()
    today_pv = res_pv[0] if res_pv else 0
    
    conn.close()
    
    return today_uv, total_uv, today_pv

# -------------------------- 页面展示 --------------------------

# 执行统计
try:
    today_uv, total_uv, today_pv = track_and_get_stats()
except Exception as e:
    st.error(f"统计模块出错: {e}")
    today_uv, total_uv, today_pv = 0, 0, 0

# 展示数据
st.markdown(f"""
<div class="metric-container">
    <div class="metric-box">
        <div class="metric-sub">今日 UV: {today_uv} 访客数</div>
    </div>
    <div class="metric-box" style="border-left: 1px solid #dee2e6; border-right: 1px solid #dee2e6; padding-left: 20px; padding-right: 20px;">
        <div class="metric-sub">历史总 UV: {total_uv} 总独立访客</div>
    </div>
</div>
""", unsafe_allow_html=True)
