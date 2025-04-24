import json
import requests
import os
import time
import hashlib
from datetime import datetime, timedelta
from openai import OpenAI
from PIL import Image
from io import BytesIO
from tavily import TavilyClient
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 创建OpenAI客户端
client = OpenAI(
    base_url="https://api-inference.modelscope.cn/v1/",
    api_key= os.getenv("DASHSCOPE_API_KEY")
)

# 对话历史
history = []

# 全局系统提示词
SYSTEM_PROMPT = """你是一个专业的电影推荐专家。请按照以下规则推荐电影：

1. 电影标题格式：请同时提供中文标题和英文标题，格式为"中文标题(英文标题)"。例如：盗梦空间(Inception)、流浪地球(The Wandering Earth)。必须使用英文括号，不要使用中文括号。

2. 响应格式：返回JSON格式的推荐结果，包含以下字段：
   - title: 电影标题（中英文格式）
   - genre: 电影类型
   - year: 上映年份
   - description: 电影详细描述（用中文，内容要详尽，足够支持创建海报）
   - reason: 推荐理由（用中文，内容详细，不要简单回复，切勿剧透）
   - rating: 评分

3. 语言要求：所有描述和推荐理由必须使用中文。

4. 详细程度：电影描述和推荐理由应当详尽，提供足够信息，但不要透露关键剧情。
"""

# 搜索相关配置
CACHE_DIR = "tavily_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_messages_with_history(user_prompt):
    """获取包含系统提示和历史记录的完整消息列表"""
    # 始终以系统提示开始
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 添加历史对话记录
    if history:
        messages.extend(history)
        print(f"【调试信息】历史记录已读取: 当前有 {len(history)} 条历史消息")
    else:
        print("【调试信息】历史记录为空，这是新对话")
    
    # 添加当前用户提示
    messages.append({"role": "user", "content": user_prompt})
    
    return messages

# 添加消息到历史记录
def add_to_history(role, content):
    """将新消息添加到对话历史"""
    # 系统消息不添加到历史记录中
    if role != "system":
        history.append({"role": role, "content": content})
        # 截断内容以避免打印过长
        content_preview = content[:50] + "..." if len(content) > 50 else content
        print(f"【调试信息】已添加到历史记录: {role} - {content_preview}")
    
    # 保持历史记录在合理长度，避免过长
    if len(history) > 10:  # 保留最近的5轮对话(10条消息)
        removed = history.pop(0)
        removed_preview = removed["content"][:30] + "..." if len(removed["content"]) > 30 else removed["content"]
        print(f"【调试信息】历史记录已满，删除最早消息: {removed['role']} - {removed_preview}")
        
        if history:  # 确保还有消息可以删除
            removed = history.pop(0)
            removed_preview = removed["content"][:30] + "..." if len(removed["content"]) > 30 else removed["content"]
            print(f"【调试信息】保持对话完整性，删除第二条消息: {removed['role']} - {removed_preview}")

# 清空历史记录
def clear_history():
    """清空对话历史"""
    global history
    history_length = len(history)
    history = []
    print(f"【调试信息】历史记录已清空，共删除了 {history_length} 条消息")

def extract_json_content(input_str):
    """从输入字符串中提取JSON内容"""
    # 查找并删除以 ```json 开头的标记
    start_index = input_str.find('```json')
    if start_index != -1:
        input_str = input_str[start_index + len('```json'):]

    # 查找并删除以 ``` 结尾的标记
    end_index = input_str.find('```')
    if end_index != -1:
        input_str = input_str[:end_index]

    # 查找 </think> 标签的位置
    end_tag = '</think>'
    tag_end = input_str.find(end_tag)
    
    if tag_end != -1:
        # 截取标签后的内容并去除前后空白
        input_str = input_str[tag_end + len(end_tag):].strip()

    return input_str.strip()

# 创建带系统提示的对话历史
def create_messages_with_system_prompt(user_prompt):
    """创建包含系统提示的消息列表"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

def generate_image_ByAI(prompt: str) -> Image:
    """使用AI生成图像"""
    url = "https://api-inference.modelscope.cn/v1/images/generations"
    payload = {
        "model": 'MusePublic/489_ckpt_FLUX_1',  # ModelScope Model-Id
        "prompt": prompt  # The prompt for image generation
    }
    headers = {
        "Authorization": "Bearer a864d9b7-b1bc-4c1d-8ca8-35d08c6a2877",
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad responses

    response_data = response.json()
    image_url = response_data['images'][0]['url']
    image_response = requests.get(image_url)
    image_response.raise_for_status()  # Raises an HTTPError for bad responses

    image = Image.open(BytesIO(image_response.content))
    return image

def extract_english_title(movie_title):
    """从电影标题中提取英文标题 (标准括号)"""
    # 查找第一个左括号和第一个右括号的位置
    start = movie_title.find('(')
    end = movie_title.find(')', start)
    
    # 如果找到了括号，返回括号内的内容
    if start != -1 and end != -1:
        return movie_title[start+1:end]
    else:
        return ""  # 如果没有找到括号，返回空字符串

def extract_english_title2(movie_title):
    """从电影标题中提取英文标题 (中文括号)"""
    # 查找第一个左括号和第一个右括号的位置
    start = movie_title.find('（')
    end = movie_title.find('）', start)
    
    # 如果找到了括号，返回括号内的内容
    if start != -1 and end != -1:
        return movie_title[start+1:end]
    else:
        return ""  # 如果没有找到括号，返回空字符串

def get_imdb_url(movie_data):
    """获取电影的IMDb URL"""
    imdb_id = movie_data.get("imdbID")
    if imdb_id:
        imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
        return imdb_url
    else:
        return "IMDb ID not found"

def get_movie_poster(movie_name):
    """从OMDb API获取电影海报"""
    # OMDb API的URL，使用电影名称和API密钥进行查询
    apikey=os.getenv("OMDB_API_KEY")
    movie_name_en = extract_english_title(movie_name)
    movie_name_cn = extract_english_title2(movie_name)
    
    # 确保 movie_name_en 不为空
    if movie_name_en:
        movie_name = movie_name_en
    elif movie_name_cn:
        movie_name = movie_name_cn
    else:
        movie_name = movie_name.split('(')[0].strip()  # 如果没有英文标题，使用中文标题
    
    # 修改为使用完整的电影名称格式
    movie_name = movie_name.replace(" ", "+")
    
    print("电影名称是：", movie_name)
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={apikey}"
    
    # 发送GET请求
    response = requests.get(url)
    
    # 检查请求是否成功
    if response.status_code == 200:
        data = response.json()
        
        # 检查API返回的数据是否包含海报信息
        if data.get("Response") == "True":
            poster_url = data.get("Poster")  # 获取海报URL
            imdb_url = get_imdb_url(data)  # 获取IMDb URL
            print("成功获取海报和IMDb URL！")
            return poster_url or "N/A", imdb_url
        else:
            print(f"未找到电影 {movie_name} 的海报或其他信息。")
            return "N/A", "无法找到电影网址，请重试"
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return "N/A", "无法找到电影网址，请重试"

def show_movie_poster(poster_url):
    """显示电影海报"""
    if poster_url == "N/A":
        return None
    try:
        # 请求海报图像
        response = requests.get(poster_url)
        
        # 检查请求是否成功
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save("poster.jpg")  # 保存图像
            return img
        else:
            print(f"无法下载图像，HTTP 状态码：{response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("网络连接不可达，无法下载图像。")
        return None
    except Exception as e:
        print(f"下载或展示图像时发生错误: {e}")
        return None

# ----- 新增Tavily搜索功能 -----

class MovieSearchEngine:
    """电影搜索引擎类，使用Tavily API"""
    
    def __init__(self, api_key=None):
        """
        初始化电影搜索引擎
        
        参数:
            api_key: Tavily API密钥。如果为None，则尝试从环境变量获取
        """
        self.api_key = os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("必须提供Tavily API密钥，通过参数或TAVILY_API_KEY环境变量")
        
        self.client = TavilyClient(api_key=self.api_key)
        
        # 缓存配置
        self.use_cache = True  # 是否使用缓存
        self.cache_duration = {
            "recent": 24,    # 最新电影信息缓存24小时
            "classic": 168   # 经典电影信息缓存7天(168小时)
        }
    
    def search(self, query, max_results=5):
        """
        使用Tavily API进行通用搜索
        
        参数:
            query: 用户输入的查询字符串
            max_results: 最大结果数
        
        返回:
            dict: 包含搜索结果的信息
        """
        # 尝试从缓存获取
        if self.use_cache:
            cache_key = self._generate_cache_key(query)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                print(f"[Tavily] 使用缓存结果: '{query}'")
                return cached_result
        
        try:
            print(f"[Tavily] 正在搜索: '{query}'")
            response = self.client.search(
                query=query,
                search_type="search",
                max_results=max_results
            )
            formatted_result = self.format_results(response)
            
            # 保存到缓存
            if self.use_cache:
                self._save_to_cache(cache_key, formatted_result)
                
            return formatted_result
        except Exception as e:
            print(f"[错误] Tavily搜索失败: {str(e)}")
            return {
                "error": True,
                "message": f"搜索失败: {str(e)}"
            }

    def format_results(self, search_result):
        """
        格式化搜索结果
        
        参数:
            search_result: Tavily搜索结果
        
        返回:
            dict: 格式化后的搜索信息
        """
        if "error" in search_result:
            return search_result

        formatted_results = {
            "results": []
        }

        for result in search_result.get("results", []):
            formatted_results["results"].append({
                "title": result.get("title", "未知"),
                "content": result.get("content", "无内容"),
                "url": result.get("url", "无链接")
            })

        return formatted_results
    
    def _generate_cache_key(self, query):
        """生成缓存键"""
        # 对查询进行哈希处理
        hash_obj = hashlib.md5(query.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _get_cache_path(self, cache_key):
        """获取缓存文件路径"""
        return os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    def _get_from_cache(self, cache_key):
        """从缓存获取结果"""
        cache_path = self._get_cache_path(cache_key)
        
        # 如果缓存文件不存在，返回None
        if not os.path.exists(cache_path):
            return None
            
        # 读取缓存文件
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01T00:00:00'))
            movie_type = cache_data.get('movie_type', 'recent')  # 默认为最新电影
            cache_hours = self.cache_duration.get(movie_type, 24)  # 默认24小时
            
            # 如果缓存已过期，返回None
            if datetime.now() - cache_time > timedelta(hours=cache_hours):
                print(f"[Tavily] 缓存已过期: {cache_key}")
                return None
                
            return cache_data.get('data')
        except Exception as e:
            print(f"[Tavily] 读取缓存失败: {str(e)}")
            return None
    
    def _save_to_cache(self, cache_key, data, movie_type='recent'):
        """保存结果到缓存"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # 创建缓存数据结构
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'movie_type': movie_type,  # 电影类型决定缓存时长
                'data': data
            }
            
            # 写入缓存文件
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            print(f"[Tavily] 已保存到缓存: {cache_key}")
        except Exception as e:
            print(f"[Tavily] 保存缓存失败: {str(e)}")

# 创建全局搜索引擎实例
def get_movie_search_engine():
    """获取或创建电影搜索引擎实例"""
    try:
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if not tavily_api_key:
            print("[警告] 未找到TAVILY_API_KEY环境变量，搜索功能可能不可用")
            return None
            
        return MovieSearchEngine(api_key=tavily_api_key)
    except Exception as e:
        print(f"[错误] 创建电影搜索引擎失败: {str(e)}")
        return None

# 简便的搜索方法
def tavily_search(query, max_results=5):
    """
    使用Tavily搜索电影相关信息
    
    参数:
        query: 搜索查询
        max_results: 最大结果数
        
    返回:
        dict: 包含搜索结果的信息
    """
    engine = get_movie_search_engine()
    if not engine:
        return {
            "error": True,
            "message": "搜索引擎初始化失败，请检查TAVILY_API_KEY环境变量"
        }
        
    return engine.search(query, max_results=max_results) 