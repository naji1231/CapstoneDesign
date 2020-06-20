from flask import Flask, request, jsonify, render_template, url_for
from urllib.request import urlopen
from bs4 import BeautifulSoup
import json

application = Flask(__name__)

@application.route("/")
def hello():
    return render_template('home.html')

@application.route("/keyboard", methods=['POST'])
def keyboard():
    res = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "안녕하세요!\n처음 뵙겠습니다!\n저는 코로나 안내 챗봇 코봇이에요~~!\n반가와요~!"
                    }
                }
            ]
        }
    }
    return jsonify(res)

# 발생현황
@application.route('/presentState', methods=["POST"])
def presentState():
    html = urlopen("http://ncov.mohw.go.kr/")
    bsObject = BeautifulSoup(html, "html.parser")
    # 환자 현황판만 가져오기
    divLiveNumOuter = bsObject.find("div", class_="liveNumOuter")

    # 최종 업데이트 일자
    time = divLiveNumOuter.find("span", class_="livedate").get_text()
    time = time.split(", ")
    time = time[0] + ")"
    # 일일 확진자
    dConfirm = divLiveNumOuter.find("span", class_="data1").get_text()
    # 일일 완치자
    dCure = divLiveNumOuter.find("span", class_="data2").get_text()
    spanNumClass = divLiveNumOuter.findAll("span", class_="num")
    spanBeforeClass = divLiveNumOuter.findAll("span", class_="before")

    # 확진환자, 완치, 치료 중, 사망 
    res = []
    for snc in spanNumClass:
        res.append(snc.get_text())
    res[0] = res[0].lstrip("'(누적)''")
    # 전일대비 확진, 완치, 치료, 사망
    beforRes = []
    for sbc in spanBeforeClass:
        beforRes.append(sbc.get_text())
    beforRes[0] = beforRes[0].lstrip("전일대비 ")
    
    result=[]
    i = 0
    while i < len(res):
        result.append(res[i]+beforRes[i])
        i = i + 1
    print(result)
        
    res = {
        "version": "2.0",
        "data": {
            "time" : time,
            "dConfirm" : dConfirm,
            "dCure" : dCure,
            "confirm" : result[0],
            "clear" : result[1],
            "isolation" : result[2],
            "death" : result[3]
        }
    }
    return jsonify(res)

@application.route('/cityConfirm', methods=['POST'])
def cityConfirm():
    req = request.get_json()
    cityName = req['action']['detailParams']['my_location']['value']
    
    html = urlopen("http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=13&ncvContSeq=&contSeq=&board_id=&gubun=")
    bsObject = BeautifulSoup(html, "html.parser")
    table = bsObject.find("table", class_="num midsize")
     # 테이블 머리에서 th 열 가져오기
    # thead = table.find("thead")
     # 테이블 몸체에서 td 내용 가져오기
    tbody = table.find("tbody")

    rows = tbody.findAll("tr")
    dataTable=[]
    for row in rows:
        contentTable = []
        for cell in row.findAll(['th','td']):
            contentTable.append(cell.get_text())
        dataTable.append(contentTable)

    # dataTable 탐색
    # 인덱스가 0인 합계행은 제외, 18개 도시만 검색
    # len(dataTable) == 19
    cityNumber = 1
    while cityNumber < len(dataTable):
        if dataTable[cityNumber][0] == cityName:
            break
        else:
            cityNumber = cityNumber+1

    if cityNumber >= len(dataTable):
        res = {
            "version": "2.0",
            "data": {
                "msg":"검색이 불가능한 지역입니다...\n다시 입력해주세요!"
            }
        }
        return jsonify(res)
    
    else:
        result = []
        for n in dataTable[cityNumber]:
            result.append(n)
            
    res = {
        "version":"2.0",
        "data":{
            "city":result[0],
            "sum":result[1],
            "aboard":result[2],
            "dome":result[3],
            "confirm":result[4],
            "isolation":result[5],
            "clear":result[6],
            "death":result[7],
            "rate":result[8]
        }
    }
    return jsonify(res)
    
# 시군구 테이블 만들기
@application.route('/cityTableconfirm', methods=['POST'])
def cityTableconfirm():
    # 선별진료소 시도 찾기
    html = urlopen("https://www.mohw.go.kr/react/popup_200128_3.html")
    bsObject = BeautifulSoup(html, "html.parser")
    table = bsObject.find("tbody", class_="tb_center")

    # 병원 관련 테이블
    # 번호, 시도, 시군구, 선별진료소, 전화번호
    rows = table.findAll("tr")
    centerTable = []
    for row in rows:
        datalist = []
        for cell in row.findAll(['td','th']):
            datalist.append(cell.get_text())
        centerTable.append(datalist)

    # 확인 가능한 시도
    cityTable =[]
    i = 0
    while i < len(centerTable):
        cityTable.append(centerTable[i][1])
        i = i + 1
    
    cityTable = list(set(cityTable))
    
    answer = "검색할 수 있는 시와 도입니다!\n"
    for ci in cityTable:
        answer = answer + ci + "\n "
    
    answer = answer + "\n중에서 입력해주세요!"
    res = {
        "version":"2.0",
        "template":{
            "outputs":[
                {
                     "simpleText":{
                         "text":answer
                     }
                }
            ]
        }
    }
    return jsonify(res)

# 시군구 
@application.route('/hospitalLocalState', methods=['POST'])
def hospitalLocalState():
    req = request.get_json()
    cityName = req['action']['detailParams']['my_location']['value']
    # 선별진료소 시도 찾기
    html = urlopen("https://www.mohw.go.kr/react/popup_200128_3.html")
    bsObject = BeautifulSoup(html, "html.parser")
    table = bsObject.find("tbody", class_="tb_center")

    # 병원 관련 테이블
    # 번호, 시도, 시군구, 선별진료소, 전화번호
    rows = table.findAll("tr")
    centerTable = []
    for row in rows:
        datalist = []
        for cell in row.findAll(['td','th']):
            datalist.append(cell.get_text())
        centerTable.append(datalist)

    # 확인 가능한 시군구
    localTable = []
    i = 0
    while i < len(centerTable):
        if centerTable[i][1] == cityName:
            localTable.append(centerTable[i][2])
        i = i + 1

    localTable = list(set(localTable))
    
    answer = "검색 가능한 시군구 리스트입니다!\n"
    for i in localTable:
        answer = answer + i + "\n"
    answer = answer + "에서 골라주세요!"

    res = {
        "version":"2.0",
        "template":{
            "outputs":[
                {
                     "simpleText":{
                         "text":answer
                     }
                }
            ]
        }
    }
    return jsonify(res)

# 선별진료소 리스트 케로셀로 출력하기
@application.route('/selcethos', methods=['POST'])
def selcethos():
    req = request.get_json()
    cityName = req['action']['detailParams']['my_location']['value']
    localName = req['action']['detailParams']['sys_location']['value']
    # 선별진료소 시도 찾기
    html = urlopen("https://www.mohw.go.kr/react/popup_200128_3.html")
    bsObject = BeautifulSoup(html, "html.parser")
    table = bsObject.find("tbody", class_="tb_center")

    # 이미지 url 리스트
    mapUrlList = []

    # 병원 관련 테이블
    # 번호, 시도, 시군구, 선별진료소, 전화번호
    rows = table.findAll("tr")
    centerTable = []
    for row in rows:
        datalist = []
        for cell in row.findAll(['td','th']):
            datalist.append(cell.get_text())
        centerTable.append(datalist)

    finalList = []
    i = 0
    while i < len(centerTable):
        url = "https://mohw.go.kr/react/ncov_map_page.jsp?hospitalCd=03"
        regionName = "&region="
        townName = "&town="
        hospitalNm= "&hospitalNm="
        if cityName == centerTable[i][1]:
            if localName == centerTable[i][2]:
                finalList.append(centerTable[i][1:5])
                regionName = regionName + centerTable[i][1]
                townName = townName + centerTable[i][2]
                hospitalNm = hospitalNm + centerTable[i][3]
                url = url + regionName + townName + hospitalNm + "'"
                mapUrlList.append(url)
        i = i + 1
    
    if finalList == []:
        res = {
            "version":"2.0",
            "template":{
                "outputs":[
                    {
                        "simpleText":{
                            "text":"선별진료소가 없어요...ㅠㅠ\n다른지역을 검색해줘!\n"
                        }
                    }
                ]
            }
        }
        return jsonify(res)
    
    listItems = []
    i = 0
    while i < len(mapUrlList):
        listItems.append({
                "title": finalList[i][0],
                "description": finalList[i][1]+" "+finalList[i][2],
                "thumbnail":{
                    "imageUrl":"https://imymeyou-nnkki.run.goorm.io/static/img/redCross.png"
                },
                "buttons":[
                {
                    "action": "webLink",
                    "label": "지도보기",
                    "webLinkUrl":mapUrlList[i]
                }
            ]
        })
        i = i + 1

    res = {
        "version":"2.0",
        "template":{
            "outputs":[
                {
                    "simpleText": {
                        "text": "선별진료소 리스트 입니다!\n버튼을 누르면 지도로 볼 수 있어요~!\n"
                    }
                },
                {
                    "carousel":{
                        "type":"basicCard",
                        "items":listItems
                    }
                }
            ],
            "quickReplies":[
                {
                    "label":"발생 현황",
                    "action":"message",
                    "messageText":"발생 현황"
                },
                {
                    "label":"선별진료소",
                    "action":"message",
                    "messageText":"선별진료소"
                },
                {
                    "label":"대표 증상",
                    "action":"message",
                    "messageText":"대표 증상"
                },
                {
                    "label":"예방 수칙",
                    "action":"message",
                    "messageText":"예방 수칙"
                },
                {
                    "label":"자주 묻는 질문",
                    "action":"message",
                    "messageText":"자주 묻는 질문"
                }
            ]
        }
    }
    
    return jsonify(res)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
