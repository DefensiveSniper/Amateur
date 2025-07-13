import re  # 正则表达式模块
import requests
import os
import random
import string

def download_aweme_list(data, headers, already_download_nums, max_download_num):
    if not data:
        print("无内容，跳过。")
        return
    author = data[0]['author']['nickname']# 获取作者ID
    os.makedirs(f"./media/{author}/images", exist_ok=True)  # 创建作者视频文件夹
    os.makedirs(f"./media/{author}/videos", exist_ok=True)  # 创建作者图片文件夹
    
    nums = 0  # 初始化下载计数
    
    for i in data:
        title = i['desc'].strip().split('\n')[0] # 获取标题

        if not title:
            title = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 如果标题为空，生成随机标题
            
        title_ulti = re.sub('[\/:*?"<>|]', '', title)# 替换非法字符
        # 视频
        if i['images'] is None: #纯视频的值为none，确保不下载动图视频的音乐
            try:
                video_url = i['video']['play_addr']['url_list'][0]  # 获取视频地址
                res_video = requests.get(video_url, headers=headers).content  # 发送请求获取视频内容
                
                nums += 1 # 增加下载计数
                if nums + already_download_nums >= max_download_num:
                    print(f"已达到最大下载数量 {already_download_nums}，停止下载。")
                    break
                
                with open(f"media/{author}/videos/{title_ulti}.mp4", 'wb') as f:
                    f.write(res_video)  
                    print(f"视频: {title_ulti} 下载完成")  # 打印下载完成信息
                    continue
            except Exception as e:
                print(f"{title_ulti} 视频下载出错: {e}")
            
        # 动图
        for idx, j in enumerate(i['images']):
            try:
                gif_url = j['video']['play_addr']['url_list'][0]
                res_gif = requests.get(gif_url, headers=headers).content
                filename = f"{title_ulti}_{idx}.mp4"
                with open(f"media/{author}/videos/{filename}", 'wb') as f:
                    f.write(res_gif)
                    print(f"动图：{filename} 下载完成")
            except Exception as e:
                print(f"{title_ulti} 不是图片视频。报错信息：{e}")
        
        # 图片
        for idx, j in enumerate(i['images']):
            try:
                image_url = j['url_list'][0]
                res_image = requests.get(image_url, headers=headers).content
                filename = f"{title_ulti}_{idx}.webp"
                with open(f"media/{author}/images/{filename}", 'wb') as f:
                    f.write(res_image)
                    print(f"图片：{filename} 下载完成")
                    
            except:
                print(f"{title_ulti} 不是图片视频。报错信息：{e}")
        
        nums += 1 # 增加下载计数
        if nums + already_download_nums >= max_download_num:
            print(f"已达到最大下载数量 {already_download_nums}，停止下载。")
            break
    
    return nums  # 返回下载的视频数量