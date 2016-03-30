#!/bin/env python3

def convertNode(orgNode,xmlParentNode):
    import xml.etree.ElementTree as ET
    heading = orgNode.heading #if not orgNode will raise exception
    xmlNode = ET.SubElement(xmlParentNode,'node')
    xmlNode.set('TEXT',heading)
    try:
        for orgChild in orgNode.content:
            convertNode(orgChild,xmlNode)
    except AttributeError:
        #Add logic for adding paragraph comments
        pass
    #Check todo state
    try:
        if orgNode.todo:
            icon = ET.SubElement(xmlNode,'icon')
            icon.set('BUILTIN','full-1')
    except AttributeError:
        pass
    
def convert(orgfile,startnode='Start',outfile=None):
    """
    Function that converts the org outline file to the xml freemind format
    """
    import sys
    from PyOrgMode import PyOrgMode
    import xml.etree.ElementTree as ET
    orgbase=PyOrgMode.OrgDataStructure()
    orgbase.load_from_file(orgfile)
    rootXML = ET.Element('map')
    rootXML.append(ET.Comment('To view this file, download free mind mapping \
software FreeMind from http://freemind.sourceforge.net'
    ))
    orgbase.root.heading = startnode
    convertNode(orgbase.root,rootXML)
    
    if not outfile:
        outfile = sys.stdout
    else:
        outfile = open(outfile,'wt')
    outfile.write(ET.tostring(rootXML).decode())
    if outfile != sys.stdout: outfile.close()
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Convert org outline to freemind mindmap.')
    parser.add_argument('outline', help='org outline file')
    parser.add_argument('output', help='output filename', nargs='?')
    parser.add_argument('-t','--topic', help='top level mind map node (default "Start")', default='Start')
    parser.add_argument('-s','--subtext',help='include non outline paragraph text')

    #argv = parser.parse_args('--topic FirstNode /home/christophe/Dropbox/Science/Cytogenetics/notes/mindmap.org'.split())
    #argv = parser.parse_args('todo_outline.org'.split())
    argv = parser.parse_args()

    convert(orgfile=argv.outline,startnode=argv.topic,outfile=argv.output)
