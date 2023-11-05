import json
import sys
import argparse

# Socket is used to validate IP addresses in nodes
import socket

gridwidth = 5

def parseGNMAP(content):
    uphosts = {}
    for line in content:
        if("Host:" in line):
            hostIP = line.split("Host: ")[1].split("(")[0].strip()
            if(hostIP not in uphosts):
                uphosts[hostIP] = {"ports":[],"os":"", "hostname":""}
            parsedHostName = line.split("(")[1].split(")")[0].strip()
            uphosts[hostIP]["hostname"] = parsedHostName
            if("OS:" in line):
                uphosts[hostIP]["os"] = line.split("OS:")[1].split("\t")[0].strip()
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
    return uphosts

def generateNode(ip, host, nodeList):
    newNode = {'id':0,'x':0,'y':0,'width':600,'height':200,'type':'text','text':"",'color':''}
    lastNode = newNode
    if(len(nodeList) > 0):
        for backwards in nodeList[::-1]:
            if(backwards['type'] == "text" and backwards["text"][:2] == "##"):
                lastNode = backwards
                break
        lastID = lastNode["id"]
        newNode['id'] = int(lastID) + 1
    newNode['y'] = getAboveNodeY(nodeList,gridwidth,newNode['id'])
    if(int(newNode['id']) % gridwidth == 0):
        newNode['x'] = 0
    else:    
        newNode['x'] = lastNode['x'] + 50 + lastNode['width']
    newNode['text'] = generateNodeText(ip, host)
    newNode['height'] = 40*len(newNode['text'].split("\n")) + 50
    return newNode

def convert2canvas(parsedhosts):
    final = {'nodes':[], 'edges':[]}
    for host in parsedhosts:
        print("New host: {}".format(host))
        newnode = generateNode(host, parsedhosts[host],final["nodes"])
        final['nodes'].append(newnode)
    
    return final

def generateNodeText(ip, host):
    nodeText = "## {}:".format(ip)
    #if(host['hostname'] != ""):
    nodeText = nodeText +"\n- **Hostname:** " + host['hostname']
    #if(host['os'] != ""):
    nodeText = nodeText +"\n- **OS:** " + host['os']
    nodeText = nodeText +"\n- **Ports:** "
    for port in host['ports']:
        nodeText = nodeText + "\n\t- ({}) **{}**: {}".format(port["proto"],port["number"],port["version"])
    return nodeText

### TODO: Fix spacing issue when there are none standard nodes in the canvas
def getAboveNodeY(nodes,gridwidth,currid):
    #If we are in the first row of the grid
    count = 0
    hostNodes = []
    for node in nodes:
        if(node["type"] == "text" and node["text"][:2] == "##"):
            count = count + 1
            hostNodes.append(node)
    # If we are in the first row
    if(count < gridwidth):
        return 0
    return hostNodes[int(currid)-gridwidth]['height'] + hostNodes[int(currid)-gridwidth]['y']  + 50

### FORMAT
'''
{
    '192.168.1.1': 
        {
            'ports': 
                [
                    {'number': '69', 'proto': 'tcp', 'version': ''},
                    {'number': '53', 'proto': 'tcp', 'version': ''},
                    {'number': '2222', 'proto': 'tcp', 'version': ''},
                    {'number': '8443', 'proto': 'tcp', 'version': ''},
                    {'number': '49152', 'proto': 'tcp', 'version': ''}
                ], 
            'os': 'Linux 3.10 - 4.11|Linux 5.1',
            'hostname': 'RT-AX86U-EA48'
        }
'''
def parseCanvas(rawCanvas):
    parsedHosts = {}
    for node in rawCanvas["nodes"]:
        if(node["type"] != "text"):
            print("SKIPPING NON HOST NODE")
            continue
        newHost = {'ports':[],'os':'','hostname':''}
        nodeLines = node["text"].split("\n")

        ### Skip all nodes that aren't host nodes
        if("##" == nodeLines[0][:2]):
            try:
                socket.inet_aton(nodeLines[0].split("## ")[1].split(":")[0].strip())
            except:
                print("SKIPPING NON HOST NODE")
                continue
        else:
            print("SKIPPING NON HOST NODE")
            continue
        ###

        nodeIP = nodeLines[0].split("## ")[1].split(":")[0]
        if(len(nodeLines) >= 3):
            if("**Hostname:**" in nodeLines[1]):
                newHost['hostname'] = nodeLines[1].split(":** ")[1]
            if("**OS:**" in nodeLines[2]):
                newHost['os'] = nodeLines[2].split(":** ")[1]
        inPorts = False
        for line in nodeLines:
            # We are reading ports in the Ports: section
            if(inPorts and "\t" == line[0]):
                portNumber = line.split("- ")[1].split("**")[1]
                portProto = line.split("- ")[1].split("(")[1].split(")")[0]
                newPort = {'number': portNumber, 'proto': portProto, 'version': ''}
                newHost["ports"].append(newPort)
            # We have left the Ports: section
            elif(inPorts and "\t" != line[0]):
                inPorts = False
            
            # We are enter the Ports: section
            if("Ports:" in line):
                inPorts = True
            


        parsedHosts[nodeIP] = newHost

    return parsedHosts


def updateCanvas(path2update, newHosts):
    rawCanvas = {}
    with open(path2update, "r") as f:
        rawCanvas = json.loads(f.read())
        # parseCanvas only returns nodes that have been generated by this script previously
        # a host node = a node previously generated by this script
        parsedCanvas = parseCanvas(rawCanvas)
        for host in newHosts:
            existing = False
            '''
            for node in rawCanvas["nodes"]:
                # Skip none-host nodes
                if(not node['type'] == "text" or not "##" == node["text"][:2]):
                    continue
                nodeIP = node["text"].split("## ")[1].split(":")[0].strip()
                if(host == nodeIP):
                    existing = True
                    break
            '''
            # If the host already exists in the canvas being updated
            if(host in parsedCanvas):
                updated = False
                # Check if there are any new ports to add
                for port in newHosts[host]["ports"]:
                    if(port not in parsedCanvas[host]["ports"]):
                        print("Port {} added to {}".format(port["number"],host))
                        parsedCanvas[host]["ports"].append(port)
                        updated = True
                if(not updated):
                    print("No new ports added to {}".format(host))
                # Check if there is a new hostname to add
                if(newHosts[host]["hostname"] != "" and newHosts[host]["hostname"] != parsedCanvas[host]["hostname"]):
                    if(parsedCanvas[host]["hostname"] == ""):
                        print("Adding hostname {} to {}".format(newHosts[host]["hostname"], host))
                        parsedCanvas[host]["hostname"] = newHosts[host]["hostname"]
                    else:
                        print("Modifying hostname for {} from {} to {}".format(host, parsedCanvas[host]["hostname"], newHosts[host]["hostname"]))
                        parsedCanvas[host]["hostname"] = newHosts[host]["hostname"]
                # Check if there is a new OS to add
                if(newHosts[host]["os"] != "" and newHosts[host]["os"] != parsedCanvas[host]["os"]):
                    if(parsedCanvas[host]["os"] == ""):
                        print(host)
                        print(parsedCanvas[host])
                        print("Adding os {} to {}".format(newHosts[host]["os"], host))
                        parsedCanvas[host]["os"] = newHosts[host]["os"]
                    else:
                        print("Modifying os for {} from {} to {}".format(host, parsedCanvas[host]["os"], newHosts[host]["os"]))
                        parsedCanvas[host]["os"] = newHosts[host]["os"]
            # If we need to add a new host
            else:
                print("New host: {}".format(host))
                #newNode = generateNode(host, newHosts[host],rawCanvas["nodes"])
                parsedCanvas[host] = newHosts[host]
                #rawCanvas["nodes"].append(newNode)

    # 
    updatedList = []
    for index in range(len(rawCanvas["nodes"])):
        if(rawCanvas["nodes"][index]["type"] != "text"):
            continue
        nodeLines = rawCanvas["nodes"][index]["text"].split("\n")
        if("##" == nodeLines[0][:2]):
            try:
                nodeIP = nodeLines[0].split("## ")[1].split(":")[0].strip()
                socket.inet_aton(nodeIP)
                # If this was one of the updated ones, update the text
                if(nodeIP in parsedCanvas):
                    rawCanvas["nodes"][index]["text"] = generateNodeText(nodeIP, parsedCanvas[nodeIP])
                    updatedList.append(nodeIP)
                #rawCanvas["nodes"].pop(index)
            except:
                continue
        else:
            continue
    # Add any additional hosts that weren't updated
    for host in parsedCanvas:
        if(host not in updatedList):
            rawCanvas["nodes"].append(generateNode(host, parsedCanvas[host],rawCanvas["nodes"]))

    with open(path2update, 'w') as f:    
        f.write(json.dumps(rawCanvas))

def main():
    parser = argparse.ArgumentParser(description="Script to build out network maps in Obsidian using canvases and greppable scan results")
    parser.add_argument("-i", '--input', nargs='+', help="Input greppable scan file", required=True)
    parser.add_argument("-o", "--output", help="Specify the output file, stdout if not specified", required=True)
    parser.add_argument("-u",'--update', help="Update instead of overwrite output canvas", action='store_true')
    args = parser.parse_args()
    # If no arguments were given, print help and exit
    if(len(sys.argv) == 1):
        parser.print_help()
        parser.exit()
    # If multiple input files have bee specified
    if(len(args.input) > 1):
        print("WIP: Add/Update multiple scans at once")
        quit()
    content = open(args.input[0]).readlines()
    parsedhosts = parseGNMAP(content)
    # If update arg is specified we will add to that file and return
    if(args.update):
        print("UPDATING EXISTING CANVAS")
        updateCanvas(args.output, parsedhosts)
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
