
import streamlit as st
import google.generativeai as genai
import time
import re
import sqlite3
import uuid
import datetime
import json

# -------------------------------------------------------------
# --- 0. 页面配置 ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="MBTI 智囊团 & 诊断", 
    page_icon="🧬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# --- 1. 数据定义 (含富豪案例) ---
# -------------------------------------------------------------

# 定义16型人格及其对应的白手起家富豪/名人代表
MBTI_DATA = {
    "INTJ": {
        "name": "建筑师 (Architect)", 
        "desc": "富有想象力和战略性的思想家，一切皆在计划之中。",
        "billionaires": ["Elon Musk (特斯拉/SpaceX)", "Mark Zuckerberg (Meta)", "Reed Hastings (Netflix)"],
        "icon": "🏰"
    },
    "INTP": {
        "name": "逻辑学家 (Logician)", 
        "desc": "具有创造力的发明家，对知识有不竭的渴望。",
        "billionaires": ["Larry Page (Google)", "Sergey Brin (Google)", "Paul Allen (Microsoft)"],
        "icon": "⚗️"
    },
    "ENTJ": {
        "name": "指挥官 (Commander)", 
        "desc": "大胆，富有想象力且意志强大的领导者。",
        "billionaires": ["Steve Jobs (Apple)", "Gordon Ramsay (餐饮帝国)", "Carl Icahn (投资大亨)"],
        "icon": "🎬"
    },
    "ENTP": {
        "name": "辩论家 (Debater)", 
        "desc": "聪明好奇的思想者，不会放弃任何智力上的挑战。",
        "billionaires": ["Steve Wozniak (Apple)", "Richard Branson (Virgin)", "Ray Dalio (桥水基金)"],
        "icon": "🗣️"
    },
    "INFJ": {
        "name": "提倡者 (Advocate)", 
        "desc": "安静而神秘，同时鼓舞人心且不知疲倦的理想主义者。",
        "billionaires": ["Oprah Winfrey (媒体大亨)", "Brian Chesky (Airbnb)", "J.K. Rowling (哈利波特系列)"], # Rowling是作家富豪
        "icon": "🕯️"
    },
    "INFP": {
        "name": "调停者 (Mediator)", 
        "desc": "诗意，善良的利他主义者，总是热情地为正当理由提供帮助。",
        "billionaires": ["George Lucas (星球大战)", "Tim Sweeney (Epic Games)", "Peter Jackson (指环王导演)"],
        "icon": "🍃"
    },
    "ENFJ": {
        "name": "主人公 (Protagonist)", 
        "desc": "富有魅力，鼓舞人心的领导者，有能力使听众着迷。",
        "billionaires": ["Sheryl Sandberg (Meta前COO)", "Howard Schultz (星巴克)", "Masayoshi Son (软银)"],
        "icon": "⚔️"
    },
    "ENFP": {
        "name": "竞选者 (Campaigner)", 
        "desc": "热情，富有创造力，爱社交的自由人。",
        "billionaires": ["Walt Disney (迪士尼)", "Brian Chesky (Airbnb)", "Kelly Ripa (媒体)"],
        "icon": "🎉"
    },
    "ISTJ": {
        "name": "物流师 (Logistician)", 
        "desc": "实际，注重事实的个人，可靠性不容怀疑。",
        "billionaires": ["Jeff Bezos (Amazon)", "Ingvar Kamprad (IKEA)", "Warren Buffett (伯克希尔)"],
        "icon": "📋"
    },
    "ISFJ": {
        "name": "守卫者 (Defender)", 
        "desc": "非常专注而温暖的守护者，时刻准备着保护爱着的人们。",
        "billionaires": ["Kim Kardashian (SKIMS)", "Kanye West (Yeezy)", "Kate Middleton (皇室/影响力)"], # 此类型富豪较少，多为公众人物
        "icon": "🛡️"
    },
    "ESTJ": {
        "name": "总经理 (Executive)", 
        "desc": "出色的管理者，在管理事情或人的方面无与伦比。",
        "billionaires": ["John D. Rockefeller (石油大亨)", "Martha Stewart (生活方式)", "Ivanka Trump (商业)"],
        "icon": "👔"
    },
    "ESFJ": {
        "name": "执政官 (Consul)", 
        "desc": "极有同情心，爱社交，受欢迎的人们。",
        "billionaires": ["Sam Walton (Walmart)", "Andrew Carnegie (钢铁大亨)", "Whitney Wolfe Herd (Bumble)"],
        "icon": "🤝"
    },
    "ISTP": {
        "name": "鉴赏家 (Virtuoso)", 
        "desc": "大胆而实际的实验家，擅长使用所有形式的工具。",
        "billionaires": ["Jack Dorsey (Twitter/Block)", "James Dyson (戴森)", "Tom Anderson (MySpace)"],
        "icon": "🔧"
    },
    "ISFP": {
        "name": "探险家 (Adventurer)", 
        "desc": "灵活，有魅力的艺术家，时刻准备着探索和体验新鲜事物。",
        "billionaires": ["Rihanna (Fenty Beauty)", "Steven Spielberg (导演)", "Jony Ive (Apple设计)"],
        "icon": "🎨"
    },
    "ESTP": {
        "name": "企业家 (Entrepreneur)", 
        "desc": "聪明，精力充沛，善于感知的人们，真心享受生活在边缘。",
        "billionaires": ["Donald Trump (地产)", "Madonna (娱乐帝国)", "Richard Branson (Virgin - 也有视为ENTP)"],
        "icon": "🚀"
    },
    "ESFP": {
        "name": "表演者 (Entertainer)", 
        "desc": "自发的，精力充沛而热情的表演者。",
        "billionaires": ["Magic Johnson (商业帝国)", "Richard Branson (Virgin)", "Tony Robbins (商业教练)"],
        "icon": "💃"
    }
}

# -------------------------------------------------------------
# --- 2. CSS 样式 (保持原有风格 + 新增卡片样式) ---
# -------------------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    * { box-sizing: border-box; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #f4f7f9 !important;
        font-family: 'Noto Sans SC', sans-serif !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    .main .block-container { padding-top: 0 !important; max-width: 100% !important; }

    /* Nav Bar */
    .nav-bar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 15px 40px;
        position: sticky; top: 0; z-index: 999;
        display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .logo-text { font-size: 1.2rem; font-weight: 700; color: #6a5acd; }
    .nav-tag { background-color: #f0e6ff; color: #6a5acd; font-size: 0.75rem; padding: 4px 8px; border-radius: 4px; margin-left: 12px; }

    /* Hero */
    .hero-section { padding: 30px 20px; text-align: left; max-width: 900px; margin: 0 auto; }
    .page-title { font-size: 2rem !important; font-weight: 700 !important; color: #1a1a1a; margin: 0; }
    .subtitle { font-size: 1rem; color: #666; margin-top: 5px; }

    /* Chat Styling */
    .chat-container { max-width: 900px; margin: 0 auto; padding: 0 20px; }
    [data-testid="stChatMessage"] { background: transparent !important; padding: 10px 0 !important; }
    [data-testid="stChatMessage"] > div:first-child { display: none !important; }
    
    .chat-row { display: flex; margin-bottom: 20px; width: 100%; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    
    .chat-avatar { width: 36px; height: 36px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
    .assistant .chat-avatar { background-color: #6a5acd; color: white; margin-right: 12px; }
    .user .chat-avatar { background-color: #9370db; color: white; margin-left: 12px; order: 2; }
    
    .chat-bubble { padding: 16px 20px; border-radius: 8px; font-size: 0.95rem; line-height: 1.6; max-width: 85%; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .assistant .chat-bubble { background-color: white; border: 1px solid #e0e0e0; color: #333; }
    .user .chat-bubble { background-color: #6a5acd; color: white; }

    /* Billionaire Card */
    .billionaire-box {
        background: linear-gradient(135deg, #fff 0%, #f3f0ff 100%);
        border: 1px solid #dcdfe6;
        border-left: 5px solid #6a5acd;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .b-title { font-size: 0.9rem; font-weight: 700; color: #6a5acd; text-transform: uppercase; margin-bottom: 10px; }
    .b-list { display: flex; gap: 15px; flex-wrap: wrap; }
    .b-item { background: rgba(255,255,255,0.8); padding: 8px 12px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 0.9rem; font-weight: 500; color: #333; display: flex; align-items: center; }
    .b-icon { margin-right: 6px; }

    /* Input & Buttons */
    [data-testid="stChatInput"] { background: white; border-top: 1px solid #e0e0e0; }
    div.stButton > button { border-radius: 6px; border: 1px solid #dcdfe6; transition: all 0.2s; }
    div.stButton > button:hover { border-color: #6a5acd; color: #6a5acd; background: #f0e6ff; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 3. 核心逻辑函数 ---
# -------------------------------------------------------------

def clean_extra_newlines(text):
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def markdown_to_html(text):
    """简易渲染，移除Markdown符号"""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) # Bold
    lines = text.split('\n')
    html = ""
    for line in lines:
        if line.strip():
            html += f"<p style='margin-bottom:8px;'>{line}</p>"
    return html

def stream_gemini_response(prompt, model):
    try:
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.01)
    except Exception as e:
        yield f"⚠️ 连接中断: {str(e)[:50]}..."

def diagnose_user_mbti(user_desc, api_key):
    """
    使用 Gemini 快速分析用户描述并返回 MBTI 代码
    """
    if not api_key: return None
    
    diagnosis_model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    作为MBTI专家，请根据用户的自我描述，判断其最可能属于哪一种MBTI 16型人格。
    用户描述: "{user_desc}"
    
    请严格只返回4个字母的MBTI代码（例如 INTJ, ENFP）。不要有任何其他解释或标点符号。
    """
    try:
        response = diagnosis_model.generate_content(prompt)
        mbti_code = response.text.strip().upper()
        # 简单清洗，确保只包含字母
        match = re.search(r'[IE][NS][TF][JP]', mbti_code)
        if match:
            return match.group(0)
        return None
    except:
        return None

# -------------------------------------------------------------
# --- 4. 初始化 ---
# -------------------------------------------------------------

gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
st.session_state["api_configured"] = bool(gemini_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏选择逻辑
with st.sidebar:
    st.title("🧩 人格控制台")
    
    # === 1. 手动选择 ===
    selected_mbti_code = st.selectbox(
        "选择对话人格",
        options=list(MBTI_DATA.keys()),
        index=0
    )
    
    st.markdown("---")
    
    # === 2. 快速诊断模块 ===
    st.subheader("🔮 不知道类型？")
    with st.expander("AI 快速诊断", expanded=True):
        st.markdown("<small style='color:#666'>简单描述你的行事风格、能量来源或决策方式：</small>", unsafe_allow_html=True)
        user_desc = st.text_area("描述自己...", height=80, placeholder="例：我喜欢独处，做决定时很理智，喜欢按计划行事...")
        
        if st.button("开始分析", use_container_width=True):
            if not user_desc:
                st.warning("请先输入描述")
            elif not gemini_api_key:
                st.error("API Key 未配置")
            else:
                with st.spinner("Gemini 正在分析你的性格特征..."):
                    detected_code = diagnose_user_mbti(user_desc, gemini_api_key)
                    if detected_code:
                        st.session_state["auto_selected_mbti"] = detected_code
                        st.success(f"诊断结果：**{detected_code}**")
                        time.sleep(1)
                        st.rerun() # 刷新页面以应用选择
                    else:
                        st.error("无法判断，请尝试更详细的描述。")

    # 处理自动跳转
    if "auto_selected_mbti" in st.session_state:
        selected_mbti_code = st.session_state.pop("auto_selected_mbti")
    
    # 状态管理：如果人格变了，清空历史
    if "last_mbti" not in st.session_state:
        st.session_state.last_mbti = selected_mbti_code
    
    if st.session_state.last_mbti != selected_mbti_code:
        st.session_state.messages = []
        st.session_state.last_mbti = selected_mbti_code
        st.rerun()

    if st.button("🗑️ 清空当前对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 获取当前数据
current_persona = MBTI_DATA[selected_mbti_code]

# 构建模型
SYSTEM_PROMPT = f"""
你现在是 {current_persona['name']} ({selected_mbti_code})。
性格特征：{current_persona['desc']}。
请完全沉浸在这个人格中与用户对话。你的思考方式、语气和价值观必须符合该人格的设定。
"""
@st.cache_resource
def get_model(sys_prompt):
    if not gemini_api_key: return None
    return genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_prompt)

gemini_model = get_model(SYSTEM_PROMPT)

# -------------------------------------------------------------
# --- 5. 页面主体 ---
# -------------------------------------------------------------

# 顶部导航
st.markdown("""
<div class="nav-bar">
    <div class="logo-text">🧬 MBTI Chat</div>
    <div class="nav-tag">AI Persona</div>
</div>
""", unsafe_allow_html=True)

# Hero 区域
st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hero-section">
    <h1 class="page-title">与 {current_persona['name']} 对话</h1>
    <div class="subtitle">{current_persona['icon']} {current_persona['desc']}</div>
</div>
""", unsafe_allow_html=True)

# === 功能点 2：白手起家富豪展示区 ===
billionaires_html = "".join([
    f'<div class="b-item"><span class="b-icon">💰</span>{name}</div>' 
    for name in current_persona['billionaires']
])

st.markdown(f"""
<div class="chat-container">
    <div class="billionaire-box">
        <div class="b-title">该人格类型的代表性亿万富豪 / 企业家</div>
        <div class="b-list">
            {billionaires_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 聊天记录区域
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(f"""
    <div class="chat-row assistant">
        <div class="chat-avatar">{current_persona['icon']}</div>
        <div class="chat-bubble"><b>{selected_mbti_code}</b> 在线。我们可以聊聊创业、生活或者任何你感兴趣的话题。</div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "assistant"
    avatar = "👤" if msg["role"] == "user" else current_persona['icon']
    content_html = markdown_to_html(msg["content"])
    st.markdown(f"""
    <div class="chat-row {role_class}">
        <div class="chat-avatar">{avatar}</div>
        <div class="chat-bubble">{content_html}</div>
    </div>
    """, unsafe_allow_html=True)

# 输入框
user_input = st.chat_input(f"向 {selected_mbti_code} 提问...")

if user_input and st.session_state.get("api_configured"):
    # 显示用户输入
    st.markdown(f"""
    <div class="chat-row user">
        <div class="chat-avatar">👤</div>
        <div class="chat-bubble">{markdown_to_html(user_input)}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 生成回复
    resp_placeholder = st.empty()
    full_resp = ""
    
    for chunk in stream_gemini_response(user_input, gemini_model):
        full_resp += chunk
        resp_placeholder.markdown(f"""
        <div class="chat-row assistant">
            <div class="chat-avatar">{current_persona['icon']}</div>
            <div class="chat-bubble">{markdown_to_html(full_resp)}<span style="color:#6a5acd;font-weight:bold">|</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    # 完成状态
    resp_placeholder.markdown(f"""
    <div class="chat-row assistant">
        <div class="chat-avatar">{current_persona['icon']}</div>
        <div class="chat-bubble">{markdown_to_html(full_resp)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": full_resp})

st.markdown('</div></div>', unsafe_allow_html=True) # End chat-container & main-wrapper

# -------------------------------------------------------------
# --- 6. 访客统计 (隐藏在底部) ---
# -------------------------------------------------------------
# (保持原有数据库逻辑)
DB_FILE = "visit_stats.db"
def track_stats():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS visitors (id TEXT PRIMARY KEY)''')
        if "vid" not in st.session_state: st.session_state.vid = str(uuid.uuid4())
        c.execute("INSERT OR IGNORE INTO visitors (id) VALUES (?)", (st.session_state.vid,))
        conn.commit()
        c.execute("SELECT COUNT(*) FROM visitors")
        count = c.fetchone()[0]
        conn.close()
        return count
    except: return 0

uv = track_stats()
st.markdown(f"<div style='text-align:center;color:#ccc;font-size:12px;margin-top:50px;'>Total Visitors: {uv}</div>", unsafe_allow_html=True)

```
