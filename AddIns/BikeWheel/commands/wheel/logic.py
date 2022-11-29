from enum import Enum
from math import pi
  
from ..spoke import logic as Spoke
from ..rim import logic as Rim
from ..hub import logic as Hub

import adsk.core as core
import adsk.fusion as fusion

app = core.Application.get()
if app:
    ui = app.userInterface
    createPoint = core.Point3D.create
    alert = ui.messageBox
design = fusion.Design.cast(app.activeProduct)
if not design:
    alert('You must be in the design workspace to use this command')
skipValidate = False

class SpokeType(Enum):
    BUTTEDSTRAIGHT = 1
    BUTTEDJ = 2
    BLADEDSTRAIGHT = 3
    BLADEDJ = 4

class WheelLogic():
    def __init__(self) -> None:
        self.hub = ""
        self.spokeQuantity = 32
        self.spokeType = SpokeType.BUTTEDJ
        self.rim = ""
        self.rimSize = "700c"
    
    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        self.hubInput: core.DropDownCommandInput = inputs.addDropDownCommandInput(
            "hub", "Hub", core.DropDownStyles.TextListDropDownStyle
        )
        for hub in Hub.hubData:
            self.hubInput.listItems.add(hub, False)

        self.rimInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('rim', 'Rim', core.DropDownStyles.TextListDropDownStyle)
        for rim in Rim.rimProfiles:
            self.rimInput.listItems.add(rim, False)

        self.sizeInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('size', 'Size', core.DropDownStyles.TextListDropDownStyle)
        # rimSizes = Rim.rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys()
        # for size in rimSizes:
            # self.sizeInput.listItems.add(size, False)

        self.spokesInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('spokes', 'Spokes', core.DropDownStyles.TextListDropDownStyle)
        # spokeCounts = Rim.rimProfiles[self.rimInput.selectedItem.name]['spokes']
        # for count in spokeCounts:
            # self.spokesInput.listItems.add(str(count), False)

        self.buttedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('butted', 'Butted', True, '', False)
        # self.straightPullInput: core.BoolValueCommandInput = inputs.addBoolValueInput('straightPull', 'Straight Pull', True, '', False)
        # self.bladedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('bladed', 'Bladed', True, '', False)
        self.diameterInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('diameter', 'Diameter', core.DropDownStyles.TextListDropDownStyle)
        self.diameterInput.listItems.add('1.8 mm', False)
        self.diameterInput.listItems.add('2.0 mm', True)
        self.diameterInput.listItems.add('2.3 mm', False)
        self.diameterInput.listItems.add('2.6 mm', False)

        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        changedInput = args.input
        
        if not skipValidate:
            if changedInput.id == 'rim':
                self.sizeInput.listItems.clear()
                self.spokesInput.listItems.clear()
                rimSizes = Rim.rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys()
                for size in rimSizes:
                    self.sizeInput.listItems.add(size, False)
                spokeCounts = Rim.rimProfiles[self.rimInput.selectedItem.name]['spokes']
                for count in spokeCounts:
                    self.spokesInput.listItems.add(str(count), False)

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        unitsMgr = design.unitsManager
        if not skipValidate:
            self.errorMessageTextInput.text = ''
            self.hub = self.hubInput.selectedItem.name
            self.rim = self.rimInput.selectedItem.name
            self.size = self.sizeInput.selectedItem.name
            self.spokes = int(self.spokesInput.selectedItem.name)
            # if not self.lengthInput.isValidExpression:
            #     self.errorMessageTextInput.text = 'The spoke length is invalid'
            #     args.areInputsValid = False
            #     return
                     
            # if self.lengthInput.value < 10 or self.lengthInput.value > 50:
            #     self.errorMessageTextInput.text = 'The spoke length should be between 100 and 500 mm'
            #     args.areInputsValid = False
            #     return
            # if self.bladedInput.value == True and self.buttedInput.value == True:
            #     self.errorMessageTextInput.text = 'Bladed and Butted cannot both be checked'
            #     args.areInputsValid = False
            #     return
            # args.areInputsValid = True
            # self.bladed = self.bladedInput.value
            # self.butted = self.buttedInput.value
            # self.length = unitsMgr.evaluateExpression(self.lengthInput.expression)
            # self.diameter = unitsMgr.evaluateExpression(self.diameterInput.selectedItem.name)
            # self.straightPull = self.straightPullInput.value

    def HandleExecute(self, args: core.CommandEventArgs):
        unitsMgr = design.unitsManager

        self.hub_logic = Hub.HubLogic()
        self.hub_logic.hubType: Hub.HubType = Hub.hubData[self.hub]["type"]
        self.hub_logic.brakeType: Hub.BrakeType = Hub.hubData[self.hub]["brake"]
        self.hub_logic.axleType: Hub.AxleType = Hub.hubData[self.hub]["axle"]
        self.hub_logic.axleDia = Hub.axleDiameters[self.hub_logic.hubType.name][self.hub_logic.axleType.name]
        self.hub_logic.old = Hub.hubData[self.hub]["old"]
        self.hub_logic.leftFlangeDia = Hub.hubData[self.hub]["leftFlangeDia"]
        self.hub_logic.rightFlangeDia = Hub.hubData[self.hub]["rightFlangeDia"]
        self.hub_logic.centerToLeftFlange = Hub.hubData[self.hub]["centerToLeftFlange"]
        self.hub_logic.centerToRightFlange = Hub.hubData[self.hub]["centerToRightFlange"]
        self.hub_logic.spokes = self.spokes
        self.hub_logic.preset = self.hub

        self.spoke_logic = Spoke.SpokeLogic()
        # self.bladed = self.bladedInput.value
        self.spoke_logic.butted = self.buttedInput.value
        self.length = {} # TODO calculate this length
        self.diameter = unitsMgr.evaluateExpression(self.diameterInput.selectedItem.name)
        # self.straightPull = self.straightPullInput.value

        self.rim_logic = Rim.RimLogic()
        self.rim_logic.rimProfilePath = f'{self.rim_logic.resource_dir}{Rim.rimProfiles[self.rim]["profile"]}'
        self.rim_logic.rim = self.rim
        self.rim_logic.size = self.size
        self.rim_logic.spokeCount = self.spokes

        createWheel(self)

def createWheel(self: WheelLogic):
    rootComp = design.rootComponent
    joints = rootComp.joints

    [lHubEdges, rHubEdges] = Hub.createHub(self.hub_logic)
    rimJointFaces = Rim.createRim(self.rim_logic)

    # TODO create spoke nipples in rim
    # TODO create ball joints for each nipple

    spokes = []
    for _ in range(self.spokes):
        (spokeHeadEdge, spokeThreadFace) = Spoke.createSpoke(self.spoke_logic)
        spokes.append([spokeHeadEdge, spokeThreadFace])

    rimJointFaces0 = []
    rimJointFaces1 = []
    rimJointFaces2 = []
    rimJointFaces3 = []
    hubJointEdges0 = []
    hubJointEdges1 = []
    hubJointEdges2 = []
    hubJointEdges3 = []

    # TODO replace rim faces with nipple faces
    for index, face in enumerate(rimJointFaces):
        if index % 4 == 0:
            rimJointFaces0.append(face)
        elif index % 4 == 1:
            rimJointFaces1.append(face)
        elif index % 4 == 2:
            rimJointFaces2.append(face)
        else:
            rimJointFaces3.append(face)

    for index, edge in enumerate(lHubEdges):
        if index % 2 == 0:
            hubJointEdges0.append(edge)
        else:
            hubJointEdges2.append(edge)
    
    for index, edge in enumerate(rHubEdges):
        if index % 2 == 0:
            hubJointEdges1.append(edge)
        else:
            hubJointEdges3.append(edge)

    for index, spoke in enumerate(spokes):
        # if index % 2 == 0:
        #     hubEdge = lHubEdges[int(index / 2)]
        # else:
        #     hubEdge = rHubEdges[int((index -1) / 2)]

        if index % 4 == 0:
            rimFace = rimJointFaces[index]
            hubEdge = hubJointEdges0[int(index / 4)]
            flipped = True
        elif index % 4 == 1:
            rimFace = rimJointFaces[int((index - 1) % 32)]
            hubEdge = hubJointEdges1[int((index - 1) / 4)]
            flipped = True
        elif index % 4 == 2:
            rimFace = rimJointFaces[int((index - 12) % 32)]
            hubEdge = hubJointEdges2[int((index - 2) / 4)]
            flipped = False
        else:
            rimFace = rimJointFaces[int((index - 13) % 32)]
            hubEdge = hubJointEdges3[int((index - 3) / 4)]
            flipped = False

        geo0 = fusion.JointGeometry.createByCurve(hubEdge, fusion.JointKeyPointTypes.CenterKeyPoint)
        geo1 = fusion.JointGeometry.createByCurve(spoke[0], fusion.JointKeyPointTypes.CenterKeyPoint)
        geo2 = fusion.JointGeometry.createByNonPlanarFace(rimFace, fusion.JointKeyPointTypes.MiddleKeyPoint)
        geo3 = fusion.JointGeometry.createByNonPlanarFace(spoke[1], fusion.JointKeyPointTypes.MiddleKeyPoint)

        
        jointInput0 = joints.createInput(geo0, geo1)
        jointInput0.isFlipped = flipped
        jointInput0.setAsBallJointMotion(fusion.JointDirections.ZAxisJointDirection, fusion.JointDirections.XAxisJointDirection)

        jointInput1 = joints.createInput(geo2, geo3)
        jointInput1.isFlipped = False
        jointInput1.setAsBallJointMotion(fusion.JointDirections.ZAxisJointDirection, fusion.JointDirections.XAxisJointDirection)

        joints.add(jointInput0)
        # joints.add(jointInput1)