import gradio as gr
from recommendation import recommend_text, recommend_filter, recommend_fuzzy, recommend_emotional

# Gradio界面组件
def create_ui():
    with gr.Blocks(theme=gr.themes.Ocean()) as demo:
        gr.HTML("<h1 style='font-size: 24px; text-align: center;'>电影推荐官</h1>")

        with gr.Tab("文本搜索"):
            text_input = gr.Textbox(label="请输入您的推荐需求", placeholder="如'想看一部轻松的喜剧片'或'推荐一部科幻电影'")
            with gr.Row():
                genre = gr.Dropdown(["剧情", "喜剧", "动作", "恐怖", "科幻", "爱情", "悬疑", "冒险", "动画", "战争", "犯罪", "纪录", "奇幻", "家庭", "武侠"], label="电影类型")
                use_langchain = gr.Checkbox(label="使用LangChain (推荐质量更高，但速度较慢)", value=False)
            recommend_button = gr.Button("推荐", variant="primary")
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    recommend_output0 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie0_title = gr.Textbox(label="推荐电影名称")
                    movie0_rating = gr.Textbox(label="评分")
                    movie0_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie0_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output1 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie1_title = gr.Textbox(label="推荐电影名称")
                    movie1_rating = gr.Textbox(label="评分")
                    movie1_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie1_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output2 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie2_title = gr.Textbox(label="推荐电影名称")
                    movie2_rating = gr.Textbox(label="评分")
                    movie2_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie2_imdb_url = gr.Textbox(label="电影网址")
            recommend_button_feedback = gr.Button("换一个", variant="primary")
            
            def process(input_text, genre, use_langchain):
                result = recommend_text(input_text, genre, use_langchain=use_langchain)
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            def process2(text_input, genre, use_langchain):
                result = recommend_text("The user didn't like your previous recommendation. Please recommend another movie and reduce recommendations of this type in the future.", "", use_langchain=use_langchain) 
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            recommend_button.click(process, inputs=[text_input, genre, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
            recommend_button_feedback.click(process2, inputs=[text_input, genre, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
        
        with gr.Tab("多维度筛选"):
            with gr.Row():
                year_range = gr.Slider(1900, 2024, label="年代范围")
                rating_range = gr.Slider(0, 10, label="评分区间")
            genre = gr.CheckboxGroup(["动作", "喜剧", "剧情", "科幻", "恐怖", "悬疑", "惊悚", "爱情", "战争", "西部", "奇幻", "动画", "纪录片", "音乐/歌舞", "冒险", "传记", "犯罪", "家庭", "历史", "体育", "灾难", "武侠", "间谍", "真人动画"], label="电影类型")
            with gr.Row():
                is_hot = gr.Checkbox(label="热播")
                is_free = gr.Checkbox(label="免费")
                is_vip = gr.Checkbox(label="会员")
                is_paid = gr.Checkbox(label="付费")
                use_langchain = gr.Checkbox(label="使用LangChain (推荐质量更高，但速度较慢)", value=False)
            language = gr.Dropdown(["无","国语", "英语"], label="语言",value="国语")
            region = gr.Dropdown(["无","中国", "美国"], label="地区",value="中国")
            filter_button = gr.Button("筛选",variant="primary")
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    recommend_output0 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie0_title = gr.Textbox(label="推荐电影名称")
                    movie0_rating = gr.Textbox(label="评分")
                    movie0_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie0_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output1 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie1_title = gr.Textbox(label="推荐电影名称")
                    movie1_rating = gr.Textbox(label="评分")
                    movie1_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie1_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output2 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie2_title = gr.Textbox(label="推荐电影名称")
                    movie2_rating = gr.Textbox(label="评分")
                    movie2_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie2_imdb_url = gr.Textbox(label="电影网址")
            filter_button_feedback = gr.Button("换一个",variant="primary")

            def process(genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain):
                result = recommend_filter(genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain=use_langchain)
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            def process2(genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain):
                result = recommend_text("The user didn't like your previous recommendation. Please recommend another movie and reduce recommendations of this type in the future.", "", use_langchain=use_langchain) 
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            filter_button.click(fn=process, inputs=[genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
            filter_button_feedback.click(fn=process2, inputs=[genre, year_range, rating_range, is_hot, is_free, is_vip, is_paid, language, region, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])

        with gr.Tab("遗忘检索"):
            description = gr.Textbox(label="请输入电影的情节、角色或其他模糊信息", placeholder="我想找一部很久以前看过的电影，好像是关于未来世界和机器人，名字有点像《终结者》。")
            use_langchain = gr.Checkbox(label="使用LangChain (推荐质量更高，但速度较慢)", value=False)
            search_button = gr.Button("检索", variant="primary")
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    recommend_output0 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie0_title = gr.Textbox(label="推荐电影名称")
                    movie0_rating = gr.Textbox(label="评分")
                    movie0_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie0_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output1 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie1_title = gr.Textbox(label="推荐电影名称")
                    movie1_rating = gr.Textbox(label="评分")
                    movie1_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie1_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output2 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie2_title = gr.Textbox(label="推荐电影名称")
                    movie2_rating = gr.Textbox(label="评分")
                    movie2_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie2_imdb_url = gr.Textbox(label="电影网址")
            search_button_feedback = gr.Button("换一个",variant="primary")
            
            def process(description, use_langchain):
                result = recommend_fuzzy(description, use_langchain=use_langchain)
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            def process2(description, use_langchain):
                result = recommend_text("The user didn't like your previous recommendation. Please recommend another movie and reduce recommendations of this type in the future.", "", use_langchain=use_langchain) 
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            search_button.click(fn=process, inputs=[description, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
            search_button_feedback.click(fn=process2, inputs=[description, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
        
        with gr.Tab("情感交互推荐"):
            emotion = gr.Dropdown(["开心", "悲伤", "愤怒", "平静"], label="当前情绪")
            environment = gr.Dropdown(["独自一人", "与朋友", "与家人"], label="观看环境")
            location = gr.Dropdown(["家", "外地", "电影院", "公司"], label="观看地点")
            atmosphere = gr.Dropdown(["安逸", "平静", "激昂", "恐怖"], label="氛围趋势")
            use_langchain = gr.Checkbox(label="使用LangChain (推荐质量更高，但速度较慢)", value=False)
            emotional_button = gr.Button("推荐",variant="primary")
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    recommend_output0 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie0_title = gr.Textbox(label="推荐电影名称")
                    movie0_rating = gr.Textbox(label="评分")
                    movie0_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie0_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output1 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie1_title = gr.Textbox(label="推荐电影名称")
                    movie1_rating = gr.Textbox(label="评分")
                    movie1_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie1_imdb_url = gr.Textbox(label="电影网址")
                with gr.Column(scale=1, min_width=300):
                    recommend_output2 = gr.Gallery(label="推荐结果", columns=1, object_fit="contain", height="auto")
                    movie2_title = gr.Textbox(label="推荐电影名称")
                    movie2_rating = gr.Textbox(label="评分")
                    movie2_reason = gr.Textbox(label="推荐理由", lines=5)
                    movie2_imdb_url = gr.Textbox(label="电影网址")
            emotional_button_feedback = gr.Button("换一个",variant="primary")
            
            def process(emotion, environment, location, atmosphere, use_langchain):
                result = recommend_emotional(emotion, environment, location, atmosphere, use_langchain=use_langchain)
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            def process2(emotion, environment, location, atmosphere, use_langchain):
                result = recommend_text("The user didn't like your previous recommendation. Please recommend another movie and reduce recommendations of this type in the future.", "", use_langchain=use_langchain) 
                if "error" in result:
                    return [], result["error"], "", "", "", [], "", "", "", "", [], "", "", "", "", ""
                else:
                    print("顺利完成！！")
                    return [result["poster0"]], result["reason0"], result["title0"], result["rating0"], result["imdb_url0"], [result["poster1"]], result["reason1"], result["title1"], result["rating1"], result["imdb_url1"], [result["poster2"]], result["reason2"], result["title2"], result["rating2"], result["imdb_url2"]
            
            emotional_button.click(fn=process, inputs=[emotion, environment, location, atmosphere, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])
            emotional_button_feedback.click(fn=process2, inputs=[emotion, environment, location, atmosphere, use_langchain], outputs=[recommend_output0, movie0_reason, movie0_title, movie0_rating, movie0_imdb_url, recommend_output1, movie1_reason, movie1_title, movie1_rating, movie1_imdb_url, recommend_output2, movie2_reason, movie2_title, movie2_rating, movie2_imdb_url])

    return demo 