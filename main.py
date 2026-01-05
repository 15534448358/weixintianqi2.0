import random
import requests  # 【新增此行】必须导入整个requests模块，异常处理才有效
from time import localtime
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os
import time     # 【新增此行】确保time模块已导入，用于time.sleep()

 
def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)
 
 
def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token
 
 
def get_weather(region):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    
    weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    weather_params = {
        'key': key,
        'city': region,
        'extensions': 'all',
        'output': 'json'
    }
    
    # 重试配置
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # 请求天气API
            response = get(weather_url, params=weather_params, headers=headers, timeout=10)
            weather_data = response.json()
            
            if weather_data["status"] != "1":
                error_info = weather_data.get('info', '未知错误')
                print(f"API返回业务错误: {error_info}")
                # 如果是最后一次尝试，跳出循环，执行最后的降级返回
                if attempt == max_retries - 1:
                    break
                else:
                    print(f"第 {attempt+1} 次尝试失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
            
            # 解析预报数据
            forecasts = weather_data.get("forecasts", [])
            if not forecasts:
                print("未找到天气预报信息")
                if attempt == max_retries - 1:
                    break
                else:
                    print(f"第 {attempt+1} 次尝试失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                    
            casts = forecasts[0].get("casts", [])
            if len(casts) < 2:
                print("天气预报数据不足")
                if attempt == max_retries - 1:
                    break
                else:
                    print(f"第 {attempt+1} 次尝试失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
            
            # 今天天气（索引0）
            today_weather = casts[0]
            # 明天天气（索引1）
            tomorrow_weather = casts[1]
            
            # 提取今天天气信息
            today_weather_text = today_weather["dayweather"]  # 白天天气现象
            today_temp = f"{today_weather['nighttemp']}~{today_weather['daytemp']}°C"  # 温度范围
            today_wind_dir = today_weather.get("daywind", "未知") + "风"
            
            # 提取明天天气信息
            tomorrow_weather_text = tomorrow_weather["dayweather"]  # 白天天气现象
            tomorrow_temp = f"{tomorrow_weather['nighttemp']}~{tomorrow_weather['daytemp']}°C"  # 温度范围
            tomorrow_wind_dir = tomorrow_weather.get("daywind", "未知") + "风"
            
            print(f"获取到天气信息: 今天 {today_weather_text}/{today_temp}/{today_wind_dir}, 明天 {tomorrow_weather_text}/{tomorrow_temp}/{tomorrow_wind_dir}")
            
            return today_weather_text, today_temp, today_wind_dir, tomorrow_weather_text, tomorrow_temp, tomorrow_wind_dir
            
        except requests.exceptions.Timeout:
            print(f"第 {attempt+1} 次请求超时，{retry_delay}秒后重试...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，天气信息获取失败")
                break  # 跳出循环，执行最后的降级返回
                
        except requests.exceptions.ConnectionError:
            print(f"第 {attempt+1} 次连接错误，{retry_delay}秒后重试...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，天气信息获取失败")
                break
                
        except Exception as e:
            print(f"第 {attempt+1} 次请求出现异常: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，天气信息获取失败")
                break
    
    # 【关键修改】如果所有重试都失败，或遇到业务错误，则返回一组安全的默认值
    print("警告：天气信息获取失败，启用降级方案。")
    return "数据更新中", "N/A", "N/A", "数据更新中", "N/A", "N/A"


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的今年对应的月和日
        try:
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
        birthday_month = birthday.month
        birthday_day = birthday.day
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
 
    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day
 
 
def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    r = get(url, headers=headers)
    note_en = r.json()["content"]
    note_ch = r.json()["note"]
    return note_ch, note_en
 
 
def send_message(to_user, access_token, region_name, today_weather, today_temp, today_wind_dir, tomorrow_weather, tomorrow_temp, tomorrow_wind_dir, note_ch, note_en):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取在一起的日子的日期格式
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "region": {
                "value": region_name,
                "color": get_color()
            },
            "today_weather": {
                "value": today_weather,
                "color": get_color()
            },
            "today_temp": {
                "value": today_temp,
                "color": get_color()
            },
            "today_wind_dir": {
                "value": today_wind_dir,
                "color": get_color()
            },
            "tomorrow_weather": {
                "value": tomorrow_weather,
                "color": get_color()
            },
            "tomorrow_temp": {
                "value": tomorrow_temp,
                "color": get_color()
            },
            "tomorrow_wind_dir": {
                "value": tomorrow_wind_dir,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            }
        }
    }
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": get_color()}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)
 
 
if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)

    # 获取accessToken
    accessToken = get_access_token()
    # 接收的用户
    users = config["user"]
    # 传入地区获取天气信息
    region = config["region"]
    # 修改这里：接收6个返回值
    today_weather, today_temp, today_wind_dir, tomorrow_weather, tomorrow_temp, tomorrow_wind_dir = get_weather(region)
    
    note_ch = config["note_ch"]
    note_en = config["note_en"]
    if note_ch == "" and note_en == "":
        # 获取词霸每日金句
        note_ch, note_en = get_ciba()
# 公众号推送消息
for user in users:
    send_message(user, accessToken, region, today_weather, today_temp, today_wind_dir, tomorrow_weather, tomorrow_temp, tomorrow_wind_dir, note_ch, note_en)

# 替换掉原来的 os.system("pause")
print("\n程序执行完毕。")
if sys.platform.startswith('win'):
    # 如果是Windows系统，使用pause
    os.system("pause")
else:
    # 如果是Linux/Mac等系统，使用input等待回车
    input("按回车键退出...")
