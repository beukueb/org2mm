#!/bin/env python3
#To implement
#Calendar
#<icon BUILTIN="calendar"/>
#<hook NAME="plugins/TimeManagementReminder.xml">
#<Parameters REMINDUSERAT="1462549440509"/>
#</hook>
#
#Interesting icons
# <icon BUILTIN="full-1"/> -> '1'
# <icon BUILTIN="full-2"/> '2'
# <icon BUILTIN="go"/> -> green traffic light
# <icon BUILTIN="prepare"/> -> yellow traffic light
# <icon BUILTIN="stop"/> -> red traffic light
# <icon BUILTIN="yes"/> -> !
# <icon BUILTIN="help"/> -> ?
# <icon BUILTIN="idea"/> -> lampje
# <icon BUILTIN="messagebox_warning"/> -> '!'
# <icon BUILTIN="stop-sign"/> -> 'STOP'
# <icon BUILTIN="closed"/> -> '-'
# <icon BUILTIN="info"/> -> 'i'
# <icon BUILTIN="button_ok"/> -> 'V'
# <icon BUILTIN="button_cancel"/> 'X'
# <icon BUILTIN="forward"/> ->
# <icon BUILTIN="back"/> <-
# <icon BUILTIN="up"/> A
# <icon BUILTIN="down"/> V
# <icon BUILTIN="group"/> iii
# <icon BUILTIN="xmag"/> -> magnifying glass

def convertNode(orgNode,xmlParentNode,todos,addNote=False):
    import xml.etree.ElementTree as ET
    heading = orgNode.heading #if not orgNode will raise exception
    xmlNode = ET.SubElement(xmlParentNode,'node')
    xmlNode.set('TEXT',heading)
    for orgChild in orgNode.content:
        try:
            convertNode(orgChild,xmlNode,todos,addNote)
        except AttributeError:
            #Add logic for adding paragraph comments
            if addNote:
                #from xml.sax.saxutils import escape
                note = ET.SubElement(xmlNode,'richcontent')
                note.set('TYPE','NOTE')
                html = ET.SubElement(note,'html')
                head = ET.SubElement(html,'head')
                head.text = '\n'
                body = ET.SubElement(ET.SubElement(html,'body'),'p')
                body.text = orgNode.output().replace(orgNode.heading,''
                ).replace('*'*orgNode.level,'')
                addNote = False
    #Check todo state
    try:
        if orgNode.todo:
            icon = ET.SubElement(xmlNode,'icon')
            icon.set('BUILTIN',todos[orgNode.todo])
    except AttributeError:
        pass
    
def convert(orgfile,startnode='Start',outfile=None,addNotes=False,icons=None):
    """
    Function that converts the org outline file to the xml freemind format
    """
    import sys
    from PyOrgMode import PyOrgMode
    import xml.etree.ElementTree as ET
    orgbase=PyOrgMode.OrgDataStructure()
    #Set todo states
    orgbase.remove_todo_state('DONE')
    todos = {t:i for i,t in icons}
    for todo in todos:
        orgbase.add_todo_state(todo)
    orgbase.load_from_file(orgfile)
    rootXML = ET.Element('map')
    rootXML.append(ET.Comment('To view this file, download free mind mapping \
software FreeMind from http://freemind.sourceforge.net'
    ))
    orgbase.root.heading = startnode
    convertNode(orgbase.root,rootXML,addNote=addNotes,todos=todos)
    
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
    parser.add_argument('-s','--subtext',help='include non outline paragraph text',
                        action='store_true', default=False)
    parser.add_argument('-i','--iconTODO',action='append',nargs=2,metavar=('icon','todo'),
                        help='Associate a builtin icon with a todo state ')

    #argv = parser.parse_args('-i i1 t1 -i i2 t2 --topic FirstNode /home/christophe/Dropbox/Science/Cytogenetics/notes/mindmap.org'.split())
    #argv = parser.parse_args('todo_outline.org'.split())
    argv = parser.parse_args()
    if not argv.iconTODO: argv.iconTODO = [['full-1','TODO']]

    convert(orgfile=argv.outline,startnode=argv.topic,outfile=argv.output,addNotes=argv.subtext,icons=argv.iconTODO)
