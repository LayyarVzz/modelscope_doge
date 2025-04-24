import json
import time
import os
from api_utils import (
    client, extract_json_content, get_messages_with_history, add_to_history, 
    generate_image_ByAI, get_movie_poster, show_movie_poster, 
    tavily_search
)
# 导入langchain推荐功能
import langchain_recommendation as langchain_recommender

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

# 不再需要初始化search_engine，使用api_utils中的tavily_search函数

def get_movie_recommendation(input_text, genre, search_query=None, use_langchain=False):
    """从API获取电影推荐"""
    if use_langchain:
        print("正在使用LangChain方式进行电影推荐...")
        return langchain_recommender.get_movie_recommendation_langchain(input_text, genre, search_query)
    
    # 使用普通方式推荐
    print("正在使用普通方式进行电影推荐...")
    # 使用Tavily搜索电影信息，优先使用search_query
    search_query = search_query or input_text
    
    # 使用api_utils中的tavily_search函数
    movie_info = tavily_search(search_query)
    
    # 构建用户提示词，包含Tavily搜索结果
    user_prompt = f"根据以下描述推荐三部{genre}电影：{input_text}\nTavily搜索结果：{json.dumps(movie_info, ensure_ascii=False)}\n请按照以下JSON格式返回：{MOVIE_JSON_TEMPLATE}"
    print("User prompt:", user_prompt)
    # 获取带历史记录的完整消息列表
    messages = get_messages_with_history(user_prompt)
    print(f"【调试信息】即将发送API请求，消息列表包含 {len(messages)} 条消息")
    
    # 调用 API 获取模型的响应
    response = client.chat.completions.create(
        model='deepseek-ai/DeepSeek-R1',
        messages=messages
    )

    # 获取模型的回答
    model_reply = response.choices[0].message.content
    model_reply = extract_json_content(model_reply)
    print("Model response:", model_reply)
    
    # 将模型回答添加到历史记录
    add_to_history("assistant", model_reply)

    # 解析模型返回的 JSON 数据
    try:
        movies_data = json.loads(model_reply)
        movie_info = movies_data.get("movie_recommendations", [])
        if movie_info:
            print("生成的第一部电影名字是:", movie_info[0]['title'])
        return movie_info
    except Exception as e:
        print("Error processing response:", e)
        return []

def get_movie_details(movie, index):
    """获取单部电影的详细信息，包括海报和IMDb链接"""
    title = movie.get("title", "Unknown")
    description = movie.get("description", "No description available")
    reason = movie.get("reason", "No reason available")
    rating = movie.get("rating", "N/A")
    
    # 获取海报和IMDb URL
    poster_url, imdb_url = get_movie_poster(title)
    if poster_url != "N/A":
        poster = show_movie_poster(poster_url)
    else:
        # 根据电影描述生成海报
        prompt = f"你是一位海报设计师。请根据以下电影描述生成一张海报：{description}。请在海报右下角清晰标注此图像由AI生成，非原始海报。"
        poster = generate_image_ByAI(prompt)
    
    return {
        f"title{index}": title,
        f"description{index}": description,
        f"poster{index}": poster,
        f"reason{index}": reason,
        f"rating{index}": rating,
        f"imdb_url{index}": imdb_url
    }

def recommend_text(input_text, genre, search_query=None, use_langchain=False):
    """主处理函数，整合推荐和海报功能"""
    try:
        # 将用户输入添加到历史记录
        add_to_history("user", f"我需要{genre}类型的电影推荐：{input_text}")
        
        # 获取电影推荐
        movie_info = get_movie_recommendation(input_text, genre, search_query, use_langchain)
        
        # 如果没有获取到电影信息，返回错误
        if not movie_info:
            return {"error": "没有找到符合条件的电影推荐。"}
        
        # 处理每部电影的详细信息
        result = {}
        for i, movie in enumerate(movie_info[:3]):  # 最多处理3部电影
            movie_details = get_movie_details(movie, i)
            result.update(movie_details)
        
        return result
        
    except Exception as e:
        print("Error in processing: 来自推荐的警告", e)
        return {"error": "处理推荐时出错，请重试。"}

def recommend_filter(genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain=False):
    """多维度筛选推荐函数"""
    # 如果 genre 是列表，则将其转为逗号分隔的字符串
    genre_str = ",".join(genre) if isinstance(genre, list) else genre
    input_text = (
        f"类型：{genre_str}\n"
        f"年代范围：{year_range}\n"
        f"评分区间：{rating_range}\n"
        f"热播：{'是' if is_hot else '否'}\n"
        f"免费：{'是' if is_free else '否'}\n"
        f"会员：{'是' if is_vip else '否'}\n"
        f"付费：{'是' if is_paid else '否'}\n"
        f"语言：{language}\n"
        f"地区：{region}\n"
    )
    
    # 构建适合搜索的查询
    search_query = f"热门电影 {genre_str} {language} {region} {year_range.split('-')[0]}年 推荐"
    
    return recommend_text(input_text, genre, search_query, use_langchain)

def recommend_fuzzy(description, use_langchain=False):
    """遗忘检索推荐函数"""
    input_text = f"我看过一部电影但现在忘记了。请根据以下描述帮我找到这部电影：\n{description}"
    
    # 从描述中提取关键词用于搜索
    # 简单处理：移除常见的介绍性词语，保留实质内容
    search_query = description.replace("这部电影", "").replace("记得", "").replace("好像", "").strip()
    search_query = f"电影 {search_query} 推荐"
    
    return recommend_text(input_text, '', search_query, use_langchain)

def recommend_emotional(emotion, environment, location, atmosphere, use_langchain=False):
    """情感交互推荐函数"""
    input_text = (
        f"情感：{emotion}\n"
        f"环境：{environment}\n"
        f"地点：{location}\n"
        f"氛围：{atmosphere}\n"
    )
    
    # 构建适合搜索的查询
    search_query = f"电影推荐 {emotion} {atmosphere} {location} 适合 {environment}"
    
    return recommend_text(input_text, "", search_query, use_langchain)

# 测试函数，用于比较普通方式和LangChain方式的推荐效果
def test_recommendation_methods(input_text="", genre="科幻", search_query=None):
    """
    测试和比较普通推荐和LangChain推荐方式
    
    参数:
        input_text: 用户输入
        genre: 电影类型
        search_query: 搜索查询
    """
    print("\n===== 测试普通推荐方式 =====")
    start_time = time.time()
    normal_result = get_movie_recommendation(input_text, genre, search_query, use_langchain=False)
    normal_time = time.time() - start_time
    print(f"普通推荐用时: {normal_time:.2f}秒")
    
    if normal_result:
        print(f"推荐电影数量: {len(normal_result)}")
        for i, movie in enumerate(normal_result[:3], 1):
            print(f"{i}. {movie.get('title', 'Unknown')} ({movie.get('year', 'N/A')}) - {movie.get('rating', 'N/A')}")
    else:
        print("普通推荐未返回结果")
    
    print("\n===== 测试LangChain推荐方式 =====")
    start_time = time.time()
    langchain_result = get_movie_recommendation(input_text, genre, search_query, use_langchain=True)
    langchain_time = time.time() - start_time
    print(f"LangChain推荐用时: {langchain_time:.2f}秒")
    
    if langchain_result:
        print(f"推荐电影数量: {len(langchain_result)}")
        for i, movie in enumerate(langchain_result[:3], 1):
            print(f"{i}. {movie.get('title', 'Unknown')} ({movie.get('year', 'N/A')}) - {movie.get('rating', 'N/A')}")
    else:
        print("LangChain推荐未返回结果")
    
    print("\n===== 比较结果 =====")
    print(f"普通推荐用时: {normal_time:.2f}秒, LangChain推荐用时: {langchain_time:.2f}秒")
    print(f"时间差异: {langchain_time - normal_time:.2f}秒 ({(langchain_time/normal_time if normal_time > 0 else 0)*100:.1f}%)")
    
    # 比较推荐电影的重合度
    if normal_result and langchain_result:
        normal_titles = [movie.get('title', '').lower() for movie in normal_result]
        langchain_titles = [movie.get('title', '').lower() for movie in langchain_result]
        
        common_titles = set(normal_titles) & set(langchain_titles)
        print(f"两种方式推荐的电影重合数: {len(common_titles)}/{max(len(normal_result), len(langchain_result))}")
        if common_titles:
            print(f"重合的电影: {', '.join(common_titles)}")
    
    return {
        "normal": normal_result,
        "langchain": langchain_result,
        "normal_time": normal_time,
        "langchain_time": langchain_time
    }

# 在作为独立脚本运行时，执行测试
if __name__ == "__main__":
    import sys
    
    # 如果没有提供参数，使用默认值
    input_text = sys.argv[1] if len(sys.argv) > 1 else "我想看一部有深度但不压抑的科幻电影"
    genre = sys.argv[2] if len(sys.argv) > 2 else "科幻"
    
    # 执行测试
    print(f"正在测试电影推荐功能...\n输入: '{input_text}'\n类型: '{genre}'")
    test_result = test_recommendation_methods(input_text, genre) 