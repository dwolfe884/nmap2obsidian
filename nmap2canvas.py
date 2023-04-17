import json
import sys

def parseGNMAP(content):
    uphosts = {}
    for line in content:
        if("Host:" in line):
            hostIP = line.split(" ")[1].strip()
            if(hostIP not in uphosts):
                uphosts[hostIP] = {"ports":[],"os":""}
            if("Ports:" in line):
                portlist = line.split("Ports: ")[-1].split(",")
                for port in portlist:
                    if("open" in port.strip()):
                        details = port.strip().split("\t")
                        #print(details)
                        portinfo = details[0].split("//")
                        portnum = portinfo[0].split("/")[0]
                        portproto = portinfo[0].split("/")[2]
                        portversion = portinfo[2][:-1]
                        uphosts[hostIP]['ports'].append({"number":portnum,"proto":portproto,"version":portversion})
                        if(len(details) >= 3):
                            uphosts[hostIP]['os'] = details[2].strip()
    return uphosts

def convert2canvas(parsedhosts):
    gridwidth = 3
    numinrow = 0
    currID = 0
    x = 0
    y = 0
    largesty = -1
    final = {'nodes':[], 'edges':[]}
    template = {'id':'','x':x,'y':y,'width':600,'height':200,'type':'text','text':"",'color':''}
    for host in parsedhosts:
        newnode = dict(template)
        newnode['id'] = str(currID)
        currID = currID + 1
        if(parsedhosts[host]['os'] != ""):
            nodeText = "## {}({}):".format(host,parsedhosts[host]['os'])
        else:
            nodeText = "## {}:".format(host)

        for port in parsedhosts[host]['ports']:
            nodeText = nodeText + "\n- ({}) **{}**: {}".format(port["proto"],port["number"],port["version"])
        newnode['text'] = nodeText
        newnode['height'] = 50*len(nodeText.split("\n")) + 50
        if(newnode['height'] > largesty):
            largesty = newnode['height']
        newnode['y'] = getAboveNodeY(final['nodes'],gridwidth,newnode['id']) + 50
        newnode['x'] = x
        x = x + newnode['width'] + 50
        numinrow = numinrow + 1
        if(numinrow >= gridwidth):
            y = y + largesty + 50 #Move to next row, with 50 for padding between nodes
            x = 0
            numinrow = 0
            largesty = -1
        final['nodes'].append(newnode)
    
    return final

def getAboveNodeY(nodes,gridwidth,currid):
    #If we are in the first row of the grid
    if(len(nodes) <= gridwidth):
        return 0
    return nodes[int(currid)-gridwidth]['height'] + nodes[int(currid)-gridwidth]['y'] 

def main(gnmappath):
    content = open(gnmappath).readlines()
    parsedhosts = parseGNMAP(content)
    newcanvas = convert2canvas(parsedhosts)      
    print(json.dumps(newcanvas)) 
    #for host in parsedhosts:
    #    print(parsedhosts[host])

if __name__ == '__main__':
    if(len(sys.argv) == 2):
        main(sys.argv[1])
    else:
        print("ERROR: Must only provide path to .gnmap file")
