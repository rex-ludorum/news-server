import anthropic
import json
import os
import re
import requests
from bs4 import BeautifulSoup

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_SONNET_MODEL = "claude-3-5-haiku-latest"
LLM_PROMPT_INTRO = (
	"Analyze the following articles for election news and output a list of the following items. If the result is not determined for a specific item yet, write IDK instead of the options given. Separate each item: "
	"1. If Kamala wins the presidency, write DPRES here, and if Trump wins, write RPRES here "
	"2. If Democrats win the majority of the seats in the Senate, write DSEN here, and if the Republicans win the majority, write RSEN here "
	"3. If Democrats win the majority of the seats in the House of Representatives, write DHOUSE here, and if the Republicans win the majority, write RHOUSE here "
	"4. If Kamala wins the Alabama election, write DAL here, and if Trump wins, write RAL here "
	"5. If Kamala wins the Alaska election, write DAK here, and if Trump wins, write RAK here "
	"6. If Kamala wins the Arizona election, write DAZ here, and if Trump wins, write RAZ here "
	"7. If Kamala wins the Arkansas election, write DAR here, and if Trump wins, write RAR here "
	"8. If Kamala wins the California election, write DCA here, and if Trump wins, write RCA here "
	"9. If Kamala wins the Colorado election, write DCO here, and if Trump wins, write RCO here "
	"10. If Kamala wins the Connecticut election, write DCT here, and if Trump wins, write RCT here "
	"11. If Kamala wins the Delaware election, write DDE here, and if Trump wins, write RDE here "
	"12. If Kamala wins the Florida election, write DFL here, and if Trump wins, write RFL here "
	"13. If Kamala wins the Georgia election, write DGA here, and if Trump wins, write RGA here "
	"14. If Kamala wins the Hawaii election, write DHI here, and if Trump wins, write RHI here "
	"15. If Kamala wins the Idaho election, write DID here, and if Trump wins, write RID here "
	"16. If Kamala wins the Illinois election, write DIL here, and if Trump wins, write RIL here "
	"17. If Kamala wins the Indiana election, write DIN here, and if Trump wins, write RIN here "
	"18. If Kamala wins the Iowa election, write DIA here, and if Trump wins, write RIA here "
	"19. If Kamala wins the Kansas election, write DKS here, and if Trump wins, write RKS here "
	"20. If Kamala wins the Kentucky election, write DKY here, and if Trump wins, write RKY here "
	"21. If Kamala wins the Louisiana election, write DLA here, and if Trump wins, write RLA here "
	"22. If Kamala wins the Maine election, write DME here, and if Trump wins, write RME here "
	"23. If Kamala wins the Maryland election, write DMD here, and if Trump wins, write RMD here "
	"24. If Kamala wins the Massachusetts election, write DMA here, and if Trump wins, write RMA here "
	"25. If Kamala wins the Michigan election, write DMI here, and if Trump wins, write RMI here "
	"26. If Kamala wins the Minnesota election, write DMN here, and if Trump wins, write RMN here "
	"27. If Kamala wins the Mississippi election, write DMS here, and if Trump wins, write RMS here "
	"28. If Kamala wins the Missouri election, write DMO here, and if Trump wins, write RMO here "
	"29. If Kamala wins the Montana election, write DMT here, and if Trump wins, write RMT here "
	"30. If Kamala wins the Nebraska election, write DNE here, and if Trump wins, write RNE here "
	"31. If Kamala wins the Nevada election, write DNV here, and if Trump wins, write RNV here "
	"32. If Kamala wins the New Hampshire election, write DNH here, and if Trump wins, write RNH here "
	"33. If Kamala wins the New Jersey election, write DNJ here, and if Trump wins, write RNJ here "
	"34. If Kamala wins the New Mexico election, write DNM here, and if Trump wins, write RNM here "
	"35. If Kamala wins the New York election, write DNY here, and if Trump wins, write RNY here "
	"36. If Kamala wins the North Carolina election, write DNC here, and if Trump wins, write RNC here "
	"37. If Kamala wins the North Dakota election, write DND here, and if Trump wins, write RND here "
	"38. If Kamala wins the Ohio election, write DOH here, and if Trump wins, write ROH here "
	"39. If Kamala wins the Oklahoma election, write DOK here, and if Trump wins, write ROK here "
	"40. If Kamala wins the Oregon election, write DOR here, and if Trump wins, write ROR here "
	"41. If Kamala wins the Pennsylvania election, write DPA here, and if Trump wins, write RPA here "
	"42. If Kamala wins the Rhode Island election, write DRI here, and if Trump wins, write RRI here "
	"43. If Kamala wins the South Carolina election, write DSC here, and if Trump wins, write RSC here "
	"44. If Kamala wins the South Dakota election, write DSD here, and if Trump wins, write RSD here "
	"45. If Kamala wins the Tennessee election, write DTN here, and if Trump wins, write RTN here "
	"46. If Kamala wins the Texas election, write DTX here, and if Trump wins, write RTX here "
	"47. If Kamala wins the Utah election, write DUT here, and if Trump wins, write RUT here "
	"48. If Kamala wins the Vermont election, write DVT here, and if Trump wins, write RVT here "
	"49. If Kamala wins the Virginia election, write DVA here, and if Trump wins, write RVA here "
	"50. If Kamala wins the Washington election, write DWA here, and if Trump wins, write RWA here "
	"51. If Kamala wins the West Virginia election, write DWV here, and if Trump wins, write RWV here "
	"52. If Kamala wins the Wisconsin election, write DWI here, and if Trump wins, write RWI here "
	"53. If Kamala wins the Wyoming election, write DWY here, and if Trump wins, write RWY here "
	"54. If Baldwin wins the Senate election in Wisconsin, write 1WI here, and if Hovde wins, write 2WI here "
	"55. If Cruz wins the Senate election in Texas, write 1TX here, and if Allred wins, write 2TX here "
	"56. If Moreno wins the Senate election in Ohio, write 1OH here, and if Brown wins, write 2OH here "
	"57. If Fischer wins the Senate election in Nebraska, write 1NE here, and if Osborn wins, write 2NE here "
	"58. If Sheehy wins the Senate election in Montana, write 1MT here, and if Tester wins, write 2MT here "
	"59. If Rosen wins the Senate election in Nevada, write 1NV here, and if Brown wins, write 2NV here "
	"60. If Slotkin wins the Senate election in Michigan, write 1MI here, and if Rogers wins, write 2MI here "
	"61. If Gallego wins the Senate election in Arizona, write 1AZ here, and if Lake wins, write 2AZ here "
	"62. If Casey Jr. wins the Senate election in Pennsylvania, write 1PA here, and if McCormick wins, write 2PA here "
)

GNEWS_URL = "https://gnews.io/api/v4/top-headlines"
PARAMS = {
	"apikey": GNEWS_API_KEY,
	"category": "nation",
	"max": 40,
	"expand": "content",
	"country": "us",
	"nullable": "image,description",
	"q": "(popular vote) OR (presidential election) OR senate OR (house of representatives) OR (state election) OR (margin of victory) OR (electoral college)",
}

claudeClient = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

response = requests.get(GNEWS_URL, params=PARAMS)
response.raise_for_status()
totalResponse = []

# print(len(response.json()['articles']))
print(json.dumps(response.json(), indent=2))
for article in response.json()['articles']:
	totalResponse.append(article['content'])

message = claudeClient.messages.create(
	model=CLAUDE_SONNET_MODEL,
	max_tokens=2048,
	messages=[
		# {"role": "user", "content": "Read the following articles and output 1 if they indicate the Republicans have won the presidential election, and output 0 otherwise." + " ".join(totalResponse)}
		{"role": "user", "content": LLM_PROMPT_INTRO + " ".join(totalResponse)}
	]
)
print(message.content)

exit()

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
