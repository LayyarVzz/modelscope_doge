# 电影推荐官

这是一个基于人工智能的电影推荐系统，可以根据用户的偏好、心情和需求推荐电影。系统支持多种推荐方式，包括文本搜索、多维度筛选、遗忘检索和情感交互推荐。

## 功能特点

- **文本搜索**：直接输入您的电影需求描述，获取相关推荐
- **多维度筛选**：按类型、年代、评分等多个维度筛选电影
- **遗忘检索**：通过模糊描述找回您记不清名字的电影
- **情感交互推荐**：根据您的情感状态和观影环境推荐合适的电影
- **LangChain切换**：可选择是否使用LangChain提供更高质量（但速度较慢）的推荐

## 安装指南

1. 克隆本仓库：
   ```
   git clone https://github.com/LayyarVzz/modelscope_doge.git
   cd movie_recommendation
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 配置API密钥：
   - 需要的API_Key放在`.env里`
   <br>
   - apikey可以去以下网站申请：
     
     - [Tavily](https://www.tavily.com/)
    
     - [DashScope](https://dashscope.com/)
       
     - [ModelScope](https://www.modelscope.cn/)
       
     - [OMDb](https://www.omdbapi.com/)
       
     
   `.env`文件内添加以下内容：
    ```
    TAVILY_API_KEY=your_tavily_api_key
    DASHSCOPE_API_KEY=your_dashscope_api_key
   ......
    ```

## 使用方法

1. 运行应用：
   ```
   gradio main.py
   
   # 或者直接运行 main.py
   ```

2. 在浏览器中打开显示的URL（通常是`http://127.0.0.1:7860/`）

3. 通过界面选择不同的推荐方式：
   - **文本搜索**：直接输入您想看什么类型的电影
   - **多维度筛选**：使用各种筛选条件精确查找电影
   - **遗忘检索**：输入您记得的电影情节或特征
   - **情感交互推荐**：根据您的情绪和环境获取推荐

## 推荐模式

系统提供两种推荐模式，可通过界面上的切换按钮选择：

- **普通模式**（默认，使用deepseek）：响应速度其实比langchain更慢，因为用了ds的思考模式
- **LangChain模式**(使用阿里云的qwen)：推荐质量不一定高，但是速度很快，而且 是API杀手

## 项目结构

- `main.py`：程序入口
- `ui.py`：用户界面实现
- `recommendation.py`：推荐功能核心实现
- `api_utils.py`：API调用和实用工具函数
- `langchain_recommendation.py`：LangChain推荐功能实现 

## 调试技巧
- 代码中存在多个调试信息提示，可以从调试信息中看到一些信息
- `recommendation.py`和`langchain_recommendation.py`文件可以单独调试，不依赖前端实现，但是没实现动态输入，所以需要手动修改代码中的输入参数，只是为了测试代码是否可以跑通
