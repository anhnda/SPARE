import params
from utils.utils import get_insert_key_dict, get_dict
TSUI_PATH = "%s/TSUI_ML.txt" % params.DATA_DIR

def load_drug_bank():
    fin = open(params.NEW_DRUGBANK_X, 'r')
    d = {}
    while True:
        line = fin.readline()
        if line == "":
            break
        parts = line.strip().split("||")
        d[parts[0]] = parts[4]
    fin.close()
    return d


def export_tsui():
    dname2code = load_drug_bank()
    fin = open(TSUI_PATH, 'r')
    fout = open("%s/TSUI_C5.txt" % params.DATA_DIR, "w")
    fin.readline()
    p_drugpair = ""
    c_ses = []
    while True:
        line = fin.readline()
        if line == "":
            break
        parts = line.strip().split(",")
        drug1, drug2 = parts[0], parts[1]
        se = parts[2]
        d_pair = "%s_%s" % (drug1, drug2)
        if d_pair != p_drugpair:
            if len(c_ses) != 0:
                c1 = get_dict(dname2code, drug1, -1)
                c2 = get_dict(dname2code, drug2, -1)
                if c1 != -1 and c2 != -1:
                    fout.write("%s|%s|%s|%s|" %( drug1, drug2, c1, c2))
                for se in c_ses[:-1]:
                    fout.write("%s," % se)
                fout.write("%s\n" % c_ses[-1])
            p_drugpair = d_pair
            c_ses = []

        c_ses.append(se)

    # Write last
    c1 = get_dict(dname2code, drug1, -1)
    c2 = get_dict(dname2code, drug2, -1)
    if c1 != -1 and c2 != -1:
        fout.write("%s|%s|%s|%s|" %( drug1, drug2, c1, c2))
    assert len(c_ses) > 0
    for se in c_ses[:-1]:
        fout.write("%s," % se)

    fout.write("%s\n" % c_ses[-1])
    fout.close()

if __name__ == "__main__":
    export_tsui()



