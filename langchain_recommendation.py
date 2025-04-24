from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
import json
import html

# 从api_utils导入系统提示词和历史记录管理函数
from api_utils import SYSTEM_PROMPT, add_to_history, get_messages_with_history, clear_history


# 电影推荐JSON格式模板
MOVIE_JSON_TEMPLATE = """
{
  "movie_recommendations": [
    {
      "title": "电影标题",
      "genre": "电影类型",
      "year": "年份",
      "description": "电影描述",
      "reason": "推荐理由",
      "rating": "评分"
    },
    {
      "title": "电影标题",
      "genre": "电影类型",
      "year": "年份",
      "description": "电影描述",
      "reason": "推荐理由",
      "rating": "评分"
    },
    {
      "title": "电影标题",
      "genre": "电影类型",
      "year": "年份",
      "description": "电影描述",
      "reason": "推荐理由",
      "rating": "评分"
    }
  ]
}
"""

def init_langchain():
    """初始化langchain环境和工具"""
    # 加载.env文件中的环境变量
    load_dotenv()

    # 获取API密钥
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not dashscope_api_key:
        print("警告：未找到DASHSCOPE_API_KEY环境变量，请确保已正确设置")
        return None, None

    if not tavily_api_key:
        print("警告：未找到TAVILY_API_KEY环境变量，请确保已正确设置")
        print("请在.env文件中添加您的Tavily API密钥：TAVILY_API_KEY=your_api_key_here")
        return None, None

    print(f"使用通义千问API密钥：{dashscope_api_key[:5]}...{dashscope_api_key[-5:] if len(dashscope_api_key) > 10 else ''}")
    print(f"使用Tavily API密钥：{tavily_api_key[:5]}...{tavily_api_key[-5:] if len(tavily_api_key) > 10 else ''}")

    # 设置Tavily API环境变量
    os.environ["TAVILY_API_KEY"] = tavily_api_key

    # 创建Tavily搜索工具
    search_tool = TavilySearchResults(max_results=3)

    # 创建LLM
    llm = ChatOpenAI(
        api_key=dashscope_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
    )
    
    # 创建Agent
    tools = [search_tool]
    
    # 将系统提示词和Langchain的指令结合
    combined_system_prompt = f"""{SYSTEM_PROMPT}

此外，作为一个严谨的电影推荐助手：
- 已知信息足够时请直接回答
- 需要最新数据时使用搜索工具
- 请确保回答严格按照指定的JSON格式返回
"""
    
    # Agent提示模板 - 使用集成的系统提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", combined_system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])
    
    # 创建Agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return llm, agent_executor

def get_movie_recommendation_langchain(input_text, genre, search_query=None):

    
    # 初始化LangChain工具
    llm, agent_executor = init_langchain()
    
    if not llm or not agent_executor:
        return []
    
    # 使用搜索查询（如果提供）或输入文本
    query = search_query or input_text
    
    # 构建提示词，包含要求返回JSON格式
    prompt = f"""我需要{genre}类型的电影推荐：{input_text}
    
请根据以上描述推荐三部电影，并严格按照以下JSON格式返回。
注意：电影标题必须同时包含中文和英文，格式为"中文标题(英文标题)"，并使用英文括号。
所有描述和推荐理由必须使用中文，内容详细且不要透露关键剧情。

搜索关键词：{query}

请返回以下格式的JSON：
{MOVIE_JSON_TEMPLATE}"""
    
    try:
        # 获取包含历史记录的完整消息列表（用于调试目的）
        history_messages = get_messages_with_history(prompt)
        history_count = len(history_messages) - 2  # 减去系统消息和当前用户消息
        
        # 使用Agent获取回答
        print(f"【LangChain】发送到LangChain的提示词：{prompt[:100]}...")
        agent_response = agent_executor.invoke({"input": prompt})
        response_text = agent_response["output"]
        
        # 添加模型回复到历史记录
        print(f"【LangChain】接收到模型回复，长度：{len(response_text)} 字符")
        add_to_history("assistant", response_text)
        
        # 尝试从回答中提取JSON
        movie_recommendations = extract_movie_json(response_text)
        
        # 验证推荐结果的格式
        if movie_recommendations:
            for movie in movie_recommendations:
                # 确保电影标题符合要求的格式
                if 'title' in movie and '(' not in movie['title']:
                    # 尝试修复标题格式
                    title = movie['title']
                    if 'genre' in movie and movie['genre']:
                        movie['title'] = f"{title}({title})"  # 如果没有英文标题，重复使用标题
                    print(f"【LangChain】警告：电影标题不符合中英文格式要求，已自动修复：{title} -> {movie['title']}")
                    
                # 确保每个字段都有值
                for field in ['description', 'reason', 'rating', 'year', 'genre']:
                    if field not in movie or not movie[field]:
                        movie[field] = "未提供" if field != 'rating' else "N/A"
                        print(f"【LangChain】警告：电影推荐缺少{field}字段，已自动填充默认值")
            
            print(f"【LangChain】成功提取电影推荐: {len(movie_recommendations)} 部电影")
        else:
            print("【LangChain】未能提供有效的电影推荐")
            # 仍将响应添加到历史记录，但标记为解析失败
            add_to_history("system", "【注意】LangChain响应解析失败，未能提取有效电影推荐")
            
        return movie_recommendations
    except Exception as e:
        error_msg = f"LangChain推荐过程中出错: {e}"
        print(f"【LangChain】{error_msg}")
        # 记录错误到历史记录
        add_to_history("system", f"【错误】{error_msg}")
        return []

def extract_movie_json(text):
    """从文本中提取JSON格式的电影推荐"""
    try:
        # 查找 ```json 或 ``` 标记
        json_block_start = text.find("```json")
        if json_block_start != -1:
            # 从 ```json 后开始
            start_idx = text.find("\n", json_block_start) + 1
            end_idx = text.find("```", start_idx)
            if end_idx != -1:
                json_str = text[start_idx:end_idx].strip()
                result = json.loads(json_str)
                print(f"【LangChain】成功从代码块提取JSON数据")
                return result.get("movie_recommendations", [])
        
        # 如果没有找到 ```json 标记，尝试找普通的 JSON 对象
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            # 提取可能的JSON字符串
            json_str = text[start_idx:end_idx]
            try:
                result = json.loads(json_str)
                # 检查是否包含 movie_recommendations 字段
                if "movie_recommendations" in result:
                    print(f"【LangChain】成功从文本中提取movie_recommendations字段")
                    return result.get("movie_recommendations", [])
                
                # 如果没有包含 movie_recommendations 字段，但是包含电影属性，
                # 说明整个返回就是一个电影数组，可能需要包装
                if isinstance(result, list) and len(result) > 0:
                    # 检查列表中的对象是否看起来像电影（包含title字段）
                    if all("title" in item for item in result):
                        print(f"【LangChain】找到电影列表数组，包含 {len(result)} 部电影")
                        return result
                
                # 如果result本身看起来像一部电影（包含title字段），则返回作为单个电影
                if isinstance(result, dict) and "title" in result:
                    print(f"【LangChain】找到单部电影信息: {result.get('title', '未知')}")
                    return [result]
                
                # 如果找不到已知格式，打印调试信息并尝试进一步处理
                print(f"【LangChain】警告：JSON结果未包含movie_recommendations字段。尝试进一步解析。")
                print(f"【LangChain】JSON数据结构: {list(result.keys()) if isinstance(result, dict) else '非字典'}")
                
                # 尝试在结果中查找任何包含电影数据的字段
                for key, value in result.items() if isinstance(result, dict) else []:
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        if "title" in value[0]:
                            print(f"【LangChain】找到可能的电影列表在字段: {key}")
                            return value
            except json.JSONDecodeError:
                print(f"【LangChain】提取到的JSON字符串无法解析: {json_str[:100]}...")
                # 尝试修复常见的JSON格式问题
                fixed_str = json_str.replace("'", '"').replace("，", ",")
                try:
                    result = json.loads(fixed_str)
                    print(f"【LangChain】成功修复并解析JSON")
                    return result.get("movie_recommendations", [])
                except:
                    print(f"【LangChain】修复JSON失败，继续尝试其他方法")
                    pass  # 如果修复失败，继续尝试其他方法
        
        # 如果以上方法都失败，尝试找到可能的电影信息并手动构建结果
        print("【LangChain】未在回答中找到有效的JSON格式，尝试手动提取电影信息")
        
        # 查找可能的电影标题行
        import re
        titles = re.findall(r'(\d+\.\s*[\w\s]+[\(（][\w\s\d]+[\)）])', text)
        
        if titles:
            print(f"【LangChain】找到 {len(titles)} 个可能的电影标题")
            # 尝试从文本中提取电影信息
            movies = []
            for i, title_match in enumerate(titles):
                # 从标题行中提取标题
                title = re.sub(r'^\d+\.\s*', '', title_match).strip()
                
                # 尝试提取周围的描述和评分等信息
                start_pos = text.find(title_match)
                end_pos = text.find('\n\n', start_pos)
                if end_pos == -1:
                    end_pos = len(text)
                
                movie_section = text[start_pos:end_pos]
                
                # 尝试提取年份
                year_match = re.search(r'(\d{4}年|\(\d{4}\)|\（\d{4}\）)', movie_section)
                year = year_match.group(1).strip('()（）年') if year_match else ""
                
                # 尝试提取评分
                rating_match = re.search(r'评分[:：]\s*([\d\.]+)', movie_section)
                rating = rating_match.group(1) if rating_match else ""
                
                # 尝试提取类型
                genre_match = re.search(r'类型[:：]\s*([^，。\n]+)', movie_section)
                genre = genre_match.group(1) if genre_match else ""
                
                # 构建电影对象
                movie = {
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "genre": genre,
                    "description": "未提供详细描述",
                    "reason": "未提供推荐理由"
                }
                
                movies.append(movie)
                print(f"【LangChain】已从文本提取电影 {i+1}: {title}")
            
            if movies:
                return movies
        
        print("【LangChain】无法从回答中提取电影信息")
        return []
    except json.JSONDecodeError as e:
        print(f"【LangChain】JSON解析错误: {e}")
        return []
    except Exception as e:
        print(f"【LangChain】提取电影JSON时出错: {e}")
        return []

# 当作为独立脚本运行时的演示代码
if __name__ == "__main__":
    # 基础演示
    llm, agent_executor = init_langchain()
    
    if llm and agent_executor:
        # 清空历史记录开始新会话
        clear_history()
        print("\n==== 清空历史记录，开始新会话 ====")
        
        # 基础演示：直接使用LLM
        print("\n==== 基础模型演示 ====")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "你是谁？"}
        ]

        print("正在发送请求到阿里云通义千问...")
        response = llm.invoke(messages)
        print("收到基础模型响应:")
        print(response.content)

        # 第一次电影推荐请求
        print("\n==== 第一次电影推荐请求 ====")
        search_query = "2024年有什么特别好看的电影吗"
        print(f"问题: {search_query}")
        
        # 测试电影推荐功能
        movies1 = get_movie_recommendation_langchain(search_query, "科幻")
        if movies1:
            print("\n获取到的电影推荐:")
            for idx, movie in enumerate(movies1):
                print(f"{idx+1}. {movie.get('title', 'Unknown')}: {movie.get('description', 'No description')[:100]}...")
        else:
            print("\n没有获取到电影推荐")
        
        # 第二次电影推荐请求（测试历史记录）
        print("\n==== 第二次电影推荐请求（测试历史记录） ====")
        search_query2 = "我还想看类似的，但是评分更高的"
        print(f"问题: {search_query2}")
        
        # 测试第二次推荐（应该会使用历史记录）
        movies2 = get_movie_recommendation_langchain(search_query2, "科幻")
        if movies2:
            print("\n第二次获取到的电影推荐:")
            for idx, movie in enumerate(movies2):
                print(f"{idx+1}. {movie.get('title', 'Unknown')}: {movie.get('description', 'No description')[:100]}...")
        else:
            print("\n第二次没有获取到电影推荐")
        
        # 打印最终的历史记录状态
        history_messages = get_messages_with_history("测试历史记录状态")
        print(f"\n==== 最终历史记录状态 ====")
        print(f"历史记录中包含 {len(history_messages) - 2} 条消息")

