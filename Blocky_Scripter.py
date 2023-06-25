
import maya.cmds as cmds
import maya.mel as mel

# __port__([],[]); //MEL
# __port__([],[]) #Python

# ///////////////////////////
# WRAPPER CLASS
# ///////////////////////////


def __runBlockyCodeBuilder__():
    import textwrap
    import enum
    import re

    # ///////////////////////////
    # CODE FOR THE INTERFACE WINDOW
    # ///////////////////////////

    class Window:

        def __init__(self):
            self.windowName = 'ScriptBuilder'
            self.body = None
            self.blocks = []

        def setup(self):
            # delete the window if it already exists
            if cmds.window(self.windowName, exists=True):
                cmds.deleteUI(self.windowName)

            # sets current layout to window
            cmds.window(self.windowName, title='Script Builder',
                        widthHeight=(300, 200))

            # create the window-wide flexible form layout
            form = cmds.formLayout(numberOfDivisions=100)

            # make the buttons
            pyButton = cmds.button(label='Python Block',
                                   command=lambda *args: self.appendBlock(Block(self, __BlockLanguage__.PYTHON)))
            melButton = cmds.button(label='MEL Block',
                                    command=lambda *args: self.appendBlock(Block(self, __BlockLanguage__.MEL)))
            runButton = cmds.button(
                "Run", command=lambda *args: self.runCode())

            # make the scroll window for code blocks
            self.body = cmds.scrollLayout(
                backgroundColor=(0.1, 0.1, 0.1), childResizable=True)

            # align all the assets in the form layout
            cmds.formLayout(form, edit=True,
                            attachForm=[(self.body, "top", 5),
                                        (self.body, "left", 5),
                                        (self.body, "right", 5),
                                        (runButton, "bottom", 5),
                                        (runButton, "left", 5),
                                        (runButton, "right", 5),
                                        (pyButton, "left", 5),
                                        (melButton, "right", 5)],
                            attachControl=[(self.body, "bottom", 5, pyButton),
                                           (pyButton, "bottom", 5, runButton),
                                           (melButton, "bottom", 5, runButton)],
                            attachPosition=[(pyButton, "right", 2.5, 50),
                                            (melButton, "left", 2.5, 50)],
                            attachNone=[(runButton, "top"),
                                        (pyButton, "top"),
                                        (melButton, "top")])

            cmds.showWindow(self.windowName)

        def appendBlock(self, layout):
            cmds.frameLayout(layout.frame, edit=True, visible=True)
            self.blocks.append(layout)

            for i in range(len(self.blocks)):
                self.blocks[i].updateUI()

        def removeBlock(self, layout):
            cmds.deleteUI(layout.frame)

            removedIndex = self.blocks.index(layout)
            self.blocks.remove(layout)

            for i in range(0, removedIndex):
                self.blocks[i].updateUI()

            for i in range(removedIndex, len(self.blocks)):
                self.blocks[i].updateUI(i)

        def moveBlock(self, layout, toMove, newIndex):
            # create invisible temp layouts for storing everything
            saving = cmds.columnLayout(manage=0)
            cmds.setParent('..')
            moving = cmds.columnLayout(manage=0)
            cmds.setParent('..')

            # sanitize newIndex
            newIndex = clampInt(newIndex, 0, len(self.blocks)-1)
            changeStart = min(self.blocks.index(toMove), newIndex)

            self.blocks.remove(toMove)
            self.blocks.insert(newIndex, toMove)

            moving = cmds.columnLayout(manage=0)
            cmds.setParent('..')

            # move and update the blocks that are moving
            for i in range(changeStart, len(self.blocks)):
                shortName = str(self.blocks[i].frame).split("|")[-1]
                cmds.layout(shortName, edit=True, parent=moving)
                cmds.layout(shortName, edit=True, parent=layout)
                self.blocks[i].updateIndex(
                    i, self.blocks[i].getToolbar()[0])

            cmds.deleteUI(moving)

        def runCode(self):
            print("Running code from script builder window.")
            if (self.blocks == []):
                print("Nothing to Run!")
            else:
                for i in self.blocks:
                    field = getChildren(i.frame)[1]
                    snippet = cmds.scrollField(field, query=True, text=True)

                    # wrapping the blocks in functions to protect scope
                    if i.language == __BlockLanguage__.MEL:
                        open = "proc MELBlock(){"
                        close = "\nreturn;} MELBlock();"
                        mel.eval(open+snippet+close)
                    elif i.language == __BlockLanguage__.PYTHON:
                        open = "def pythonBlock():\n"
                        close = "\n\treturn\npythonBlock()"
                        exec(open+textwrap.indent(snippet, '\t')+close)

            print("Execution completed.\n")

    # ///////////////////////////
    # CODE FOR INDIVIDUAL BLOCKS
    # ///////////////////////////

    class __BlockLanguage__(enum.Enum):
        MEL = "MEL"
        PYTHON = "Python"

    def clampInt(input, minimum, maximum):
        return min(max(input, minimum), maximum)

    # returns a list of the children of <layout>
    def getChildren(layout):
        try:
            return cmds.layout(layout, query=True, childArray=True)
        except:
            return None

    class Block:
        def __init__(self, parent, language: __BlockLanguage__):
            # sets current layout to the enclosing frameLayout
            self.parent = parent
            self.language = language
            self.comment = "//" if language == __BlockLanguage__.MEL else "#"

            self.frame = cmds.frameLayout(label=str(len(self.parent.blocks))+"_Unnamed "+self.comment +
                                          language.value, collapsable=True, collapse=True, marginHeight=10, marginWidth=10)

            # sets current layout to the rowLayout top toolbar
            cmds.rowLayout(numberOfColumns=3)

            dropdown = cmds.optionMenu(changeCommand=lambda *args: parent.moveBlock(
                parent.body, self, cmds.optionMenu(dropdown, query=True, select=True)-1))
            for i in range(len(self.parent.blocks)+1):
                cmds.menuItem(label="#"+str(i))
            cmds.optionMenu(dropdown, edit=True,
                            select=len(self.parent.blocks)+1)

            cmds.textField(
                textChangedCommand=lambda *args: self.updateName(), text="Section Name")

            cmds.button(label='Remove',
                        command=lambda *args: parent.removeBlock(self))

            cmds.setParent('..')
            cmds.scrollField(
                text=(self.comment+language.value+" code goes here"))

            cmds.setParent('..')
            # active layout is reset

        def getToolbar(self):
            return (getChildren(getChildren(self.frame)[0]))

        def updateName(self):
            toolbar = self.getToolbar()
            dropdown = toolbar[0]

            number = cmds.optionMenu(dropdown, query=True, select=True)-1
            name = re.sub(r'\s', '_', cmds.textField(
                toolbar[1], query=True, text=True))

            cmds.frameLayout(self.frame, edit=True, label=(
                str(number)+"_"+name+" "+self.comment+self.language.value))

        def updateIndex(self, index, dropdown):
            cmds.optionMenu(dropdown, edit=True, select=index+1)
            label = cmds.frameLayout(self.frame, query=True, label=True)
            name = label.split('_', 1)[1]

            cmds.frameLayout(self.frame, edit=True,
                             label=(str(index)+"_"+name))

        def updateUI(self, newIndex=None):
            dropdown = self.getToolbar()[0]
            newMenuLength = len(self.parent.blocks)
            oldMenu = cmds.optionMenu(dropdown, query=True, itemListShort=True)
            oldSize = len(oldMenu)
            sizeChange = newMenuLength - oldSize

            if sizeChange > 0:
                for i in range(oldSize, newMenuLength):
                    cmds.menuItem(parent=dropdown, label=("#"+str(i)))
            elif sizeChange < 0:
                for i in range(newMenuLength, oldSize):
                    cmds.deleteUI(oldMenu[i])

            if newIndex is not None:
                self.updateIndex(newIndex, dropdown)

    # ///////////////////////////
    # CREATING AND SETTING UP THE WINDOW
    # ///////////////////////////

    buildWindow = Window()
    buildWindow.setup()

# ///////////////////////////
# END OF WRAPPER CLASS
# ///////////////////////////


__runBlockyCodeBuilder__()
