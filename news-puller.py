import anthropic
import datetime
import json
import os
import re
import requests
import select
import socket
import time
import traceback
from bs4 import BeautifulSoup

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-5-haiku-latest"

NYT_KEY = os.environ.get("NYT_KEY")
NYT_US_NEWS_URL = "https://api.nytimes.com/svc/news/v3/content/nyt/u.s.json"
NYT_PARAMS = {"api-key": NYT_KEY}
WGET_HEADERS = {
	"User-Agent": "Wget/1.21.1 (linux-gnu)"  # Use the same User-Agent as wget
}

PRIVATE_IP = '172.31.21.121'

LLM_PROMPT_INTRO = (
	"Analyze the following articles within the <text> tag about election news and output a json with one key for each item in the list. The key should be the number of the item in the list. The value should be made according to the instructions for each item. If the result cannot be confirmed for a specific item, ignore that key and omit it from the json output. Only consider an election a victory if it's EXPLICITLY confirmed. Do NOT make projections or base the answers on expectations. For example, the first two items could be {'1': 'DPRES', '2': 'DSEN'}\n"
	"1: (DPRES if Kamala wins the presidency/RPRES if Trump wins the presidency)\n"
	"2: (DSEN if Democrats win the majority of the seats in the Senate/RSEN if Republicans win the majority of the seats)\n"
	"3: (DHOUSE if Democrats win the majority of the seats in the House of Representatives/RHOUSE if Republicans win the majority)\n"
	"4: (DAL if Kamala wins the Alabama election/RAL if Trump wins)\n"
	"5: (DAK if Kamala wins the Alaska election/RAK if Trump wins)\n"
	"6: (DAZ if Kamala wins the Arizona election/RAZ if Trump wins)\n"
	"7: (DAR if Kamala wins the Arkansas election/RAR if Trump wins)\n"
	"8: (DCA if Kamala wins the California election/RCA if Trump wins)\n"
	"9: (DCO if Kamala wins the Colorado election/RCO if Trump wins)\n"
	"10: (DCT if Kamala wins the Connecticut election/RCT if Trump wins)\n"
	"11: (DDE if Kamala wins the Delaware election/RDE if Trump wins)\n"
	"12: (DFL if Kamala wins the Florida election/RFL if Trump wins)\n"
	"13: (DGA if Kamala wins the Georgia election/RGA if Trump wins)\n"
	"14: (DHI if Kamala wins the Hawaii election/RHI if Trump wins)\n"
	"15: (DID if Kamala wins the Idaho election/RID if Trump wins)\n"
	"16: (DIL if Kamala wins the Illinois election/RIL if Trump wins)\n"
	"17: (DIN if Kamala wins the Indiana election/RIN if Trump wins)\n"
	"18: (DIA if Kamala wins the Iowa election/RIA if Trump wins)\n"
	"19: (DKS if Kamala wins the Kansas election/RKS if Trump wins)\n"
	"20: (DKY if Kamala wins the Kentucky election/RKY if Trump wins)\n"
	"21: (DLA if Kamala wins the Louisiana election/RLA if Trump wins)\n"
	"22: (DME if Kamala wins the Maine election/RME if Trump wins)\n"
	"23: (DMD if Kamala wins the Maryland election/RMD if Trump wins)\n"
	"24: (DMA if Kamala wins the Massachusetts election/RMA if Trump wins)\n"
	"25: (DMI if Kamala wins the Michigan election/RMI if Trump wins)\n"
	"26: (DMN if Kamala wins the Minnesota election/RMN if Trump wins)\n"
	"27: (DMS if Kamala wins the Mississippi election/RMS if Trump wins)\n"
	"28: (DMO if Kamala wins the Missouri election/RMO if Trump wins)\n"
	"29: (DMT if Kamala wins the Montana election/RMT if Trump wins)\n"
	"30: (DNE if Kamala wins the Nebraska election/RNE if Trump wins)\n"
	"31: (DNV if Kamala wins the Nevada election/RNV if Trump wins)\n"
	"32: (DNH if Kamala wins the New Hampshire election/RNH if Trump wins)\n"
	"33: (DNJ if Kamala wins the New Jersey election/RNJ if Trump wins)\n"
	"34: (DNM if Kamala wins the New Mexico election/RNM if Trump wins)\n"
	"35: (DNY if Kamala wins the New York election/RNY if Trump wins)\n"
	"36: (DNC if Kamala wins the North Carolina election/RNC if Trump wins)\n"
	"37: (DND if Kamala wins the North Dakota election/RND if Trump wins)\n"
	"38: (DOH if Kamala wins the Ohio election/ROH if Trump wins)\n"
	"39: (DOK if Kamala wins the Oklahoma election/ROK if Trump wins)\n"
	"40: (DOR if Kamala wins the Oregon election/ROR if Trump wins)\n"
	"41: (DPA if Kamala wins the Pennsylvania election/RPA if Trump wins)\n"
	"42: (DRI if Kamala wins the Rhode Island election/RRI if Trump wins)\n"
	"43: (DSC if Kamala wins the South Carolina election/RSC if Trump wins)\n"
	"44: (DSD if Kamala wins the South Dakota election/RSD if Trump wins)\n"
	"45: (DTN if Kamala wins the Tennessee election/RTN if Trump wins)\n"
	"46: (DTX if Kamala wins the Texas election/RTX if Trump wins)\n"
	"47: (DUT if Kamala wins the Utah election/RUT if Trump wins)\n"
	"48: (DVT if Kamala wins the Vermont election/RVT if Trump wins)\n"
	"49: (DVA if Kamala wins the Virginia election/RVA if Trump wins)\n"
	"50: (DWA if Kamala wins the Washington election/RWA if Trump wins)\n"
	"51: (DWV if Kamala wins the West Virginia election/RWV if Trump wins)\n"
	"52: (DWI if Kamala wins the Wisconsin election/RWI if Trump wins)\n"
	"53: (DWY if Kamala wins the Wyoming election/RWY if Trump wins)\n"
	"54: (1W1 if Baldwin wins the Senate election in Wisconsin/2WI if Hovde wins)\n"
	"55: (1TX if Cruz wins the Senate election in Texas/2TX if Allred wins)\n"
	"56: (1OH if Moreno wins the Senate election in Ohio/2OH if Brown wins)\n"
	"57: (1NE if Fischer wins the Senate election in Nebraska/2NE if Osborn wins)\n"
	"58: (1MT if Sheehy wins the Senate election in Montana/2MT if Tester wins)\n"
	"59: (1NV if Rosen wins the Senate election in Nevada/2NV if Brown wins)\n"
	"60: (1MI if Slotkin wins the Senate election in Michigan/2MI if Rogers wins)\n"
	"61: (1AZ if Gallego wins the Senate election in Arizona/2AZ if Lake wins)\n"
	"62: (1PA if Casey Jr. wins the Senate election in Pennsylvania/2PA if McCormick wins)\n"
)

GNEWS_URL = "https://gnews.io/api/v4/top-headlines"
GNEWS_PARAMS = {
	"apikey": GNEWS_API_KEY,
	"category": "nation",
	"max": 3,
	"expand": "content",
	"country": "us",
	"nullable": "image,description",
	"q": "(popular vote) OR (presidential election) OR senate OR (house of representatives) OR (state election) OR (margin of victory) OR (electoral college)",
}

def printError(error):
	errorMessage = repr(error) + " encountered at " + str(time.strftime("%H:%M:%S", time.localtime()))
	print(errorMessage)

MAX_RECENT_ARTICLES = 100

TERMINAL_WIDTH = 172

NYT_API_TIMEOUT = 30
CLAUDE_API_TIMEOUT = 1.2

conns = []

def isRelevantUrl(url):
	return not ("/video" in url or "/podcasts" in url or "/crosswords" in url or "/arts" in url or "/learning" in url or "/science" in url or "/world" in url or "cooking." in url or "/business" in url or "/weather" in url or "/well" in url)

def sendSocketMessage(sock, data):
	global conns

	conn = None
	if isSocketActive(sock):
		try:
			conn, _ = sock.accept()
			conns.append(conn)
			print("------------------------ Connection accepted at " + str(datetime.datetime.now()) + " ------------------------")
		except Exception as e:
			if conn in conns:
				conns.remove(conn)
			traceback.print_exc()
			printError(e)

	for conn in conns:
		try:
			conn.sendall(data.encode())
		except Exception as e:
			conn.close()
			conns.remove(conn)
			traceback.print_exc()
			printError(e)

def isSocketActive(sock):
	# Use select to check if the socket is readable
	readable, _, _ = select.select([sock], [], [], 0)
	return bool(readable)

def runNewsPuller():
	claudeClient = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
	mostRecentGNewsArticles = []
	mostRecentNYTArticles = []

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
	sock.bind((PRIVATE_IP, 23456))
	sock.listen(1)

	elapsedGNewsTime = -1
	elapsedNYTTime = -1
	elapsedClaudeTime = -1

	while True:
		totalResponse = []
		try:
			elapsedGNewsTime = 1 if elapsedGNewsTime == -1 else time.time() - startGNews
			startGNews = time.time()
			if elapsedGNewsTime < 1:
				time.sleep(1 - elapsedGNewsTime)
			response = requests.get(GNEWS_URL, params=GNEWS_PARAMS)
			response.raise_for_status()

			for article in response.json()['articles']:
				title = article['title']
				if title not in mostRecentGNewsArticles:
					print(str(datetime.datetime.now()) + ": " + title)

					mostRecentGNewsArticles.append(title)
					if len(mostRecentGNewsArticles) > MAX_RECENT_ARTICLES:
						mostRecentGNewsArticles = mostRecentGNewsArticles[len(mostRecentGNewsArticles) - MAX_RECENT_ARTICLES:]

					totalResponse.append(article['content'])
					sendSocketMessage(sock, json.dumps({"title": title}))
					# totalResponse.append(article['title'])
		except Exception as e:
			traceback.print_exc()
			printError(e)

		try:
			elapsedNYTTime = 12 if elapsedNYTTime == -1 else time.time() - startNYT
			if elapsedNYTTime >= NYT_API_TIMEOUT:
				startNYT = time.time()
				response = requests.get(NYT_US_NEWS_URL, params=NYT_PARAMS)
				response.raise_for_status()
				for result in response.json()['results']:
					subUrl = result['url']
					if '/live' in subUrl:
						# print(subUrl)
						try:
							response = requests.get(subUrl, headers=WGET_HEADERS)
							response.raise_for_status()
							# with open(subUrl.split('/')[-1], "w") as f:
								# f.write(response.text)
							soup = BeautifulSoup(response.text, 'html.parser')
							divs = soup.find_all("div", attrs={"class": re.compile("live-blog-post css|live-blog-post pinned-post|live-blog-reporter-update")})
							for div in divs:
								cleanedDiv = div.get_text(" ", strip=True)
								divIdentifier = cleanedDiv[:TERMINAL_WIDTH]
								if divIdentifier not in mostRecentNYTArticles:
									print(str(datetime.datetime.now()) + ": " + divIdentifier)
									mostRecentNYTArticles.append(cleanedDiv[:TERMINAL_WIDTH])
									if len(mostRecentNYTArticles) > MAX_RECENT_ARTICLES:
										mostRecentNYTArticles = mostRecentNYTArticles[len(mostRecentNYTArticles) - MAX_RECENT_ARTICLES:]
									totalResponse.append(cleanedDiv)
									sendSocketMessage(sock, json.dumps({"title": divIdentifier}))
								'''
								scripts = soup.find_all("script", attrs={"data-rh": "true"})
								for script in scripts:
									print(script)
									for content in script.contents:
										print(content)
								'''
						except Exception as e:
							traceback.print_exc()
							printError(e)
					elif subUrl not in mostRecentNYTArticles and isRelevantUrl(subUrl):
						print(str(datetime.datetime.now()) + ": " + subUrl)
						try:
							response = requests.get(subUrl, headers=WGET_HEADERS)
							response.raise_for_status()
							# with open(subUrl.split('/')[-1], "w") as f:
								# f.write(response.text)
							# print(response.text)
							soup = BeautifulSoup(response.text, 'html.parser')
							mainArticles = soup.find_all("article", attrs={"id": "story"})
							for mainArticle in mainArticles:
								cleanedArticle = mainArticle.get_text(" ", strip=True)
								totalResponse.append(cleanedArticle)
								# print(cleanedArticle)
							mostRecentNYTArticles.append(subUrl)
							if len(mostRecentNYTArticles) > MAX_RECENT_ARTICLES:
								mostRecentNYTArticles = mostRecentNYTArticles[len(mostRecentNYTArticles) - MAX_RECENT_ARTICLES:]
							sendSocketMessage(sock, json.dumps({"title": subUrl}))
						except Exception as e:
							traceback.print_exc()
							printError(e)
		except Exception as e:
			traceback.print_exc()
			printError(e)

		try:
			if totalResponse:
				elapsedClaudeTime = 2 if elapsedClaudeTime == -1 else time.time() - startClaude
				if elapsedClaudeTime < CLAUDE_API_TIMEOUT:
					time.sleep(CLAUDE_API_TIMEOUT - elapsedClaudeTime)
				startClaude = time.time()
				message = claudeClient.messages.create(
					model=CLAUDE_MODEL,
					max_tokens=2048,
					messages=[
						{"role": "user", "content": LLM_PROMPT_INTRO + "<text>" + " ".join(totalResponse) + "</text>"}
					]
				)
				sendSocketMessage(sock, message.content[0].text)
				print(message.content[0].text)
		except Exception as e:
			traceback.print_exc()
			printError(e)

runNewsPuller()
