import json
import sys
import argparse

gridwidth = 3

def parseGNMAP(content):
    uphosts = {}
    for line in content:
        if("Host:" in line):
            hostIP = line.split("Host: ")[1].split("(")[0].strip()
            if(hostIP not in uphosts):
                uphosts[hostIP] = {"ports":[],"os":""}
            if("Ports:" in line):
                portlist = line.split("Ports: ")[-1].split(",")
                for port in portlist:
                    if("open" in port.strip()):
                        details = port.strip().split("\t")
                        portinfo = details[0].split("//")
                        portnum = portinfo[0].split("/")[0]
                        portproto = portinfo[0].split("/")[2]
                        portversion = portinfo[2][:-1]
                        uphosts[hostIP]['ports'].append({"number":portnum,"proto":portproto,"version":portversion})
                        if(len(details) >= 3):
                            uphosts[hostIP]['os'] = details[2].strip()
    return uphosts

def convert2canvas(parsedhosts):
    numinrow = 0
    currID = 0
    x = 0
    y = 0
    largesty = -1
    final = {'nodes':[], 'edges':[]}
    template = {'id':'','x':x,'y':y,'width':600,'height':200,'type':'text','text':"",'color':''}
    for host in parsedhosts:
        print("New host: {}".format(host))
        newnode = dict(template)
        newnode['id'] = str(currID)
        currID = currID + 1
        if(parsedhosts[host]['os'] != ""):
            nodeText = "## {}({}):".format(host,parsedhosts[host]['os'])
        else:
            nodeText = "## {}:".format(host)

        for port in parsedhosts[host]['ports']:
            print("Port {} added to {}".format(port["number"],host))
            nodeText = nodeText + "\n- ({}) **{}**: {}".format(port["proto"],port["number"],port["version"])
        newnode['text'] = nodeText
        newnode['height'] = 50*len(nodeText.split("\n")) + 50
        if(newnode['height'] > largesty):
            largesty = newnode['height']
        newnode['y'] = getAboveNodeY(final['nodes'],gridwidth,newnode['id'])
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

### TODO: Fix spacing issue when there are none standard nodes in the canvas
def getAboveNodeY(nodes,gridwidth,currid):
    #If we are in the first row of the grid
    count = 0
    for node in nodes:
        if(node["type"] == "text" and node["text"][:2] == "##"):
            count = count + 1
    if(count < gridwidth):
        return 0
    return nodes[int(currid)-gridwidth]['height'] + nodes[int(currid)-gridwidth]['y']  + 50

def updateCanvas(path2update, newHosts):
    rawCanvas = {}
    with open(path2update, "r") as f:
        rawCanvas = json.loads(f.read())
        for host in newHosts:
            existing = False
            for node in rawCanvas["nodes"]:
                # Skip none-host nodes
                if(not node['type'] == "text" or not "##" == node["text"][:2]):
                    continue
                nodeIP = node["text"].split("## ")[1].split(":")[0]
                if(host == nodeIP):
                    existing = True
                    break
            if(existing):
                updated = False
                for port in newHosts[host]["ports"]:
                    portToAdd = "({}) **{}**".format(port["proto"],port["number"])
                    if portToAdd not in node["text"]:
                        print("Port {} added to {}".format(port["number"],host))
                        node["text"] = node["text"] + "\n- ({}) **{}**: {}".format(port["proto"],port["number"],port["version"])
                        updated = True
                if(not updated):
                    print("No new ports added to {}".format(host))
            else:
                print("New host: {}".format(host))
                lastNode = {}
                for backwards in rawCanvas["nodes"][::-1]:
                    if(backwards['type'] == "text" and backwards["text"][:2] == "##"):
                        lastNode = backwards
                        break
                lastID = lastNode["id"]
                newNode = {'id':int(lastID) + 1,'x':'','y':'','width':600,'height':200,'type':'text','text':"",'color':''}
                newNode['y'] = getAboveNodeY(rawCanvas["nodes"],gridwidth,newNode['id'])
                if(newNode['id'] % gridwidth == 0):
                    newNode['x'] = 0
                else:    
                    newNode['x'] = lastNode['x'] + 50 + lastNode['width']
                if(newHosts[host]['os'] != ""):
                    nodeText = "## {}({}):".format(host,parsedhosts[host]['os'])
                else:
                    nodeText = "## {}:".format(host)
                for port in newHosts[host]['ports']:
                    print("Port {} added to {}".format(port["number"],host))
                    nodeText = nodeText + "\n- ({}) **{}**: {}".format(port["proto"],port["number"],port["version"])
                newNode['text'] = nodeText
                rawCanvas["nodes"].append(newNode)
    with open(path2update, 'w') as f:    
        f.write(json.dumps(rawCanvas))

def main():
    parser = argparse.ArgumentParser(description="Script to build out network maps in Obsidian using canvases and greppable scan results")
    parser.add_argument("-o", "--output", help="Specify the output file, stdout if not specified")
    parser.add_argument("-u", "--update", help="Specify the file to update", required=False)
    parser.add_argument("-i", "--input", nargs='+', help="Input greppable scan file")
    args = parser.parse_args()
    if(len(args.input) > 1):
        print("WIP: Add/Update multiple scans at once")
        quit()
    content = open(args.input[0]).readlines()
    parsedhosts = parseGNMAP(content)
    # If update arg is specified we will add to that file and return
    if(args.update):
        print("UPDATING EXISTING CANVAS")
        updateCanvas(args.update, parsedhosts)
        return
    print("GENERATING NEW CANVAS")
    newcanvas = convert2canvas(parsedhosts)
    # If we are writing output to a file or stdout
    if(args.output):
        with open(args.output, 'w') as f:
            f.write(json.dumps(newcanvas))
    else:
        print(json.dumps(newcanvas)) 
    #for host in parsedhosts:
    #    print(parsedhosts[host])

if __name__ == '__main__':
    main()