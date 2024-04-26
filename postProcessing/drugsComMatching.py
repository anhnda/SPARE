from selenium import webdriver
import time

from selenium.webdriver.chrome.service import Service

from utils import utils
from bs4 import BeautifulSoup
import params
from selenium.webdriver.common.by import By
import json
from utils.utils import getTextURL


Pref = "https://www.drugs.com/api/autocomplete/?id=livesearch-interaction&s=%s&data-autocomplete=interaction"
INTER_PREF = "https://www.drugs.com/interactions-check.php?drug_list="
RAW_DRUG_TEXT = params.DRUGSCOM_DRUG_ID_RAW
DRUG_WEB_ID_PATH = params.DRUGSCOM_DRUG_ID_WEB

PREDICTION_PATH = "%s/TopPredictedTriples.txt" % params.TMP_DIR
RAW_RES_INTER = "%s/RawDrugComResponse.dat" % params.TMP_DIR


def loadDrugList():
    r"""
    Returns:
        A list of drug names in full high quality TWOSIDES

    """
    fin = open("%s/TWOSIDES/DrugId2NameC5.txt" % params.TMP_DIR)
    drugList = []
    for line in fin.readlines():
        ss = line.strip().split("\t")
        drugList.append(ss[1].lower())
    fin.close()
    return drugList


def getRetrieveDrugURL(drugName):
    r"""

    Args:
        drugName:

    Returns:
        An URL for getting Drugs.com Id given a drug name
    """
    return Pref % drugName


def downloadDrugWebId():
    r"""
    Getting raw responses from drugs.com for mapping from drug names to drug ids
    The result is saved in RAW_DRUG_TEXT
    """

    # from selenium.webdriver.chrome.options import Options

    #options = Options()
    # options.binary_location = '/Users/anhnd/Downloads/chrome-mac-arm64/Google Chrome for Testing'
    ## this is the chromium for testing which can be downloaded from the link given below
    # service = Service('/Users/anhnd/Downloads/chrome-mac-arm64/Google Chrome for Testing')

    browser = webdriver.Chrome()


    # browser = webdriver.Chrome()

    drugList = loadDrugList()
    try:
        dDrugName2Re = utils.load_obj(RAW_DRUG_TEXT)
    except:
        dDrugName2Re = dict()

    for drug in drugList:
        if drug in dDrugName2Re:
            continue
        print("\r %s, %s" % (len(dDrugName2Re), drug), end="")
        urlx = getRetrieveDrugURL(drug)

        dDrugName2Re[drug] = getTextURL(urlx)
        time.sleep(3)
        if len(dDrugName2Re) % 10 == 0:
            utils.save_obj(dDrugName2Re, RAW_DRUG_TEXT)
            print(urlx)

    utils.save_obj(dDrugName2Re, RAW_DRUG_TEXT)


def parsex(pin=RAW_DRUG_TEXT, pout=DRUG_WEB_ID_PATH):
    r"""
    Extracting the mapping from drug names to drug ids given the raw responses from drugs.com
    Args:
        pin: The path to the raw responses
        pout: The path to the clean mapping


    """
    print("\r Parsing Drug Raw Ids", end="")
    d = utils.load_obj(pin)
    print("OK? ", pout)
    fout = open(pout, "w")
    for k, v in d.items():
        rex = []
        print(k,v)
        try:
            if (v.startswith('{"categories":')):
                jsonObj = json.loads(v)
                info1 = jsonObj["categories"]

                info1 = info1[0]["results"][0]


                ddc_id = "%s" % info1["ddc_id"]
                b_id = "%s" % info1["brand_name_id"]

                rex.append(ddc_id)
                rex.append(b_id)
                print("OK")


            else:
                vbody = BeautifulSoup(v, "html.parser")
                c = vbody.find('a', {"class": "ls-item"})
                txt = c['onclick']
                i1 = txt.index('(')
                i2 = txt.index(')')
                re = txt[i1 + 1:i2]
                parts = re.split(",")

                for part in parts:
                    part = part.strip()
                    val = part[1:-1]
                    rex.append(val)
                # if not rex[-1] == k:
                #     rex = []
        except:
            pass
        if len(rex) > 0:
            fout.write("%s||%s\n" % (k, ",".join(rex)))
    fout.close()


def getInteractions(drugWebIdPath=DRUG_WEB_ID_PATH, predictionPath=PREDICTION_PATH, pOut=RAW_RES_INTER):
    r"""
    Use annotation with Selenium to check drug-drug interactions
    Args:
        drugWebIdPath: path for the mapping from drug names to drugs.com ids
        predictionPath: path for predicted drug interactions
        pOut: path for the output file of raw responses from drugs.com

    """


    fin = open(drugWebIdPath)
    lines = fin.readlines()
    dDrugName2WebId = dict()

    browser = webdriver.Chrome()

    dDrugPairToRe = dict()
    print("Start...")
    try:
        dDrugPairToRe = utils.load_obj(pOut)
    except:
        pass
    print("Init len: ", len(dDrugPairToRe))
    for line in lines:
        line = line.strip()
        parts = line.split("||")
        drugName = parts[0]
        info = parts[1].split(",")
        k1 = info[0]
        k2 = info[1]
        dDrugName2WebId[drugName] = "%s-%s" % (k1, k2)
    fin.close()
    try:
        currentRe = utils.load_obj(pOut)
    except:
        currentRe = {}
    validDrugs = dDrugName2WebId.keys()
    print("N valid drugs: ", len(validDrugs))

    # exit(-1)
    def srt(v1, v2):
        if v1 > v2:
            v1, v2 = v2, v1
        return v1, v2

    fin = open(predictionPath)
    lines = fin.readlines()
    print("Loop")
    for line in lines:
        # print(line)
        try:
            line = line.strip().lower()
            parts = line.split(",")
            d1 = parts[0].strip()
            d2 = parts[1].strip()
            d1, d2 = srt(d1, d2)
            if d1 not in validDrugs or d2 not in validDrugs:
                continue
            p = "%s,%s" % (d1, d2)
            if p in currentRe:
                continue

            pair = "%s,%s" % (dDrugName2WebId[d1], dDrugName2WebId[d2])
            urlx = "%s%s" % (INTER_PREF, pair)
            print("\r %s, %s, %s" % (len(dDrugPairToRe), p, urlx), end="")

            browser.get(urlx)
            html = browser.find_elements(By.TAG_NAME, 'body')[0]
            html = html.get_attribute('innerHTML')
            dDrugPairToRe[p] = html
            time.sleep(4)
            if len(dDrugPairToRe) % 10 == 0:
                utils.save_obj(dDrugPairToRe, pOut)
                print(html[:20])
        except Exception as e:
            print(e)
            continue

    utils.save_obj(dDrugPairToRe, pOut)


def extractInteraction():
    r"""
    Extracting drug-drug interactions information from raw responses of drugs.com
    """
    fMatching = open("%s/PairMatching.txt" % params.TMP_DIR, "w")
    fnoMatching = open("%s/PairNoMatching.txt" % params.TMP_DIR, "w")
    d = utils.load_obj(RAW_RES_INTER)
    cc = 0
    print("N Pais: ", len(d))
    for k, v in d.items():
        cc += 1
        vbody = BeautifulSoup(v, "html.parser")
        div = vbody.find("div", {'class': 'interactions-reference-wrapper'})
        isNoMatch = False
        try:
            if div.text.__contains__('No drug ⬌ drug interactions were found'):
                fnoMatching.write("%s\n" % k)
                isNoMatch = True
        except Exception as e:
            print("1 Error in No Matching")
            print(e)
            pass

        if not isNoMatch:
            try:
                pp = div.findAll("p")
                pr = []
                for p in pp:
                    txt = p.text
                    pr.append(txt)
                fMatching.write("%s||%s\n" % (k, ". ".join(pr).replace("\n", ". ")))
            except Exception as e:
                print("- Error In Matching")
                print(e)

    fMatching.close()
    fnoMatching.close()


def getDrugsComIds():
    r"""
    First get the raw responses from drugs.com for drug names to drug ids
    Then extract the mapping from drug names
    """
    downloadDrugWebId()
    parsex()


def matching():
    r"""
    First get the raw responses from drugs.com for drug interactions
    Then extract the interactions from the raw responses
    """
    getInteractions()
    extractInteraction()

def demo():
    url = "https://www.drugs.com/api/autocomplete/?id=livesearch-interaction&s=fludarabine&data-autocomplete=interaction"
    from utils.utils import getTextURL
    print(getTextURL(url))
if __name__ == "__main__":
    print("Start ")

    # getDrugsComIds()
    # getInteractions()
    extractInteraction()
    # demo()
    print("End ")
    pass
