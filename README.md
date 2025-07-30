# 墨痕AI阅读器

一个基于Streamlit的AI增强阅读器，支持PDF文档的智能阅读、标注和AI问答功能。采用DeepSeek API提供高性价比的AI问答服务。

## 功能特点

- 📚 PDF文档上传和阅读
- 🎯 文本高亮和标注功能
- 🤖 AI智能问答（基于DeepSeek API）
- 📁 简易文件夹管理
- 👤 用户认证系统
- 💡 支持嵌套问答和问答历史
- 🎨 响应式界面设计

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置API密钥：
编辑 `.env` 文件，设置你的DeepSeek API密钥：
```
DEEPSEEK_API_KEY=你的DeepSeek API密钥
```

3. 运行应用：
```bash
streamlit run app.py
```

## 测试账号

- 用户名：demo@mohhen.com
- 密码：mohhen123

## API配置说明

本项目使用DeepSeek API，具有以下优势：
- 💰 成本低廉，性价比高
- 🚀 响应速度快
- 🔧 OpenAI兼容的API格式
- 🌐 支持中文优化

获取DeepSeek API密钥：
1. 访问 https://platform.deepseek.com/
2. 注册并获取API密钥
3. 将密钥配置到环境变量中

## 部署到Streamlit Cloud

1. 将代码推送到GitHub仓库
2. 在Streamlit Cloud中连接仓库
3. 在环境变量中设置 `DEEPSEEK_API_KEY`
4. 部署完成

## 核心功能演示流程

1. **用户登录**：使用测试账号登录系统
2. **文件上传**：上传PDF文件到系统
3. **智能阅读**：
   - 调节字体大小
   - 记忆阅读位置
   - 段落化显示文本
4. **交互标注**：
   - 🟡 高亮重要内容
   - 🖍️ 添加个人标注
   - ❓ AI智能问答
5. **嵌套问答**：对AI回答进行追问
6. **文件管理**：将文件归类到测试文件夹

## 技术架构

- **前端框架**：Streamlit
- **PDF处理**：PyPDF2
- **AI引擎**：DeepSeek API
- **认证系统**：streamlit-authenticator
- **部署平台**：Streamlit Cloud

## 项目优势

✅ **快速开发**：基于Streamlit快速搭建Web界面  
✅ **成本控制**：使用DeepSeek API降低运营成本  
✅ **用户体验**：简洁直观的交互设计  
✅ **功能完整**：覆盖阅读-标注-问答全流程  
✅ **易于部署**：一键部署到云端  

## 商业化价值

- 🎯 **知识管理**：帮助用户高效处理文档
- 📈 **学习辅助**：AI问答提升理解效果
- 🔄 **工作流优化**：标注-问答-整理一体化
- 📱 **SaaS模式**：可快速扩展为付费服务