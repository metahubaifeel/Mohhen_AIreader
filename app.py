import streamlit as st
import PyPDF2
import io
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置页面
st.set_page_config(
    page_title="墨痕AI阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 + 文本选中菜单和悬浮卡片样式
st.markdown("""
<style>
.main {
    padding-top: 2rem;
}
.sidebar .sidebar-content {
    padding-top: 2rem;
}
.highlight-text {
    background-color: #ffeb3b;
    padding: 2px 4px;
    border-radius: 3px;
}
.annotation-text {
    border-left: 3px solid #4caf50;
    padding-left: 10px;
    margin: 5px 0;
    background-color: #f5f5f5;
}
.qa-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    background-color: #fafafa;
}
.paragraph-container {
    border: 1px solid #f0f0f0;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
    transition: box-shadow 0.3s;
}
.paragraph-container:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    margin: 2px;
}
.badge-highlight {
    background-color: #fff3cd;
    color: #856404;
}
.badge-annotation {
    background-color: #d4edda;
    color: #155724;
}
.badge-qa {
    background-color: #cce5ff;
    color: #004085;
}

/* 文本选中浮动菜单样式 */
.selection-menu {
    position: absolute;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 8px;
    z-index: 1000;
    display: none;
}

.selection-menu button {
    background: #f8f9fc;
    border: 1px solid #e1e5e9;
    border-radius: 4px;
    padding: 6px 12px;
    margin: 0 2px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
}

.selection-menu button:hover {
    background: #e9ecef;
    border-color: #adb5bd;
}

/* 悬浮AI问答卡片样式 */
.floating-qa-card {
    position: fixed;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    padding: 20px;
    z-index: 1001;
    max-width: 400px;
    width: 90vw;
    max-height: 500px;
    overflow-y: auto;
    display: none;
}

.floating-qa-card .close-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #f8f9fa;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.floating-qa-card .qa-input {
    width: 100%;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 10px;
    resize: vertical;
    min-height: 60px;
}

.floating-qa-card .qa-submit {
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    cursor: pointer;
    transition: background 0.2s;
}

.floating-qa-card .qa-submit:hover {
    background: #0056b3;
}

.floating-qa-card .qa-loading {
    text-align: center;
    padding: 20px;
    color: #666;
}

.floating-qa-card .qa-answer {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 15px;
    margin-top: 10px;
    line-height: 1.6;
}
</style>

<script>
let selectionMenu = null;
let floatingCard = null;
let selectedText = '';
let selectionRect = null;

// 监听文本选中事件
document.addEventListener('selectionchange', function() {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    
    if (text && text.length > 0) {
        selectedText = text;
        try {
            const range = selection.getRangeAt(0);
            selectionRect = range.getBoundingClientRect();
            showSelectionMenu();
        } catch(e) {
            console.log('获取选区位置失败:', e);
        }
    } else {
        hideSelectionMenu();
        selectedText = '';
    }
});

// 显示选中文本菜单
function showSelectionMenu() {
    hideSelectionMenu(); // 先隐藏现有菜单
    
    selectionMenu = document.createElement('div');
    selectionMenu.className = 'selection-menu';
    selectionMenu.innerHTML = `
        <button onclick="highlightText()">🟡 高亮</button>
        <button onclick="annotateText()">🖍️ 标注</button>
        <button onclick="askAI()">❓ 问一问</button>
    `;
    
    // 计算菜单位置
    const menuWidth = 180;
    const menuHeight = 40;
    let left = selectionRect.right + 5;
    let top = selectionRect.top - 5;
    
    // 边界检查
    if (left + menuWidth > window.innerWidth) {
        left = selectionRect.left - menuWidth - 5;
    }
    if (top < 0) {
        top = selectionRect.bottom + 5;
    }
    
    selectionMenu.style.left = left + window.scrollX + 'px';
    selectionMenu.style.top = top + window.scrollY + 'px';
    selectionMenu.style.display = 'block';
    
    document.body.appendChild(selectionMenu);
    
    // 点击其他地方隐藏菜单
    setTimeout(() => {
        document.addEventListener('click', hideMenuOnClickOutside);
    }, 100);
}

// 隐藏选中菜单
function hideSelectionMenu() {
    if (selectionMenu) {
        selectionMenu.remove();
        selectionMenu = null;
        document.removeEventListener('click', hideMenuOnClickOutside);
    }
}

// 点击外部区域隐藏菜单
function hideMenuOnClickOutside(e) {
    if (selectionMenu && !selectionMenu.contains(e.target)) {
        hideSelectionMenu();
    }
}

// 高亮文本功能
function highlightText() {
    if (selectedText) {
        // 通过placeholder查找对应的输入框
        const highlightInput = parent.document.querySelector('input[placeholder="高亮文本"]');
        if (highlightInput) {
            highlightInput.value = selectedText;
            highlightInput.dispatchEvent(new Event('input', { bubbles: true }));
            highlightInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        hideSelectionMenu();
    }
}

// 标注文本功能
function annotateText() {
    if (selectedText) {
        const annotation = prompt('请输入标注内容:');
        if (annotation && annotation.trim()) {
            // 通过placeholder查找对应的输入框
            const textInput = parent.document.querySelector('input[placeholder="标注文本"]');
            const annotationInput = parent.document.querySelector('input[placeholder="标注内容"]');
            if (textInput && annotationInput) {
                textInput.value = selectedText;
                textInput.dispatchEvent(new Event('input', { bubbles: true }));
                annotationInput.value = annotation.trim();
                annotationInput.dispatchEvent(new Event('input', { bubbles: true }));
                annotationInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
        hideSelectionMenu();
    }
}

// AI问答功能
function askAI() {
    if (selectedText) {
        showFloatingQACard();
        hideSelectionMenu();
    }
}

// 显示悬浮问答卡片
function showFloatingQACard() {
    hideFloatingCard(); // 先隐藏现有卡片
    
    floatingCard = document.createElement('div');
    floatingCard.className = 'floating-qa-card';
    floatingCard.innerHTML = `
        <button class="close-btn" onclick="hideFloatingCard()">×</button>
        <div style="margin-bottom: 15px; font-weight: bold; color: #333;">
            💬 AI问答助手
        </div>
        <div style="margin-bottom: 10px; font-size: 14px; color: #666;">
            选中文本: "${selectedText.substring(0, 50)}${selectedText.length > 50 ? '...' : ''}"
        </div>
        <textarea class="qa-input" placeholder="请输入您的问题（已自动填入选中文本作为上下文）" id="qaInput">${selectedText}</textarea>
        <button class="qa-submit" onclick="submitQuestion()">提交问题</button>
        <div id="qaResult"></div>
    `;
    
    // 计算卡片位置
    let left = selectionRect.right + 10;
    let top = selectionRect.top;
    
    // 边界检查
    if (left + 400 > window.innerWidth) {
        left = Math.max(10, selectionRect.left - 410);
    }
    if (top + 300 > window.innerHeight) {
        top = Math.max(10, window.innerHeight - 510);
    }
    
    floatingCard.style.left = left + window.scrollX + 'px';
    floatingCard.style.top = top + window.scrollY + 'px';
    floatingCard.style.display = 'block';
    
    document.body.appendChild(floatingCard);
}

// 隐藏悬浮卡片
function hideFloatingCard() {
    if (floatingCard) {
        floatingCard.remove();
        floatingCard = null;
    }
}

// 提交问题
function submitQuestion() {
    const input = document.getElementById('qaInput');
    const question = input.value.trim();
    const resultDiv = document.getElementById('qaResult');
    
    if (!question) {
        alert('请输入问题');
        return;
    }
    
    // 显示加载状态
    resultDiv.innerHTML = '<div class="qa-loading">🤖 AI正在思考中...</div>';
    
    // 通过placeholder查找对应的输入框
    const questionInput = parent.document.querySelector('input[placeholder="AI问题"]');
    const contextInput = parent.document.querySelector('input[placeholder="问题上下文"]');
    if (questionInput && contextInput) {
        questionInput.value = question;
        questionInput.dispatchEvent(new Event('input', { bubbles: true }));
        contextInput.value = selectedText;
        contextInput.dispatchEvent(new Event('input', { bubbles: true }));
        contextInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
}
</script>
""", unsafe_allow_html=True)

# 初始化session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    if 'reading_position' not in st.session_state:
        st.session_state.reading_position = 0
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 16
    if 'highlights' not in st.session_state:
        st.session_state.highlights = []
    if 'annotations' not in st.session_state:
        st.session_state.annotations = []
    if 'qa_history' not in st.session_state:
        st.session_state.qa_history = []
    if 'folders' not in st.session_state:
        st.session_state.folders = {"测试文件夹": []}
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

# 用户认证
def authenticate():
    st.title("🔐 墨痕AI阅读器 - 登录")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 请输入您的登录信息")
        
        username = st.text_input("用户名", placeholder="demo@mohhen.com")
        password = st.text_input("密码", type="password", placeholder="mohhen123")
        
        if st.button("登录", use_container_width=True):
            if username == "demo@mohhen.com" and password == "mohhen123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("登录成功！正在跳转...")
                st.rerun()
            else:
                st.error("用户名或密码错误！")
        
        st.info("📝 测试账号：demo@mohhen.com\n🔑 测试密码：mohhen123")

# PDF文本提取
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        st.error(f"PDF解析失败: {str(e)}")
        return None

# AI问答功能
def ask_ai(question, context=""):
    try:
        from openai import OpenAI
        
        # 获取DeepSeek API密钥
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your-deepseek-api-key-here":
            return "⚠️ 请先配置DeepSeek API密钥。在Streamlit Cloud部署时需要在环境变量中设置DEEPSEEK_API_KEY。"
        
        # 初始化DeepSeek客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：{question}

请简洁明了地回答问题，如果文档内容不足以回答问题，请说明。"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except ImportError:
        return "❌ openai库未安装，请检查依赖。"
    except Exception as e:
        return f"AI回答失败: {str(e)}"

# 文件上传和管理
def file_management():
    st.sidebar.title("📁 文件管理")
    
    # 文件上传
    uploaded_file = st.sidebar.file_uploader(
        "上传PDF文件", 
        type=['pdf'],
        help="支持上传PDF格式文件"
    )
    
    if uploaded_file is not None:
        # 修复：使用文件名和大小判断是否已存在，避免重复添加
        file_exists = any(
            f['name'] == uploaded_file.name and 
            len(f['content']) == len(uploaded_file.getvalue()) 
            for f in st.session_state.uploaded_files
        )
        
        if not file_exists:
            with st.spinner("正在处理PDF文件..."):
                text_content = extract_text_from_pdf(uploaded_file)
                if text_content:
                    st.session_state.uploaded_files.append({
                        'name': uploaded_file.name,
                        'content': text_content,
                        'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.sidebar.success(f"文件 {uploaded_file.name} 上传成功！")
    
    # 文件夹管理
    st.sidebar.subheader("📂 文件夹")
    folder_name = "测试文件夹"
    
    # 显示已上传文件
    if st.session_state.uploaded_files:
        st.sidebar.subheader("📄 已上传文件")
        for i, file_info in enumerate(st.session_state.uploaded_files):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if st.button(f"📖 {file_info['name']}", key=f"file_{i}"):
                    st.session_state.current_file = file_info
                    st.session_state.file_content = file_info['content']
                    st.session_state.reading_position = 0
            with col2:
                if st.button("📁", key=f"folder_{i}", help="添加到文件夹"):
                    if file_info not in st.session_state.folders[folder_name]:
                        st.session_state.folders[folder_name].append(file_info)
                        st.sidebar.success("已添加到文件夹")

# 阅读界面
def reading_interface():
    if not st.session_state.current_file:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h3>📚 欢迎使用墨痕AI阅读器</h3>
            <p>👈 请从左侧上传并选择一个PDF文件开始阅读</p>
            <div style='margin-top: 30px;'>
                <p><strong>功能介绍：</strong></p>
                <p>🟡 <strong>高亮</strong> - 标记重要内容</p>
                <p>🖍️ <strong>标注</strong> - 添加个人笔记</p>
                <p>❓ <strong>问一问</strong> - AI智能问答</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 阅读控制栏
    st.markdown(f"### 📖 {st.session_state.current_file['name']}")
    
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
    with col1:
        st.markdown(f"**上传时间：** {st.session_state.current_file['upload_time']}")
    
    with col2:
        st.session_state.font_size = st.selectbox(
            "字体大小", 
            [12, 14, 16, 18, 20, 24], 
            index=2,
            key="font_selector"
        )
    
    with col3:
        total_highlights = len(st.session_state.highlights)
        st.metric("高亮数量", total_highlights)
    
    with col4:
        total_annotations = len(st.session_state.annotations)
        st.metric("标注数量", total_annotations)
    
    with col5:
        total_qa = len(st.session_state.qa_history)
        st.metric("问答数量", total_qa)
    
    # 分割文本为段落以便选择
    content = st.session_state.file_content
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 20]
    
    # 显示阅读进度
    st.progress(min(st.session_state.reading_position / len(paragraphs), 1.0))
    st.markdown("---")
    
    # 使用更简单可靠的方式：通过查询参数或会话状态处理选中文本操作
    
    # 检查URL参数中是否有选中文本操作
    query_params = st.experimental_get_query_params()
    
    if 'highlight' in query_params:
        text = query_params['highlight'][0]
        if text and text not in [h['text'] for h in st.session_state.highlights]:
            st.session_state.highlights.append({
                'text': text,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"✅ 已高亮: {text[:50]}...")
            # 清除查询参数
            st.experimental_set_query_params()
    
    # 添加隐藏的输入框用于接收前端操作
    col_hidden1, col_hidden2, col_hidden3 = st.columns(3)
    with col_hidden1:
        highlight_input = st.text_input("", key="js_highlight", label_visibility="collapsed", placeholder="高亮文本")
        if highlight_input and highlight_input not in [h['text'] for h in st.session_state.highlights]:
            st.session_state.highlights.append({
                'text': highlight_input,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"✅ 已高亮选中文本")
            st.session_state.js_highlight = ""
            st.rerun()
    
    with col_hidden2:
        annotate_input = st.text_input("", key="js_annotate", label_visibility="collapsed", placeholder="标注文本")
        annotation_content = st.text_input("", key="js_annotation_content", label_visibility="collapsed", placeholder="标注内容")
        if annotate_input and annotation_content:
            st.session_state.annotations.append({
                'text': annotate_input,
                'annotation': annotation_content,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success(f"✅ 已添加标注")
            st.session_state.js_annotate = ""
            st.session_state.js_annotation_content = ""
            st.rerun()
    
    with col_hidden3:
        ai_question_input = st.text_input("", key="js_ai_question", label_visibility="collapsed", placeholder="AI问题")
        ai_context_input = st.text_input("", key="js_ai_context", label_visibility="collapsed", placeholder="问题上下文")
        if ai_question_input and ai_context_input:
            with st.spinner("🤖 AI正在分析中..."):
                answer = ask_ai(ai_question_input, ai_context_input)
                st.session_state.qa_history.append({
                    'question': ai_question_input,
                    'answer': answer,
                    'context': ai_context_input,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                # 显示AI回答在悬浮卡片中
                st.components.v1.html(f"""
                <script>
                // 更新悬浮卡片中的回答
                function updateFloatingAnswer() {{
                    const resultDiv = document.getElementById('qaResult');
                    if (resultDiv) {{
                        resultDiv.innerHTML = `
                            <div class="qa-answer">
                                <div style="font-weight: bold; margin-bottom: 8px;">🤖 AI回答:</div>
                                <div>{answer.replace("'", "\\'").replace('"', '\\"')}</div>
                            </div>
                        `;
                    }}
                }}
                // 延迟执行，确保DOM已加载
                setTimeout(updateFloatingAnswer, 100);
                </script>
                """, height=0)
            st.session_state.js_ai_question = ""
            st.session_state.js_ai_context = ""
            st.rerun()
    
    # 隐藏这些输入框
    st.markdown("""
    <style>
    /* 隐藏用于JS通信的输入框 */
    div[data-testid="column"]:has(input[placeholder="高亮文本"]) input,
    div[data-testid="column"]:has(input[placeholder="标注文本"]) input,
    div[data-testid="column"]:has(input[placeholder="标注内容"]) input,
    div[data-testid="column"]:has(input[placeholder="AI问题"]) input,
    div[data-testid="column"]:has(input[placeholder="问题上下文"]) input {
        position: absolute !important;
        left: -9999px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    /* 隐藏包含这些输入框的列 */
    div[data-testid="column"]:has(input[placeholder="高亮文本"]),
    div[data-testid="column"]:has(input[placeholder="标注文本"]),
    div[data-testid="column"]:has(input[placeholder="AI问题"]) {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 显示文本内容
    for i, paragraph in enumerate(paragraphs):
        # 检查段落是否有相关标记
        is_highlighted = any(h['text'] == paragraph for h in st.session_state.highlights)
        has_annotation = any(a['text'] == paragraph for a in st.session_state.annotations)
        has_qa = any(qa['context'] == paragraph for qa in st.session_state.qa_history)
        
        # 创建段落容器
        with st.container():
            # 状态标记
            status_badges = ""
            if is_highlighted:
                status_badges += '<span class="status-badge badge-highlight">🟡 已高亮</span>'
            if has_annotation:
                status_badges += '<span class="status-badge badge-annotation">🖍️ 有标注</span>'
            if has_qa:
                status_badges += '<span class="status-badge badge-qa">❓ 有问答</span>'
            
            if status_badges:
                st.markdown(status_badges, unsafe_allow_html=True)
            
            # 段落文本 - 根据是否高亮应用不同样式
            paragraph_class = "highlight-text" if is_highlighted else ""
            st.markdown(
                f'<div class="paragraph-container"><div class="{paragraph_class}" style="font-size: {st.session_state.font_size}px; line-height: 1.8;">{paragraph}</div></div>', 
                unsafe_allow_html=True
            )
            
            # 显示相关标注
            if has_annotation:
                for annotation in st.session_state.annotations:
                    if annotation['text'] == paragraph:
                        st.markdown(
                            f'<div class="annotation-text">📝 <strong>标注:</strong> {annotation["annotation"]} <em>({annotation["timestamp"]})</em></div>',
                            unsafe_allow_html=True
                        )
            
            # 操作按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
            
            with col1:
                if st.button("🟡", key=f"highlight_{i}", help="高亮段落", disabled=is_highlighted):
                    st.session_state.highlights.append({
                        'text': paragraph,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("✅ 已高亮！")
                    st.rerun()
            
            with col2:
                if st.button("🖍️", key=f"annotate_{i}", help="添加标注"):
                    # 使用弹窗方式添加标注
                    annotation_modal = st.empty()
                    with annotation_modal.container():
                        with st.expander("✍️ 添加标注", expanded=True):
                            annotation_text = st.text_area(
                                "请输入标注内容:", 
                                key=f"ann_input_{i}",
                                height=100
                            )
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("保存标注", key=f"save_ann_{i}"):
                                    if annotation_text.strip():
                                        st.session_state.annotations.append({
                                            'text': paragraph,
                                            'annotation': annotation_text.strip(),
                                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                                        })
                                        st.success("✅ 标注已保存！")
                                        annotation_modal.empty()
                                        st.rerun()
                            with col_b:
                                if st.button("取消", key=f"cancel_ann_{i}"):
                                    annotation_modal.empty()
            
            with col3:
                if st.button("❓", key=f"ask_{i}", help="向AI提问"):
                    with st.spinner("🤖 AI正在分析文档..."):
                        answer = ask_ai(f"请解释和分析这段文字的主要内容：{paragraph[:200]}...", paragraph)
                        st.session_state.qa_history.append({
                            'question': f"关于：{paragraph[:50]}...",
                            'answer': answer,
                            'context': paragraph,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    
                    # 显示问答卡片
                    with st.expander(f"💬 AI回答 - {datetime.now().strftime('%H:%M')}", expanded=True):
                        st.markdown('<div class="qa-card">', unsafe_allow_html=True)
                        st.markdown(f"**📝 问题：** {paragraph[:100]}...")
                        st.markdown(f"**🤖 AI回答：**")
                        st.write(answer)
                        
                        # 支持对回答进行二次提问
                        with st.expander("继续提问", expanded=False):
                            follow_up = st.text_input("继续提问:", key=f"followup_{i}")
                            if st.button("提交问题", key=f"followup_btn_{i}") and follow_up:
                                with st.spinner("🤖 AI正在回答追问..."):
                                    follow_answer = ask_ai(follow_up, f"原文：{paragraph}\n\n之前的回答：{answer}")
                                    st.markdown("**🔄 追问：**")
                                    st.write(follow_up)
                                    st.markdown("**🤖 AI回答：**")
                                    st.write(follow_answer)
                                    
                                    # 保存追问到历史
                                    st.session_state.qa_history.append({
                                        'question': follow_up,
                                        'answer': follow_answer,
                                        'context': f"追问基于：{paragraph[:50]}...",
                                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                                    })
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            
            # 更新阅读位置
            if i > st.session_state.reading_position:
                st.session_state.reading_position = i

# 侧边栏状态显示
def sidebar_status():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 阅读统计")
    
    # 显示统计信息
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📄 总文件", len(st.session_state.uploaded_files))
        st.metric("🟡 高亮", len(st.session_state.highlights))
    with col2:
        st.metric("🖍️标注", len(st.session_state.annotations))
        st.metric("❓ 问答", len(st.session_state.qa_history))
    
    # 显示文件夹内容
    if st.session_state.folders["测试文件夹"]:
        st.sidebar.markdown("### 📁 测试文件夹")
        for file_info in st.session_state.folders["测试文件夹"]:
            if st.sidebar.button(f"📄 {file_info['name'][:20]}...", key=f"folder_file_{file_info['name']}"):
                st.session_state.current_file = file_info
                st.session_state.file_content = file_info['content']
                st.session_state.reading_position = 0
                st.rerun()
    
    # 显示最近的高亮内容
    if st.session_state.highlights:
        st.sidebar.markdown("### 🟡 最近高亮")
        for i, highlight in enumerate(st.session_state.highlights[-3:]):  # 显示最近3个
            with st.sidebar.expander(f"高亮 {len(st.session_state.highlights)-i}", expanded=False):
                st.write(highlight['text'][:100] + "...")
                st.caption(f"时间: {highlight['timestamp']}")
    
    # 显示最近的标注
    if st.session_state.annotations:
        st.sidebar.markdown("### 🖍️ 最近标注") 
        for i, annotation in enumerate(st.session_state.annotations[-3:]):
            with st.sidebar.expander(f"标注 {len(st.session_state.annotations)-i}", expanded=False):
                st.write(f"**内容:** {annotation['text'][:80]}...")
                st.write(f"**标注:** {annotation['annotation']}")
                st.caption(f"时间: {annotation['timestamp']}")
    
    # 显示问答历史
    if st.session_state.qa_history:
        st.sidebar.markdown("### ❓ 问答历史")
        for i, qa in enumerate(st.session_state.qa_history[-3:]):
            with st.sidebar.expander(f"问答 {len(st.session_state.qa_history)-i}", expanded=False):
                st.write(f"**问题:** {qa['question']}")
                st.write(f"**回答:** {qa['answer'][:100]}...")
                st.caption(f"时间: {qa['timestamp']}")
    
    # 导出功能
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📤 数据导出")
    
    if st.sidebar.button("导出高亮内容"):
        if st.session_state.highlights:
            export_data = "\n".join([f"• {h['text'][:100]}... ({h['timestamp']})" for h in st.session_state.highlights])
            st.sidebar.download_button(
                label="下载高亮内容",  
                data=export_data,
                file_name=f"highlights_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.sidebar.info("暂无高亮内容")
    
    if st.sidebar.button("导出标注内容"):
        if st.session_state.annotations:
            export_data = "\n\n".join([
                f"原文: {a['text'][:100]}...\n标注: {a['annotation']}\n时间: {a['timestamp']}" 
                for a in st.session_state.annotations
            ])
            st.sidebar.download_button(
                label="下载标注内容",
                data=export_data,
                file_name=f"annotations_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.sidebar.info("暂无标注内容")
    
    if st.sidebar.button("导出问答记录"):
        if st.session_state.qa_history:
            export_data = "\n\n".join([
                f"问题: {qa['question']}\n回答: {qa['answer']}\n时间: {qa['timestamp']}" 
                for qa in st.session_state.qa_history
            ])
            st.sidebar.download_button(
                label="下载问答记录",
                data=export_data,
                file_name=f"qa_history_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            st.sidebar.info("暂无问答记录")

# 主函数
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        authenticate()
        return
    
    # 主界面
    st.title("📚 墨痕AI阅读器")
    st.markdown(f"🎯 欢迎回来，**{st.session_state.username}**！开始您的智能阅读之旅")
    
    # 快速操作提示
    if not st.session_state.current_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**第一步**\n📁 上传PDF文件")
        with col2:
            st.info("**第二步**\n📖 选择文件阅读")
        with col3:
            st.info("**第三步**\n🤖 AI智能问答")
    
    # 侧边栏
    file_management()
    sidebar_status()
    
    # 主内容区域
    reading_interface()
    
    # 底部信息和功能展示
    st.markdown("---")
    
    # 功能演示区域
    if st.session_state.current_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 当前文档统计")
            content_stats = {
                "文档名称": st.session_state.current_file['name'],
                "上传时间": st.session_state.current_file['upload_time'],
                "字数统计": f"约 {len(st.session_state.file_content)} 字符",
                "段落数量": len([p for p in st.session_state.file_content.split('\n\n') if p.strip() and len(p.strip()) > 20]),
                "高亮段落": len(st.session_state.highlights),
                "标注数量": len(st.session_state.annotations),
                "问答次数": len(st.session_state.qa_history),
                "阅读进度": f"{min(st.session_state.reading_position, len([p for p in st.session_state.file_content.split('\n\n') if p.strip() and len(p.strip()) > 20]))} / {len([p for p in st.session_state.file_content.split('\n\n') if p.strip() and len(p.strip()) > 20])} 段落"
            }
            
            for key, value in content_stats.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.markdown("### 🎯 功能使用技巧")
            tips = [
                "💡 **高亮功能**: 点击段落旁的🟡按钮，重要内容一键标黄",
                "📝 **智能标注**: 点击🖍️按钮，添加个人思考和笔记",
                "🤖 **AI问答**: 点击❓按钮，让AI解释难懂的内容",
                "🔄 **嵌套提问**: 在AI回答基础上继续追问，深度理解",
                "📁 **文件管理**: 将重要文档添加到测试文件夹便于管理",
                "📤 **导出数据**: 侧边栏支持导出所有标注和问答记录"
            ]
            
            for tip in tips:
                st.markdown(tip)
    
    # 产品价值说明
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🚀 核心特色
        - ⚡ **AI驱动**: DeepSeek高性能问答
        - 📱 **云端部署**: 随时随地访问
        - 💡 **智能标注**: 知识点快速提取
        - 🔄 **嵌套问答**: 深度理解助手
        """)
    
    with col2:
        st.markdown("""
        ### 📈 适用场景
        - 📚 **学术研究**: 论文阅读分析
        - 💼 **商务办公**: 报告文档处理
        - 📖 **学习提升**: 知识点梳理
        - 🎯 **内容创作**: 素材整理分析
        """)
    
    with col3:
        st.markdown("""
        ### 💎 商业价值
        - ⏰ **提升效率**: 阅读速度提升50%
        - 🧠 **增强理解**: AI辅助深度分析
        - 📊 **知识沉淀**: 标注问答可导出
        - 🎯 **个性定制**: 根据需求精准问答
        """)
    
    # 技术支持信息
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
        <h4>🏆 墨痕AI阅读器 - 让阅读更智能</h4>
        <p>✨ <strong>技术栈:</strong> Streamlit + DeepSeek API + Python</p>
        <p>🎯 <strong>demo账号:</strong> demo@mohhen.com | mohhen123</p>
        <p>💼 <strong>商务合作:</strong> 支持私有化部署和定制开发</p>
        <p>📧 <strong>技术支持:</strong> 现已开源，支持二次开发</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
