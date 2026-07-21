import requests
from bs4 import BeautifulSoup
import csv
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://movie.douban.com/top250'
}

def fetch_page(url):
    """获取页面内容"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.encoding = 'utf-8'
    if resp.status_code == 200:
        return resp.text
    else:
        print(f"请求失败，状态码：{resp.status_code}")
        return None

def get_node_text(node, default=""):
    """通用取值工具，做空判断"""
    return node.text.strip() if node else default

def parse_movie(html):
    """解析页面，提取电影信息：排名、片名、评分、上映时间、主演、短评"""
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('.grid_view .item')
    movies = []
    for item in items:
        rank = get_node_text(item.select_one('.pic em'), "0")
        title = get_node_text(item.select_one('.title'))
        rating = get_node_text(item.select_one('.rating_num'), "0")
        quote = item.select_one('.quote')
        quote_text = get_node_text(quote)

        # 提取摘要文本（包含上映时间、导演、主演）
        info_text = get_node_text(item.select_one('.bd p:first-child'))
        release_date = ""
        actors = ""
        if info_text:
            # 匹配上映年份：开头的4位年份
            year_match = re.search(r'(\d{4})', info_text)
            if year_match:
                release_date = year_match.group(1)
            # 匹配主演：截取"主演:"后面的内容，到换行/结束为止
            actor_match = re.search(r'主演:(.*?)(?=\n|$)', info_text)
            if actor_match:
                actors = actor_match.group(1).strip()

        movies.append([rank, title, rating, release_date, actors, quote_text])
    return movies

def save_to_csv(movies, filename='douban_top250.csv'):
    """保存为CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['排名', '片名', '评分', '上映年份', '主演', '短评'])
        writer.writerows(movies)
    print(f"数据已保存至 {filename}")

def main():
    base_url = 'https://movie.douban.com/top250?start={}&filter='
    all_movies = []
    for page in range(0, 10):  # 共10页，每页25条
        start = page * 25
        url = base_url.format(start)
        print(f"正在抓取第{page+1}页...")
        html = fetch_page(url)
        if html is None:
            continue
        # 校验是否被豆瓣反爬拦截
        if "grid_view" not in html:
            print("当前页被反爬拦截，跳过本页")
            time.sleep(3)
            continue
        movies = parse_movie(html)
        all_movies.extend(movies)
        time.sleep(1.5)
    print(f"共抓取 {len(all_movies)} 部电影")
    save_to_csv(all_movies)

if __name__ == '__main__':
    main()