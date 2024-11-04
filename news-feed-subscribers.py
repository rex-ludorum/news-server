import anthropic
import os
import re
import requests
from bs4 import BeautifulSoup

NYT_KEY = os.environ.get("NYT_KEY")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_SONNET_MODEL = "claude-3-5-sonnet-20241022"

NYT_US_NEWS_URL = "https://api.nytimes.com/svc/news/v3/content/nyt/u.s.json"
PARAMS = {"api-key": NYT_KEY}
WGET_HEADERS = {
	"User-Agent": "Wget/1.21.1 (linux-gnu)"  # Use the same User-Agent as wget
}

claudeClient = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

response = requests.get(NYT_US_NEWS_URL, params=PARAMS)
response.raise_for_status()
totalResponse = []

def isRelevantUrl(url):
	return not ("/video" in url or "/podcasts" in url or "/crosswords" in url or "/arts" in url or "/learning" in url or "/science" in url or "/world" in url)

for result in response.json()['results']:
	subUrl = result['url']
	response = requests.get(subUrl, headers=WGET_HEADERS)
	response.raise_for_status()
	with open(subUrl.split('/')[-1], "w") as f:
		f.write(response.text)
	# print(response.text)
	soup = BeautifulSoup(response.text, 'html.parser')
	print(subUrl)
	if "/live" in subUrl:
		divs = soup.find_all("div", attrs={"class": re.compile("live-blog-post css|live-blog-post pinned-post|live-blog-reporter-update")})
		for div in divs:
			cleanedDiv = div.get_text(" ", strip=True)
			# print(cleanedDiv)
			totalResponse.append(cleanedDiv)
		'''
		scripts = soup.find_all("script", attrs={"data-rh": "true"})
		for script in scripts:
			print(script)
			for content in script.contents:
				print(content)
		'''
	elif isRelevantUrl(subUrl):
		mainArticles = soup.find_all("article", attrs={"id": "story"})
		# print(mainArticle)
		# print(soup.get_text(" ", strip=True))
		for mainArticle in mainArticles:
			cleanedArticle = mainArticle.get_text(" ", strip=True)
			totalResponse.append(cleanedArticle)
			print(cleanedArticle)

with open("totalResponse", "w") as f:
	for response in totalResponse:
		f.write(response)
		f.write("\n")

message = claudeClient.messages.create(
	model=CLAUDE_SONNET_MODEL,
	max_tokens=1024,
	messages=[
		{"role": "user", "content": "Read the following articles and output 1 if they indicate the Republicans have won the presidential election, and output 0 otherwise." + " ".join(totalResponse)}
	]
)
print(message.content)
